# Stock Downloader implementation

import json
import gzip
import boto3
import requests
import time
import random
from typing import Dict, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger()


class StockDownloader:
    """Downloads stock prices, calculates EMAs, and stores in S3 and DynamoDB"""
    
    def __init__(self, environment: str, s3_bucket: str, dynamodb_table: str):
        """
        Initialize Stock Downloader
        
        Args:
            environment: Environment name (dev, uat, prod)
            s3_bucket: S3 bucket name for raw data storage
            dynamodb_table: DynamoDB table name for processed data
        """
        self.environment = environment
        self.s3_bucket = s3_bucket
        self.dynamodb_table = dynamodb_table
        
        # AWS clients
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.ssm = boto3.client('ssm')
        self.secretsmanager = boto3.client('secretsmanager')
        
        # Configuration
        self.api_endpoints_parameter_name = f"/ts-batch-v2/{environment}/api-endpoints"
        self.secret_name = f"ts-batch-v2-{environment}-eodhd-api-token"
        
        # Cache for API token and endpoints
        self._api_token = None
        self._api_endpoints = None
    
    def get_api_token(self) -> str:
        """Retrieve and cache EODHD API token from Secrets Manager"""
        if self._api_token is None:
            try:
                response = self.secretsmanager.get_secret_value(SecretId=self.secret_name)
                secret = json.loads(response['SecretString'])
                self._api_token = secret['api_token']
            except Exception as e:
                logger.error(f"Error fetching API token: {str(e)}")
                raise
        
        return self._api_token
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Retrieve and cache API endpoints from SSM Parameter Store"""
        if self._api_endpoints is None:
            try:
                response = self.ssm.get_parameter(Name=self.api_endpoints_parameter_name)
                self._api_endpoints = json.loads(response['Parameter']['Value'])
            except Exception as e:
                logger.error(f"Error fetching API endpoints: {str(e)}")
                raise
        
        return self._api_endpoints
    
    def process_task(self, record: Dict[str, Any]):
        """
        Process a single download task from SQS
        
        Args:
            record: SQS record containing task details
        """
        # Parse task from message body
        task = json.loads(record['body'])
        
        symbol = task['symbol']
        market_code = task['marketCode']
        date = task['date']
        
        logger.info(f"Processing: {symbol}.{market_code} for date {date}")
        
        # Fetch stock price data with retry
        price_data = self.fetch_with_retry(task)
        
        if not price_data or len(price_data) == 0:
            logger.warning(f"No price data returned for {symbol}.{market_code}")
            return
        
        logger.info(f"Fetched {len(price_data)} price records for {symbol}.{market_code}")
        
        # Upload raw data to S3
        self.upload_to_s3(task, price_data)
        
        # Calculate EMAs and save to DynamoDB
        self.save_to_dynamodb(task, price_data)
        
        logger.info(f"Completed processing {symbol}.{market_code}")
    
    def fetch_with_retry(self, task: Dict, max_retries: int = 1) -> List[Dict]:
        """
        Fetch stock price data with exponential backoff retry
        
        Args:
            task: Task dictionary with symbol and market info
            max_retries: Maximum number of retry attempts (default: 1)
            
        Returns:
            List of price records
        """
        api_token = self.get_api_token()
        
        for attempt in range(max_retries + 1):
            try:
                return self.call_eodhd_api(task, api_token)
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                
                # Check if error is retriable
                if status_code in [429, 500, 502, 503, 504] and attempt < max_retries:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) * 0.1 + random.uniform(0, 0.1)
                    logger.warning(f"Retriable error {status_code}, retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    logger.error(f"Non-retriable error or max retries reached: {status_code}")
                    raise
                    
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries:
                    delay = (2 ** attempt) * 0.1 + random.uniform(0, 0.1)
                    logger.warning(f"Network error, retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    logger.error(f"Max retries reached for network error")
                    raise
    
    def call_eodhd_api(self, task: Dict, api_token: str) -> List[Dict]:
        """
        Call EODHD API to fetch full historical stock price data
        
        Args:
            task: Task dictionary with symbol and market info
            api_token: EODHD API token
            
        Returns:
            List of price records
        """
        endpoints = self.get_api_endpoints()
        
        # Build URL
        url = endpoints['stockPriceUrl'] \
            .replace('{SYMBOL}', task['symbol']) \
            .replace('{MARKET_CODE}', task['marketCode'])
        url += f'?api_token={api_token}&fmt=json'
        
        logger.info(f"Calling EODHD API: {url.replace(api_token, '***')}")
        
        # Make request (no date params - get full historical data)
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        return response.json()

    
    def upload_to_s3(self, task: Dict, price_data: List[Dict]):
        """
        Upload compressed JSON data to S3
        
        Args:
            task: Task dictionary with symbol and market info
            price_data: List of price records
        """
        symbol = task['symbol']
        market_code = task['marketCode']
        date = task['date']
        
        # Build S3 key with partitioned structure
        s3_key = f"prices/market={market_code}/dt={date}/symbol={symbol}/data.json.gz"
        
        # Compress data as gzip JSON
        json_data = json.dumps(price_data)
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        
        logger.info(f"Uploading to S3: {self.s3_bucket}/{s3_key} (size: {len(compressed_data)} bytes)")
        
        try:
            self.s3.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=compressed_data,
                ContentType='application/json',
                ContentEncoding='gzip',
                Metadata={
                    'symbol': symbol,
                    'market_code': market_code,
                    'date': date,
                    'record_count': str(len(price_data))
                }
            )
            
            logger.info(f"Successfully uploaded to S3: {s3_key}")
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise

    
    def calculate_ema_series(self, data: List[Dict], period: int) -> List[float]:
        """
        Calculate EMA series for all data points
        
        EMA formula:
        - EMA(today) = (Price(today) × k) + (EMA(yesterday) × (1 - k))
        - k = 2 / (period + 1)
        - First EMA = SMA of first 'period' prices
        
        Args:
            data: List of price records sorted by date
            period: EMA period (e.g., 7, 30, 50, 200)
            
        Returns:
            List of EMA values (None for insufficient data points)
        """
        if len(data) < period:
            return [None] * len(data)
        
        k = 2 / (period + 1)
        ema_values = []
        
        # Calculate initial SMA for first EMA value
        initial_prices = [data[i]['close'] for i in range(period)]
        ema = sum(initial_prices) / period
        
        # Fill None for insufficient data points
        for i in range(period - 1):
            ema_values.append(None)
        
        # First EMA value
        ema_values.append(ema)
        
        # Calculate EMA for remaining data points
        for i in range(period, len(data)):
            price = data[i]['close']
            ema = (price * k) + (ema * (1 - k))
            ema_values.append(ema)
        
        return ema_values

    
    def save_to_dynamodb(self, task: Dict, price_data: List[Dict]):
        """
        Save OHLCV data and EMAs to DynamoDB as nested lists
        Data retention varies by market to stay within DynamoDB item size limits (400KB):
        - Stock markets (US, BK, etc.): 10 years
        - Crypto market (CC): 3 years (more frequent data points)
        
        Args:
            task: Task dictionary with symbol and market info
            price_data: List of price records
        """
        from decimal import Decimal
        from datetime import datetime, timedelta
        
        symbol = task['symbol']
        market_code = task['marketCode']
        symbol_with_market = f"{symbol}.{market_code}"
        
        # Sort by date
        sorted_data = sorted(price_data, key=lambda x: x['date'])
        
        # Filter data based on market code to stay within DynamoDB item size limits (400KB)
        if market_code == 'CC':
            # Crypto data is more frequent, keep only 3 years
            years_to_keep = 3
        else:
            # Stock data, keep 10 years
            years_to_keep = 10
        
        cutoff_date = (datetime.now() - timedelta(days=365*years_to_keep)).strftime('%Y-%m-%d')
        filtered_data = [record for record in sorted_data if record['date'] >= cutoff_date]
        
        # Skip processing if latest price is less than $1 (penny stocks/low-value crypto)
        if filtered_data and filtered_data[-1]['close'] < 1.0:
            logger.info(f"Skipping {symbol_with_market}: latest price ${filtered_data[-1]['close']:.4f} < $1.00")
            return
        
        logger.info(f"Calculating EMAs for {len(filtered_data)} records (filtered from {len(sorted_data)} total, keeping last {years_to_keep} years)")
        
        # Build prices list with Decimal types (reduced precision to save space)
        prices = []
        for record in filtered_data:
            prices.append({
                'date': record['date'],
                'open': Decimal(str(round(record['open'], 2))),
                'high': Decimal(str(round(record['high'], 2))),
                'low': Decimal(str(round(record['low'], 2))),
                'close': Decimal(str(round(record['close'], 2))),
                'adjusted_close': Decimal(str(round(record['adjusted_close'], 2))),
                'volume': int(record['volume'])
            })
        
        # Calculate EMAs for all periods (using filtered data)
        ema_7 = self.calculate_ema_series(filtered_data, 7)
        ema_30 = self.calculate_ema_series(filtered_data, 30)
        ema_50 = self.calculate_ema_series(filtered_data, 50)
        ema_200 = self.calculate_ema_series(filtered_data, 200)
        
        # Build moving averages list with Decimal types (reduced precision)
        moving_averages = []
        for i, record in enumerate(filtered_data):
            ma_record = {
                'date': record['date'],
                'ema_7': Decimal(str(round(ema_7[i], 2))) if ema_7[i] is not None else None,
                'ema_30': Decimal(str(round(ema_30[i], 2))) if ema_30[i] is not None else None,
                'ema_50': Decimal(str(round(ema_50[i], 2))) if ema_50[i] is not None else None,
                'ema_200': Decimal(str(round(ema_200[i], 2))) if ema_200[i] is not None else None
            }
            moving_averages.append(ma_record)
        
        # Detect golden cross or death cross
        cross_info = self.detect_golden_cross(moving_averages)
        
        # Calculate candle metrics for last 30 days
        candle_metrics = self.calculate_candle_metrics(filtered_data)
        
        # Prepare item for DynamoDB
        item = {
            'symbol': symbol_with_market,
            'market_code': market_code,
            'prices': prices,
            'moving_averages': moving_averages,
            'total_records': len(sorted_data),
            'stored_records': len(filtered_data),
            'oldest_date': filtered_data[0]['date'] if filtered_data else None,
            'latest_date': filtered_data[-1]['date'] if filtered_data else None,
            'golden_cross': cross_info['signal'] if cross_info else None,
            'golden_cross_date': cross_info['date'] if cross_info and cross_info['signal'] == 'GOLDEN_CROSS' else None,
            'death_cross_date': cross_info['date'] if cross_info and cross_info['signal'] == 'DEATH_CROSS' else None,
            'green_days_30d_pct': candle_metrics['green_days_pct'] if candle_metrics else None,
            'max_red_candle_30d_pct': candle_metrics['max_red_candle_pct'] if candle_metrics else None,
            'updated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Saving to DynamoDB: {self.dynamodb_table}/{symbol_with_market} ({len(filtered_data)} records)")
        
        try:
            table = self.dynamodb.Table(self.dynamodb_table)
            table.put_item(Item=item)
            
            logger.info(f"Successfully saved to DynamoDB: {symbol_with_market}")
            
            # If cross detected in past 30 days, save to respective table
            if cross_info:
                from datetime import datetime, timedelta
                cross_date = datetime.strptime(cross_info['date'], '%Y-%m-%d')
                days_ago = (datetime.now() - cross_date).days
                
                logger.info(f"Cross detected: {cross_info['signal']} on {cross_info['date']} ({days_ago} days ago)")
                
                if days_ago <= 30:
                    if cross_info['signal'] == 'GOLDEN_CROSS':
                        logger.info(f"Saving golden cross to separate table (within 30 days)")
                        self.save_cross_signal(symbol_with_market, market_code, cross_info, 'golden', candle_metrics)
                    elif cross_info['signal'] == 'DEATH_CROSS':
                        logger.info(f"Saving death cross to separate table (within 30 days)")
                        self.save_cross_signal(symbol_with_market, market_code, cross_info, 'death', candle_metrics)
                else:
                    logger.info(f"{cross_info['signal']} found but older than 30 days ({days_ago} days ago), not saving to separate table")
            
            # Check for ATH detection after saving price data
            self.check_and_save_ath_detection(symbol_with_market, market_code, filtered_data)
            
        except Exception as e:
            logger.error(f"Error saving to DynamoDB: {str(e)}")
            raise
    
    def detect_golden_cross(self, moving_averages: List[Dict], scan_days: int = 30) -> Dict:
        """
        Detect golden cross or death cross from moving averages
        Returns the MOST RECENT cross within scan_days
        
        Args:
            moving_averages: List of MA records sorted by date
            scan_days: Number of recent days to scan (default: 30)
            
        Returns:
            dict with most recent cross info or None
        """
        if len(moving_averages) < 2:
            return None
        
        # Only scan the last N days for performance
        start_index = max(0, len(moving_averages) - scan_days)
        
        # Scan through recent data to find the most recent golden cross
        most_recent_cross = None
        
        for i in range(start_index + 1, len(moving_averages)):
            today = moving_averages[i]
            yesterday = moving_averages[i-1]
            
            # Check if both EMAs exist
            if (today['ema_50'] is None or today['ema_200'] is None or
                yesterday['ema_50'] is None or yesterday['ema_200'] is None):
                continue
            
            # Convert Decimal to float for comparison
            today_50 = float(today['ema_50'])
            today_200 = float(today['ema_200'])
            yesterday_50 = float(yesterday['ema_50'])
            yesterday_200 = float(yesterday['ema_200'])
            
            # Golden Cross: 50 crosses above 200
            if today_50 > today_200 and yesterday_50 <= yesterday_200:
                most_recent_cross = {
                    'signal': 'GOLDEN_CROSS',
                    'date': today['date'],
                    'ema_50': today_50,
                    'ema_200': today_200,
                    'crossover_strength': round(today_50 - today_200, 2)
                }
            
            # Death Cross: 50 crosses below 200 (bearish)
            elif today_50 < today_200 and yesterday_50 >= yesterday_200:
                most_recent_cross = {
                    'signal': 'DEATH_CROSS',
                    'date': today['date'],
                    'ema_50': today_50,
                    'ema_200': today_200,
                    'crossover_strength': round(today_200 - today_50, 2)
                }
        
        return most_recent_cross
    
    def calculate_candle_metrics(self, price_data: List[Dict], days: int = 30) -> Dict:
        """
        Calculate candle metrics for the last N days
        
        Args:
            price_data: List of price records sorted by date
            days: Number of recent days to analyze (default: 30)
            
        Returns:
            dict with green_days_pct and max_red_candle_pct as Decimal types
        """
        if len(price_data) < days:
            return None
        
        # Get last N days
        recent_data = price_data[-days:]
        
        green_days = 0
        max_red_candle_pct = 0.0  # Track the largest red candle (most negative)
        
        for record in recent_data:
            open_price = record['open']
            close_price = record['close']
            
            # Check if green day (close > open)
            if close_price > open_price:
                green_days += 1
            
            # Calculate candle percentage change
            if open_price > 0:
                candle_pct = ((close_price - open_price) / open_price) * 100
                
                # Track the most negative (largest red candle)
                if candle_pct < max_red_candle_pct:
                    max_red_candle_pct = candle_pct
        
        # Calculate green days percentage
        green_days_pct = (green_days / days) * 100
        
        return {
            'green_days_pct': Decimal(str(round(green_days_pct, 2))),
            'max_red_candle_pct': Decimal(str(round(max_red_candle_pct, 2)))
        }
    
    def save_cross_signal(self, symbol: str, market_code: str, cross_info: Dict, signal_type: str, candle_metrics: Dict = None):
        """
        Save cross signal (golden or death) to separate table with TTL for 30 days
        
        Args:
            symbol: Symbol with market code (e.g., AAPL.US)
            market_code: Market code
            cross_info: Cross signal information
            signal_type: 'golden' or 'death'
            candle_metrics: Candle metrics (green days %, max red candle %)
        """
        from datetime import datetime, timedelta
        from decimal import Decimal
        
        table_name = f"ts-batch-v2-{self.environment}-{signal_type}-crosses"
        
        # Calculate TTL (30 days from now)
        ttl = int((datetime.now() + timedelta(days=30)).timestamp())
        
        item = {
            'symbol': symbol,
            'cross_date': cross_info['date'],
            'market_code': market_code,
            'signal': cross_info['signal'],
            'ema_50': Decimal(str(cross_info['ema_50'])),
            'ema_200': Decimal(str(cross_info['ema_200'])),
            'crossover_strength': Decimal(str(cross_info['crossover_strength'])),
            'detected_at': datetime.now().isoformat(),
            'ttl': ttl
        }
        
        # Add candle metrics if available
        if candle_metrics:
            item['green_days_30d_pct'] = Decimal(str(candle_metrics['green_days_pct']))
            item['max_red_candle_30d_pct'] = Decimal(str(candle_metrics['max_red_candle_pct']))
        
        try:
            table = self.dynamodb.Table(table_name)
            table.put_item(Item=item)
            logger.info(f"{cross_info['signal']} saved to {table_name}: {symbol} on {cross_info['date']}")
        except Exception as e:
            logger.error(f"Error saving {signal_type} cross: {str(e)}")
            # Don't raise - this is not critical

    def check_and_save_ath_detection(self, symbol: str, market_code: str, price_data: List[Dict]):
        """
        Check if symbol has recent golden cross and detect ATH within 30 days
        
        Args:
            symbol: Symbol with market code (e.g., AAPL.US)
            market_code: Market code
            price_data: List of price records sorted by date
        """
        try:
            # Check if symbol has golden cross in past 30 days
            if not self.has_recent_golden_cross(symbol):
                return
            
            # Get latest price
            if not price_data:
                return
                
            latest_record = max(price_data, key=lambda x: x['date'])
            current_price = float(latest_record['close'])
            detection_date = latest_record['date']
            
            # Calculate historical maximum and minimum (all prices before current date)
            historical_prices = [
                float(p['close']) for p in price_data 
                if p['date'] < detection_date
            ]
            
            if not historical_prices:
                return
            
            previous_ath = max(historical_prices)
            lowest_price = min(historical_prices)
            
            # Check if current price is new ATH
            if current_price > previous_ath:
                percentage_gain = ((current_price - lowest_price) / lowest_price) * 100
                
                ath_detection = {
                    'symbol': symbol,
                    'detection_date': detection_date,
                    'ath_price': current_price,
                    'ath_percentage_gain': round(percentage_gain, 2),
                    'market_code': market_code,
                    'detected_at': datetime.now().isoformat(),
                    'ttl': int((datetime.now() + timedelta(days=2)).timestamp())
                }
                
                self.save_ath_detection(ath_detection)
                
        except Exception as e:
            logger.error(f"Error in ATH detection for {symbol}: {str(e)}")

    def has_recent_golden_cross(self, symbol: str) -> bool:
        """
        Check if symbol has golden cross signal in past 30 days
        
        Args:
            symbol: Symbol with market code (e.g., AAPL.US)
            
        Returns:
            True if golden cross found in past 30 days, False otherwise
        """
        try:
            table_name = f"ts-batch-v2-{self.environment}-golden-crosses"
            table = self.dynamodb.Table(table_name)
            
            # Calculate date range (30 days ago to today)
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Query golden crosses by symbol and date range
            response = table.query(
                KeyConditionExpression='symbol = :symbol',
                FilterExpression='cross_date BETWEEN :start_date AND :end_date',
                ExpressionAttributeValues={
                    ':symbol': symbol,
                    ':start_date': start_date.strftime('%Y-%m-%d'),
                    ':end_date': end_date.strftime('%Y-%m-%d')
                }
            )
            
            has_golden_cross = len(response['Items']) > 0
            if has_golden_cross:
                logger.info(f"Found recent golden cross for {symbol}")
            
            return has_golden_cross
            
        except Exception as e:
            logger.error(f"Error checking golden cross for {symbol}: {str(e)}")
            return False

    def save_ath_detection(self, detection: Dict):
        """
        Save ATH detection record to DynamoDB
        
        Args:
            detection: ATH detection record dictionary
        """
        try:
            from decimal import Decimal
            
            table_name = f"ts-batch-v2-{self.environment}-ath-detections"
            table = self.dynamodb.Table(table_name)
            
            # Check for duplicate detection
            existing = table.get_item(
                Key={
                    'symbol': detection['symbol'],
                    'detection_date': detection['detection_date']
                }
            )
            
            if 'Item' not in existing:
                # Convert float values to Decimal for DynamoDB
                detection_record = {
                    k: Decimal(str(v)) if isinstance(v, float) else v
                    for k, v in detection.items()
                }
                
                table.put_item(Item=detection_record)
                logger.info(f"ATH detection saved: {detection['symbol']} - ${detection['ath_price']} (+{detection['ath_percentage_gain']}%)")
            else:
                logger.info(f"Duplicate ATH detection skipped: {detection['symbol']} on {detection['detection_date']}")
                
        except Exception as e:
            logger.error(f"Error saving ATH detection for {detection['symbol']}: {str(e)}")
            # Don't raise - this is not critical
