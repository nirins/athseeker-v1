"""
DynamoDB client for TradeSeekerAPI v2.
Provides read-only access to golden-crosses and stock-prices tables.
"""

import os
import logging
import time
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """Client for DynamoDB operations with read-only access."""
    
    def __init__(self, region: str = None):
        """
        Initialize DynamoDB client.
        
        Args:
            region: AWS region (defaults to environment variable or ap-southeast-1)
        """
        self.region = region or os.environ.get('LAMBDA_REGION', 'ap-southeast-1')
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        
        # Table names from environment variables
        self.golden_crosses_table_name = os.environ.get(
            'GOLDEN_CROSSES_TABLE', 
            'ts-batch-v2-dev-golden-crosses'
        )
        self.death_crosses_table_name = os.environ.get(
            'DEATH_CROSSES_TABLE',
            'ts-batch-v2-dev-death-crosses'
        )
        self.stock_prices_table_name = os.environ.get(
            'STOCK_PRICES_TABLE',
            'ts-batch-v2-dev-stock-prices'
        )
        self.stock_prices_lite_table_name = os.environ.get(
            'STOCK_PRICES_LITE_TABLE',
            'ts-batch-v2-dev-stock-prices-lite'
        )
        self.ath_stocks_table_name = os.environ.get(
            'ATH_STOCKS_TABLE',
            'ts-batch-v2-dev-ath'
        )
        self.near_ath_stocks_table_name = os.environ.get(
            'NEAR_ATH_STOCKS_TABLE',
            'ts-batch-v2-dev-near-ath'
        )
        
        # GSI names from environment variables
        self.cross_date_index = os.environ.get('CROSS_DATE_INDEX', 'cross_date-index')
        self.market_cross_date_index = os.environ.get(
            'MARKET_CROSS_DATE_INDEX',
            'market_code-cross_date-index'
        )
        
        # Initialize table references
        self.golden_crosses_table = self.dynamodb.Table(self.golden_crosses_table_name)
        self.death_crosses_table = self.dynamodb.Table(self.death_crosses_table_name)
        self.stock_prices_table = self.dynamodb.Table(self.stock_prices_table_name)
        self.stock_prices_lite_table = self.dynamodb.Table(self.stock_prices_lite_table_name)
        self.ath_stocks_table = self.dynamodb.Table(self.ath_stocks_table_name)
        self.near_ath_stocks_table = self.dynamodb.Table(self.near_ath_stocks_table_name)
        
        logger.info(f"DynamoDB client initialized for region {self.region}")
    
    def query_golden_crosses_by_date(
        self, 
        date: str, 
        market_code: Optional[str] = None
    ) -> list[dict]:
        """
        Query golden crosses by date using GSI.
        
        Args:
            date: Cross date in YYYY-MM-DD format
            market_code: Optional market filter (US, BK, CC)
            
        Returns:
            List of golden cross records
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        start_time = time.time()
        
        try:
            if market_code:
                # Use market_code-cross_date-index GSI
                logger.info(f"Querying golden crosses by market={market_code} and date={date}")
                response = self.golden_crosses_table.query(
                    IndexName=self.market_cross_date_index,
                    KeyConditionExpression='market_code = :market AND cross_date = :date',
                    ExpressionAttributeValues={
                        ':market': market_code,
                        ':date': date
                    }
                )
            else:
                # Use cross_date-index GSI
                logger.info(f"Querying golden crosses by date={date}")
                response = self.golden_crosses_table.query(
                    IndexName=self.cross_date_index,
                    KeyConditionExpression='cross_date = :date',
                    ExpressionAttributeValues={
                        ':date': date
                    }
                )
            
            items = response.get('Items', [])
            execution_time = time.time() - start_time
            logger.info(f"Query returned {len(items)} items in {execution_time:.3f}s")
            
            return items
            
        except ClientError as e:
            execution_time = time.time() - start_time
            error_code = e.response['Error']['Code']
            logger.error(
                f"DynamoDB query failed after {execution_time:.3f}s: {error_code} - {e.response['Error']['Message']}"
            )
            raise
    
    def query_golden_crosses_by_date_range(
        self,
        start_date: str,
        end_date: str,
        market_code: Optional[str] = None
    ) -> list[dict]:
        """
        Query golden crosses within date range using GSI.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            market_code: Optional market filter (US, BK, CC)
            
        Returns:
            List of golden cross records
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        start_time = time.time()
        
        try:
            if market_code:
                # Use market_code-cross_date-index GSI
                logger.info(
                    f"Querying golden crosses by market={market_code} "
                    f"and date range {start_date} to {end_date}"
                )
                response = self.golden_crosses_table.query(
                    IndexName=self.market_cross_date_index,
                    KeyConditionExpression='market_code = :market AND cross_date BETWEEN :start AND :end',
                    ExpressionAttributeValues={
                        ':market': market_code,
                        ':start': start_date,
                        ':end': end_date
                    }
                )
            else:
                # Use cross_date-index GSI with multiple queries
                # Since we can't use BETWEEN on a GSI partition key, we need to scan or query multiple dates
                logger.info(f"Querying golden crosses by date range {start_date} to {end_date}")
                logger.warning("Date range query without market_code requires scanning - consider adding market filter")
                
                # For now, use scan with filter expression
                response = self.golden_crosses_table.scan(
                    FilterExpression='cross_date BETWEEN :start AND :end',
                    ExpressionAttributeValues={
                        ':start': start_date,
                        ':end': end_date
                    }
                )
            
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                if market_code:
                    response = self.golden_crosses_table.query(
                        IndexName=self.market_cross_date_index,
                        KeyConditionExpression='market_code = :market AND cross_date BETWEEN :start AND :end',
                        ExpressionAttributeValues={
                            ':market': market_code,
                            ':start': start_date,
                            ':end': end_date
                        },
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                else:
                    response = self.golden_crosses_table.scan(
                        FilterExpression='cross_date BETWEEN :start AND :end',
                        ExpressionAttributeValues={
                            ':start': start_date,
                            ':end': end_date
                        },
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                items.extend(response.get('Items', []))
            
            execution_time = time.time() - start_time
            logger.info(f"Query returned {len(items)} items in {execution_time:.3f}s")
            
            return items
            
        except ClientError as e:
            execution_time = time.time() - start_time
            error_code = e.response['Error']['Code']
            logger.error(
                f"DynamoDB query failed after {execution_time:.3f}s: {error_code} - {e.response['Error']['Message']}"
            )
            raise
    
    def scan_golden_crosses(self, market_code: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
            """
            Scan golden crosses table with optional market filter, limit, and offset.

            WARNING: This is an expensive operation. Use query methods when possible.

            Args:
                market_code: Optional market filter (US, BK, CC)
                limit: Maximum number of items to return (default: 40)
                offset: Number of items to skip (default: 0)

            Returns:
                List of golden cross records (limited to specified count with offset)

            Raises:
                ClientError: If DynamoDB operation fails
            """
            start_time = time.time()

            try:
                if market_code:
                    logger.info(f"Scanning golden crosses table with market filter: {market_code}, limit: {limit}, offset: {offset}")
                    response = self.golden_crosses_table.scan(
                        FilterExpression=Attr('market_code').eq(market_code)
                    )
                else:
                    logger.info(f"Scanning golden crosses table with limit: {limit}, offset: {offset}")
                    response = self.golden_crosses_table.scan()

                items = response.get('Items', [])

                # Apply offset and limit
                total_items = len(items)
                start_index = min(offset, total_items)
                end_index = min(offset + limit, total_items)

                if start_index >= total_items:
                    items = []
                else:
                    items = items[start_index:end_index]

                execution_time = time.time() - start_time

                logger.info(f"Scanned {len(items)} golden cross records (offset: {offset}, total: {total_items}) in {execution_time:.3f}s")
                return items

            except ClientError as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"DynamoDB scan failed after {execution_time:.3f}s: "
                    f"{e.response['Error']['Code']} - {e.response['Error']['Message']}"
                )
                raise
    
    def get_stock_price(self, symbol: str) -> Optional[dict]:
        """
        Get stock price data by symbol.
        
        Args:
            symbol: Stock symbol with market code (e.g., AAPL.US)
            
        Returns:
            Stock price record or None if not found
            
        Raises:
            ClientError: If DynamoDB operation fails (except ResourceNotFoundException)
        """
        start_time = time.time()
        
        try:
            logger.info(f"Getting stock price for symbol={symbol}")
            response = self.stock_prices_table.get_item(
                Key={'symbol': symbol}
            )
            
            item = response.get('Item')
            execution_time = time.time() - start_time
            
            if item:
                logger.info(f"Stock price found in {execution_time:.3f}s")
            else:
                logger.info(f"Stock price not found in {execution_time:.3f}s")
            
            return item
            
        except ClientError as e:
            execution_time = time.time() - start_time
            error_code = e.response['Error']['Code']
            
            # ResourceNotFoundException is expected when symbol doesn't exist
            if error_code == 'ResourceNotFoundException':
                logger.error(f"DynamoDB table not found: {self.stock_prices_table_name}")
                raise
            
            logger.error(
                f"DynamoDB get_item failed after {execution_time:.3f}s: {error_code} - {e.response['Error']['Message']}"
            )
            raise

    def query_death_crosses_by_date(
        self, 
        date: str, 
        market_code: Optional[str] = None
    ) -> list[dict]:
        """
        Query death crosses by date using GSI.
        
        Args:
            date: Cross date in YYYY-MM-DD format
            market_code: Optional market filter (US, BK, CC)
            
        Returns:
            List of death cross records
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        start_time = time.time()
        
        try:
            if market_code:
                # Use market_code-cross_date-index GSI
                logger.info(f"Querying death crosses by market={market_code} and date={date}")
                response = self.death_crosses_table.query(
                    IndexName=self.market_cross_date_index,
                    KeyConditionExpression='market_code = :market AND cross_date = :date',
                    ExpressionAttributeValues={
                        ':market': market_code,
                        ':date': date
                    }
                )
            else:
                # Use cross_date-index GSI
                logger.info(f"Querying death crosses by date={date}")
                response = self.death_crosses_table.query(
                    IndexName=self.cross_date_index,
                    KeyConditionExpression='cross_date = :date',
                    ExpressionAttributeValues={
                        ':date': date
                    }
                )
            
            items = response.get('Items', [])
            execution_time = time.time() - start_time
            logger.info(f"Death cross query returned {len(items)} items in {execution_time:.3f}s")
            
            return items
            
        except ClientError as e:
            execution_time = time.time() - start_time
            error_code = e.response['Error']['Code']
            logger.error(
                f"DynamoDB death cross query failed after {execution_time:.3f}s: {error_code} - {e.response['Error']['Message']}"
            )
            raise
    
    def query_death_crosses_by_date_range(
        self,
        start_date: str,
        end_date: str,
        market_code: Optional[str] = None
    ) -> list[dict]:
        """
        Query death crosses within date range using GSI.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            market_code: Optional market filter (US, BK, CC)
            
        Returns:
            List of death cross records
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        start_time = time.time()
        
        try:
            if market_code:
                # Use market_code-cross_date-index GSI
                logger.info(
                    f"Querying death crosses by market={market_code} "
                    f"and date range {start_date} to {end_date}"
                )
                response = self.death_crosses_table.query(
                    IndexName=self.market_cross_date_index,
                    KeyConditionExpression='market_code = :market AND cross_date BETWEEN :start AND :end',
                    ExpressionAttributeValues={
                        ':market': market_code,
                        ':start': start_date,
                        ':end': end_date
                    }
                )
            else:
                # Use scan with filter expression for date range without market
                logger.info(f"Querying death crosses by date range {start_date} to {end_date}")
                logger.warning("Date range query without market_code requires scanning - consider adding market filter")
                
                response = self.death_crosses_table.scan(
                    FilterExpression='cross_date BETWEEN :start AND :end',
                    ExpressionAttributeValues={
                        ':start': start_date,
                        ':end': end_date
                    }
                )
            
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                if market_code:
                    response = self.death_crosses_table.query(
                        IndexName=self.market_cross_date_index,
                        KeyConditionExpression='market_code = :market AND cross_date BETWEEN :start AND :end',
                        ExpressionAttributeValues={
                            ':market': market_code,
                            ':start': start_date,
                            ':end': end_date
                        },
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                else:
                    response = self.death_crosses_table.scan(
                        FilterExpression='cross_date BETWEEN :start AND :end',
                        ExpressionAttributeValues={
                            ':start': start_date,
                            ':end': end_date
                        },
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                items.extend(response.get('Items', []))
            
            execution_time = time.time() - start_time
            logger.info(f"Death cross query returned {len(items)} items in {execution_time:.3f}s")
            
            return items
            
        except ClientError as e:
            execution_time = time.time() - start_time
            error_code = e.response['Error']['Code']
            logger.error(
                f"DynamoDB death cross query failed after {execution_time:.3f}s: {error_code} - {e.response['Error']['Message']}"
            )
            raise
    
    def scan_death_crosses(self, market_code: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
            """
            Scan death crosses table with optional market filter, limit, and offset.

            WARNING: This is an expensive operation. Use query methods when possible.

            Args:
                market_code: Optional market filter (US, BK, CC)
                limit: Maximum number of items to return (default: 40)
                offset: Number of items to skip (default: 0)

            Returns:
                List of death cross records (limited to specified count with offset)

            Raises:
                ClientError: If DynamoDB operation fails
            """
            start_time = time.time()

            try:
                if market_code:
                    logger.info(f"Scanning death crosses table with market filter: {market_code}, limit: {limit}, offset: {offset}")
                    response = self.death_crosses_table.scan(
                        FilterExpression=Attr('market_code').eq(market_code)
                    )
                else:
                    logger.info(f"Scanning death crosses table with limit: {limit}, offset: {offset}")
                    response = self.death_crosses_table.scan()

                items = response.get('Items', [])

                # Apply offset and limit
                total_items = len(items)
                start_index = min(offset, total_items)
                end_index = min(offset + limit, total_items)

                if start_index >= total_items:
                    items = []
                else:
                    items = items[start_index:end_index]

                execution_time = time.time() - start_time

                logger.info(f"Scanned {len(items)} death cross records (offset: {offset}, total: {total_items}) in {execution_time:.3f}s")
                return items

            except ClientError as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"DynamoDB scan failed after {execution_time:.3f}s: "
                    f"{e.response['Error']['Code']} - {e.response['Error']['Message']}"
                )
                raise

    def query_ath_stocks_by_date(
        self, 
        date: str, 
        market_code: Optional[str] = None
    ) -> list[dict]:
        """
        Query ATH stocks by detection date with optional market filter.
        
        Uses GSI for efficient querying by date.
        
        Args:
            date: Detection date in YYYY-MM-DD format
            market_code: Optional market filter (US, BK, CC)
            
        Returns:
            List of ATH stock records
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        start_time = time.time()
        
        try:
            if market_code:
                # Use market_code-detection_date-index GSI for market + date query
                logger.info(f"Querying ATH stocks by market={market_code} and date={date}")
                response = self.ath_stocks_table.query(
                    IndexName=self.market_cross_date_index,
                    KeyConditionExpression=Key('market_code').eq(market_code) & 
                                         Key('detection_date').eq(date)
                )
            else:
                # Use detection_date-index GSI for date-only query
                logger.info(f"Querying ATH stocks by date={date}")
                response = self.ath_stocks_table.query(
                    IndexName=self.cross_date_index,
                    KeyConditionExpression=Key('detection_date').eq(date)
                )
            
            items = response.get('Items', [])
            execution_time = time.time() - start_time
            
            logger.info(f"Found {len(items)} ATH stock records in {execution_time:.3f}s")
            return items
            
        except ClientError as e:
            execution_time = time.time() - start_time
            logger.error(
                f"DynamoDB query failed after {execution_time:.3f}s: "
                f"{e.response['Error']['Code']} - {e.response['Error']['Message']}"
            )
            raise

    def query_ath_stocks_by_date_range(
        self,
        start_date: str,
        end_date: str,
        market_code: Optional[str] = None
    ) -> list[dict]:
        """
        Query ATH stocks by date range with optional market filter.
        
        Uses GSI for efficient querying by date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            market_code: Optional market filter (US, BK, CC)
            
        Returns:
            List of ATH stock records
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        start_time = time.time()
        
        try:
            if market_code:
                # Use market_code-detection_date-index GSI for market + date range query
                logger.info(f"Querying ATH stocks by market={market_code} and date range {start_date} to {end_date}")
                response = self.ath_stocks_table.query(
                    IndexName=self.market_cross_date_index,
                    KeyConditionExpression=Key('market_code').eq(market_code) & 
                                         Key('detection_date').between(start_date, end_date)
                )
            else:
                # Use detection_date-index GSI for date range query
                logger.info(f"Querying ATH stocks by date range {start_date} to {end_date}")
                response = self.ath_stocks_table.query(
                    IndexName=self.cross_date_index,
                    KeyConditionExpression=Key('detection_date').between(start_date, end_date)
                )
            
            items = response.get('Items', [])
            execution_time = time.time() - start_time
            
            logger.info(f"Found {len(items)} ATH stock records in {execution_time:.3f}s")
            return items
            
        except ClientError as e:
            execution_time = time.time() - start_time
            logger.error(
                f"DynamoDB query failed after {execution_time:.3f}s: "
                f"{e.response['Error']['Code']} - {e.response['Error']['Message']}"
            )
            raise
    def query_ath_stocks_by_beauty_score(
        self,
        market_code: str = 'US',
        limit: int = 1000,
        min_beauty_score: float = 0.0
    ) -> list[dict]:
        """
        Query ATH stocks ordered by beauty score descending.

        Uses beauty_score-index GSI for efficient querying by beauty score.

        Args:
            market_code: Market filter (US, BK, CC) - defaults to US
            limit: Maximum number of results to return
            min_beauty_score: Minimum beauty score threshold

        Returns:
            List of ATH stock records ordered by beauty score descending

        Raises:
            ClientError: If DynamoDB operation fails
        """
        start_time = time.time()

        try:
            logger.info(f"Querying ATH stocks by beauty score for market={market_code}, min_score={min_beauty_score}")

            # Convert float to Decimal for DynamoDB
            min_score_decimal = Decimal(str(min_beauty_score))
            
            # Query using beauty_score-index GSI
            response = self.ath_stocks_table.query(
                IndexName='beauty_score-index',
                KeyConditionExpression=Key('market_code').eq(market_code) &
                                     Key('beauty_score').gte(min_score_decimal),
                ScanIndexForward=False,  # Sort descending (highest beauty score first)
                Limit=limit
            )

            items = response.get('Items', [])
            execution_time = time.time() - start_time

            logger.info(f"Found {len(items)} ATH stock records ordered by beauty score in {execution_time:.3f}s")
            return items

        except ClientError as e:
            execution_time = time.time() - start_time
            logger.error(
                f"DynamoDB beauty score query failed after {execution_time:.3f}s: "
                f"{e.response['Error']['Code']} - {e.response['Error']['Message']}"
            )
            raise

    def scan_ath_stocks(self, market_code: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
            """
            Scan ATH stocks table with optional market filter, limit, and offset.

            WARNING: This is an expensive operation. Use query methods when possible.

            Args:
                market_code: Optional market filter (US, BK, CC)
                limit: Maximum number of items to return (default: 40)
                offset: Number of items to skip (default: 0)

            Returns:
                List of ATH stock records (limited to specified count with offset)

            Raises:
                ClientError: If DynamoDB operation fails
            """
            start_time = time.time()

            try:
                if market_code:
                    logger.info(f"Scanning ATH stocks table with market filter: {market_code}, limit: {limit}, offset: {offset}")
                    response = self.ath_stocks_table.scan(
                        FilterExpression=Attr('market_code').eq(market_code)
                    )
                else:
                    logger.info(f"Scanning ATH stocks table with limit: {limit}, offset: {offset}")
                    response = self.ath_stocks_table.scan()

                items = response.get('Items', [])

                # Apply offset and limit
                total_items = len(items)
                start_index = min(offset, total_items)
                end_index = min(offset + limit, total_items)

                if start_index >= total_items:
                    items = []
                else:
                    items = items[start_index:end_index]

                execution_time = time.time() - start_time

                logger.info(f"Scanned {len(items)} ATH stock records (offset: {offset}, total: {total_items}) in {execution_time:.3f}s")
                return items

            except ClientError as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"DynamoDB scan failed after {execution_time:.3f}s: "
                    f"{e.response['Error']['Code']} - {e.response['Error']['Message']}"
                )
                raise


    def query_near_ath_stocks_by_beauty_score(
        self,
        market_code: str,
        limit: int = 50
    ) -> list[dict]:
        """
        Query Near ATH stocks by beauty score (highest first) for a specific market.
        
        Uses beauty_score-index GSI for efficient querying ordered by beauty score.
        
        Args:
            market_code: Market code (US, BK, CC)
            limit: Maximum number of results to return
            
        Returns:
            List of Near ATH stock records ordered by beauty score (highest first)
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        start_time = time.time()
        
        try:
            logger.info(f"Querying Near ATH stocks by beauty score for market={market_code}, limit={limit}")
            
            response = self.near_ath_stocks_table.query(
                IndexName='beauty_score-index',
                KeyConditionExpression=Key('market_code').eq(market_code),
                ScanIndexForward=False,  # Descending order (highest beauty score first)
                Limit=limit
            )
            
            items = response.get('Items', [])
            execution_time = time.time() - start_time
            
            logger.info(f"Found {len(items)} Near ATH stock records in {execution_time:.3f}s")
            return items
            
        except ClientError as e:
            execution_time = time.time() - start_time
            logger.error(
                f"DynamoDB query failed after {execution_time:.3f}s: "
                f"{e.response['Error']['Code']} - {e.response['Error']['Message']}"
            )
            raise

    def scan_near_ath_stocks(self, market_code: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
        """
        Scan Near ATH stocks table with optional market filter.
        
        WARNING: This is a table scan operation which is less efficient than queries.
        Use query methods when possible.
        
        Args:
            market_code: Optional market filter (US, BK, CC)
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of Near ATH stock records
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        start_time = time.time()
        
        try:
            scan_kwargs = {
                'Limit': limit + offset  # Get extra items to handle offset
            }
            
            if market_code:
                logger.info(f"Scanning Near ATH stocks with market filter: {market_code}")
                scan_kwargs['FilterExpression'] = Attr('market_code').eq(market_code)
            else:
                logger.info("Scanning all Near ATH stocks (no market filter)")
            
            response = self.near_ath_stocks_table.scan(**scan_kwargs)
            
            items = response.get('Items', [])
            
            # Handle pagination manually for offset
            if offset > 0:
                items = items[offset:]
            
            # Limit results
            if len(items) > limit:
                items = items[:limit]
            
            execution_time = time.time() - start_time
            
            logger.info(f"Scanned {len(items)} Near ATH stock records in {execution_time:.3f}s")
            return items
            
        except ClientError as e:
            execution_time = time.time() - start_time
            logger.error(
                f"DynamoDB scan failed after {execution_time:.3f}s: "
                f"{e.response['Error']['Code']} - {e.response['Error']['Message']}"
            )
            raise

    def batch_get_stock_prices_lite(self, symbols: list[str]) -> list[dict]:
        """
        Fetch 360-day stock price records from the lite table using ThreadPoolExecutor.
        Much faster than the full table due to smaller item sizes.
        """
        if not symbols:
            return []

        import concurrent.futures
        start_time = time.time()
        results = []

        def fetch_one(symbol: str):
            try:
                response = self.stock_prices_lite_table.get_item(Key={'symbol': symbol})
                return response.get('Item')
            except ClientError as e:
                logger.error(f"get_item (lite) failed for {symbol}: {e.response['Error']['Code']}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(fetch_one, s): s for s in symbols}
            for future in concurrent.futures.as_completed(futures):
                item = future.result()
                if item:
                    results.append(item)

        execution_time = time.time() - start_time
        logger.info(f"batch_get_stock_prices_lite: fetched {len(results)}/{len(symbols)} in {execution_time:.3f}s")
        return results

    def batch_get_stock_prices(self, symbols: list[str]) -> list[dict]:
        """
        Fetch multiple stock price records concurrently using ThreadPoolExecutor.
        Uses individual get_item calls to avoid DynamoDB batch_get_item 16MB limit
        (stock price items are large — prices + moving_averages arrays).

        Args:
            symbols: List of stock symbols (e.g. ['AAPL.US', 'MSFT.US'])

        Returns:
            List of stock price records (order not guaranteed)
        """
        if not symbols:
            return []

        import concurrent.futures
        start_time = time.time()
        results = []

        def fetch_one(symbol: str):
            try:
                response = self.stock_prices_table.get_item(Key={'symbol': symbol})
                return response.get('Item')
            except ClientError as e:
                logger.error(f"get_item failed for {symbol}: {e.response['Error']['Code']}")
                return None

        # Run up to 20 concurrent get_item calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(fetch_one, s): s for s in symbols}
            for future in concurrent.futures.as_completed(futures):
                item = future.result()
                if item:
                    results.append(item)

        execution_time = time.time() - start_time
        logger.info(f"batch_get_stock_prices: fetched {len(results)}/{len(symbols)} records in {execution_time:.3f}s")
        return results
