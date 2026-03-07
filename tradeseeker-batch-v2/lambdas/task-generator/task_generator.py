# Task Generator implementation

import json
import boto3
import requests
from typing import List, Dict
import logging

logger = logging.getLogger()


class TaskGenerator:
    """Generates download tasks for stock symbols across multiple markets"""
    
    def __init__(self, environment: str, sqs_queue_url: str):
        """
        Initialize Task Generator
        
        Args:
            environment: Environment name (dev, uat, prod)
            sqs_queue_url: SQS queue URL for sending tasks
        """
        self.environment = environment
        self.sqs_queue_url = sqs_queue_url
        
        # AWS clients
        self.ssm = boto3.client('ssm')
        self.secretsmanager = boto3.client('secretsmanager')
        self.sqs = boto3.client('sqs')
        
        # Configuration
        self.markets_parameter_name = f"/ts-batch-v2/{environment}/markets"
        self.api_endpoints_parameter_name = f"/ts-batch-v2/{environment}/api-endpoints"
        self.secret_name = f"ts-batch-v2-{environment}-eodhd-api-token"
    
    def get_markets(self) -> List[Dict]:
        """
        Retrieve market configuration from SSM Parameter Store
        
        Returns:
            List of market dictionaries with Name and Code
        """
        try:
            logger.info(f"Fetching markets from parameter: {self.markets_parameter_name}")
            
            response = self.ssm.get_parameter(Name=self.markets_parameter_name)
            markets = json.loads(response['Parameter']['Value'])
            
            logger.info(f"Retrieved {len(markets)} markets")
            return markets
            
        except Exception as e:
            logger.error(f"Error fetching markets from SSM: {str(e)}")
            raise
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """
        Retrieve API endpoint templates from SSM Parameter Store
        
        Returns:
            Dictionary with symbolListUrl and stockPriceUrl templates
        """
        try:
            logger.info(f"Fetching API endpoints from parameter: {self.api_endpoints_parameter_name}")
            
            response = self.ssm.get_parameter(Name=self.api_endpoints_parameter_name)
            endpoints = json.loads(response['Parameter']['Value'])
            
            return endpoints
            
        except Exception as e:
            logger.error(f"Error fetching API endpoints from SSM: {str(e)}")
            raise
    
    def get_api_token(self) -> str:
        """
        Retrieve EODHD API token from Secrets Manager
        
        Returns:
            API token string
        """
        try:
            logger.info(f"Fetching API token from secret: {self.secret_name}")
            
            response = self.secretsmanager.get_secret_value(SecretId=self.secret_name)
            secret = json.loads(response['SecretString'])
            
            return secret['api_token']
            
        except Exception as e:
            logger.error(f"Error fetching API token from Secrets Manager: {str(e)}")
            raise
    
    def generate_tasks(self, date: str, market_filter: str = None, limit: int = None) -> int:
        """
        Generate download tasks for all markets and symbols
        
        Args:
            date: Target date in YYYY-MM-DD format
            market_filter: Optional market code to process only one market (e.g., "US")
            limit: Optional limit on number of symbols to process per market
            
        Returns:
            Total number of tasks generated
        """
        # Fetch configuration
        markets = self.get_markets()
        api_token = self.get_api_token()
        endpoints = self.get_api_endpoints()
        
        # Filter markets if specified
        if market_filter:
            markets = [m for m in markets if m['Code'] == market_filter]
            logger.info(f"Filtered to market: {market_filter}")
        
        total_tasks = 0
        
        # Process each market
        for market in markets:
            market_code = market['Code']
            market_name = market['Name']
            
            logger.info(f"Processing market: {market_name} ({market_code})")
            
            try:
                # Fetch symbol list for this market
                symbols = self.fetch_symbol_list(market_code, api_token, endpoints)
                
                # Apply limit if specified
                if limit:
                    symbols = symbols[:limit]
                    logger.info(f"Limited to {len(symbols)} symbols (limit: {limit})")
                
                logger.info(f"Found {len(symbols)} symbols for market {market_code}")
                
                # Send tasks to SQS in batches
                tasks_sent = self.send_tasks_to_sqs(symbols, market_code, date)
                total_tasks += tasks_sent
                
                logger.info(f"Sent {tasks_sent} tasks for market {market_code}")
                
            except Exception as e:
                logger.error(f"Error processing market {market_code}: {str(e)}")
                # Continue with other markets even if one fails
                continue
        
        return total_tasks
    
    def fetch_symbol_list(self, market_code: str, api_token: str, endpoints: Dict) -> List[Dict]:
        """
        Fetch symbol list from EODHD API and filter by type
        
        Args:
            market_code: Market code (e.g., "US", "BK", "CC")
            api_token: EODHD API token
            endpoints: API endpoint templates
            
        Returns:
            List of symbol dictionaries (filtered by type based on market)
        """
        url = endpoints['symbolListUrl'].replace('{MARKET_CODE}', market_code)
        url += f'?api_token={api_token}&fmt=json'
        
        logger.info(f"Fetching symbols from: {url.replace(api_token, '***')}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            all_symbols = response.json()
            logger.info(f"Fetched {len(all_symbols)} total symbols for {market_code}")
            
            # Determine filter type based on market code
            if market_code == 'CC':
                # For crypto market, filter for Currency type
                target_type = 'Currency'
            else:
                # For stock markets (US, BK, etc.), filter for Common Stock only
                target_type = 'Common Stock'
            
            # Apply filter
            filtered_symbols = [
                s for s in all_symbols 
                if s.get('Type') == target_type
            ]
            
            logger.info(f"Filtered to {len(filtered_symbols)} symbols from {len(all_symbols)} total (Type='{target_type}')")
            
            return filtered_symbols
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching symbol list for {market_code}: {str(e)}")
            raise
    
    def send_tasks_to_sqs(self, symbols: List[Dict], market_code: str, date: str) -> int:
        """
        Send download tasks to SQS in batches
        
        Args:
            symbols: List of symbol dictionaries
            market_code: Market code
            date: Target date
            
        Returns:
            Number of tasks sent
        """
        batch_size = 10
        tasks_sent = 0
        
        # Process symbols in batches
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            # Prepare batch entries
            entries = []
            for idx, symbol_data in enumerate(batch):
                symbol = symbol_data['Code']
                request_id = f"{symbol}-{market_code}-{date}"
                
                # Create a valid batch entry ID (alphanumeric, hyphens, underscores only, max 80 chars)
                # Use batch index to ensure uniqueness within the batch
                batch_entry_id = f"{market_code}-{i + idx}".replace('.', '_').replace('/', '_')[:80]
                
                message = {
                    'symbol': symbol,
                    'marketCode': market_code,
                    'date': date,
                    'requestId': request_id
                }
                
                entries.append({
                    'Id': batch_entry_id,
                    'MessageBody': json.dumps(message)
                })
            
            # Send batch to SQS
            try:
                response = self.sqs.send_message_batch(
                    QueueUrl=self.sqs_queue_url,
                    Entries=entries
                )
                
                # Check for failures
                if 'Failed' in response and response['Failed']:
                    logger.warning(f"Failed to send {len(response['Failed'])} messages")
                    for failure in response['Failed']:
                        logger.warning(f"Failed message: {failure}")
                
                tasks_sent += len(entries) - len(response.get('Failed', []))
                
            except Exception as e:
                logger.error(f"Error sending batch to SQS: {str(e)}")
                raise
        
        return tasks_sent
