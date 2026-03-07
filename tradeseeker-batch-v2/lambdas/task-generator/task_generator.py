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
            
            # Log symbol type distribution for debugging
            if market_code == 'US':
                type_counts = {}
                exchange_counts = {}
                sample_symbols = []
                
                # Analyze all symbols to understand the data structure
                for symbol in all_symbols:
                    symbol_type = symbol.get('Type', 'Unknown')
                    exchange = symbol.get('Exchange', 'Unknown')
                    type_counts[symbol_type] = type_counts.get(symbol_type, 0) + 1
                    exchange_counts[exchange] = exchange_counts.get(exchange, 0) + 1
                
                # Sample first 20 symbols for inspection
                for i, symbol in enumerate(all_symbols[:20]):
                    sample_symbols.append({
                        'Code': symbol.get('Code', 'N/A'),
                        'Name': symbol.get('Name', 'N/A'),
                        'Type': symbol.get('Type', 'N/A'),
                        'Exchange': symbol.get('Exchange', 'N/A')
                    })
                
                logger.info(f"US Market - Total symbols: {len(all_symbols)}")
                logger.info(f"US Market symbol types: {dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True))}")
                logger.info(f"US Market exchanges: {dict(sorted(exchange_counts.items(), key=lambda x: x[1], reverse=True))}")
                logger.info(f"Sample symbols: {sample_symbols}")
            
            # Determine filter type based on market code
            if market_code == 'CC':
                # For crypto market, filter for Currency type
                target_type = 'Currency'
            elif market_code == 'US':
                # For US market, be more specific about what we want
                # Let's see what types actually exist first
                target_types = ['Common Stock']
            else:
                # For other stock markets, filter for Common Stock only
                target_types = ['Common Stock']
            
            # Apply filter based on market code
            if market_code == 'CC':
                # For crypto market, filter for Currency type
                filtered_symbols = [
                    s for s in all_symbols 
                    if s.get('Type') == 'Currency'
                ]
            elif market_code == 'US':
                # For US market, apply comprehensive common stock filtering
                filtered_symbols = []
                filter_stats = {
                    'total': len(all_symbols),
                    'wrong_type': 0,
                    'special_chars': 0,
                    'too_long': 0,
                    'too_short': 0,
                    'derivative_suffix': 0,
                    'excluded_keywords': 0,
                    'has_numbers': 0,
                    'wrong_exchange': 0,
                    'otc_pink_sheets': 0,
                    'passed_all': 0
                }
                
                for symbol in all_symbols:
                    code = symbol.get('Code', '')
                    name = symbol.get('Name', '')
                    symbol_type = symbol.get('Type', '')
                    exchange = symbol.get('Exchange', '')
                    
                    # Primary filter: Must be Common Stock type
                    if symbol_type != 'Common Stock':
                        filter_stats['wrong_type'] += 1
                        continue
                    
                    # Filter out symbols with special characters (warrants, rights, etc.)
                    if any(char in code for char in ['.', '-', '/', '^', '~', '+', '=']):
                        filter_stats['special_chars'] += 1
                        continue
                    
                    # Filter out symbols that are too long (usually derivatives) or too short
                    if len(code) > 5:
                        filter_stats['too_long'] += 1
                        continue
                    
                    if len(code) < 1:
                        filter_stats['too_short'] += 1
                        continue
                    
                    # Filter out symbols ending with common suffixes for derivatives/special securities
                    derivative_suffixes = [
                        'W', 'WS', 'WT', 'WD', 'WI', 'WR',  # Warrants
                        'R', 'RT', 'RD',  # Rights
                        'U', 'UN',  # Units
                        'V',  # When-issued
                        'P', 'PR', 'PRA', 'PRB', 'PRC', 'PRD', 'PRE', 'PRF', 'PRG', 'PRH', 'PRI', 'PRJ',  # Preferred
                        'A', 'B', 'C', 'D', 'E', 'F'  # Class shares (but be careful, some legit stocks end with these)
                    ]
                    
                    # Only filter class shares if they're clearly derivatives (length > 4 or have other indicators)
                    if code.endswith(tuple(['W', 'WS', 'WT', 'WD', 'WI', 'WR', 'R', 'RT', 'RD', 'U', 'UN', 'V'] + 
                                          [f'PR{x}' for x in 'ABCDEFGHIJ'])):
                        filter_stats['derivative_suffix'] += 1
                        continue
                    
                    # Be more careful with single letter suffixes - only filter if combined with other indicators
                    if len(code) > 4 and code[-1] in 'ABCDEF' and any(keyword in name.lower() for keyword in ['class', 'series']):
                        filter_stats['derivative_suffix'] += 1
                        continue
                    
                    # Filter out symbols that are clearly ETFs, REITs, or funds by name
                    name_lower = name.lower()
                    excluded_keywords = [
                        'etf', 'fund', 'trust', 'reit', 'index', 'spdr', 'ishares', 
                        'vanguard', 'invesco', 'proshares', 'direxion', 'leveraged',
                        'inverse', '2x', '3x', 'ultra', 'bear', 'bull', 'volatility',
                        'treasury', 'bond', 'note', 'municipal', 'corporate bond',
                        'commodity', 'futures', 'option', 'warrant', 'right',
                        'depositary receipt', 'adr', 'gdr', 'preferred stock'
                    ]
                    
                    if any(keyword in name_lower for keyword in excluded_keywords):
                        filter_stats['excluded_keywords'] += 1
                        continue
                    
                    # Filter out symbols with numbers (often special classes or derivatives)
                    # But allow some exceptions for legitimate companies
                    if any(char.isdigit() for char in code):
                        # Allow certain patterns that might be legitimate
                        if not (len(code) <= 4 and code[-1].isdigit() and code[:-1].isalpha()):
                            filter_stats['has_numbers'] += 1
                            continue
                    
                    # Filter by exchange - be more inclusive but exclude OTC/Pink Sheets
                    excluded_exchanges = [
                        'OTCBB', 'OTC', 'PINK', 'GREY', 'OTCQB', 'OTCQX', 'OTCPK',
                        'BATS', 'IEX'  # These might be legitimate but often have fewer listings
                    ]
                    
                    if exchange in excluded_exchanges:
                        filter_stats['otc_pink_sheets'] += 1
                        continue
                    
                    # Include major exchanges and some others
                    major_exchanges = [
                        'NASDAQ', 'NYSE', 'AMEX', 'NYSE MKT', 'NYSE American', 
                        'NYSE ARCA', 'NASDAQ Global Market', 'NASDAQ Global Select Market',
                        'NASDAQ Capital Market', 'New York Stock Exchange'
                    ]
                    
                    # If exchange is not in major exchanges but also not in excluded, still include it
                    # This handles cases where exchange names might be slightly different
                    if exchange not in major_exchanges and exchange not in excluded_exchanges:
                        # Check if it contains keywords that suggest it's a major exchange
                        exchange_lower = exchange.lower()
                        if not any(keyword in exchange_lower for keyword in ['nasdaq', 'nyse', 'amex', 'american']):
                            filter_stats['wrong_exchange'] += 1
                            continue
                    
                    # If it passes all filters, it's likely a common stock
                    filter_stats['passed_all'] += 1
                    filtered_symbols.append(symbol)
                
                # Log detailed filtering results
                logger.info(f"US Market filtering results:")
                for key, value in filter_stats.items():
                    percentage = (value / filter_stats['total']) * 100 if filter_stats['total'] > 0 else 0
                    logger.info(f"  {key}: {value} ({percentage:.1f}%)")
                
                # Log some examples of what passed and what didn't
                logger.info(f"Sample symbols that passed all filters:")
                for symbol in filtered_symbols[:10]:
                    logger.info(f"  {symbol.get('Code')} - {symbol.get('Name')} ({symbol.get('Exchange')})")
                
                if filter_stats['wrong_type'] > 0:
                    # Show what types were filtered out
                    wrong_type_samples = [s for s in all_symbols if s.get('Type') != 'Common Stock'][:5]
                    logger.info(f"Sample non-Common Stock types filtered out:")
                    for symbol in wrong_type_samples:
                        logger.info(f"  {symbol.get('Code')} - {symbol.get('Type')} - {symbol.get('Name')}")
                    
            else:
                # For other stock markets, filter for Common Stock only
                filtered_symbols = [
                    s for s in all_symbols 
                    if s.get('Type') == 'Common Stock'
                ]
            
            logger.info(f"After comprehensive filtering: {len(filtered_symbols)} symbols from {len(all_symbols)} total")
            
            # Log filtering results for all markets
            logger.info(f"{market_code} Market filtering results:")
            logger.info(f"  - Total symbols from EODHD: {len(all_symbols)}")
            logger.info(f"  - After all filters: {len(filtered_symbols)}")
            logger.info(f"  - Reduction: {len(all_symbols) - len(filtered_symbols)} symbols filtered out")
            logger.info(f"  - Retention rate: {(len(filtered_symbols) / len(all_symbols) * 100):.1f}%")
            
            # Log some examples of what made it through for all markets
            if len(filtered_symbols) > 0:
                sample_final = filtered_symbols[:5]
                logger.info(f"Sample final symbols: {[s.get('Code') for s in sample_final]}")
            else:
                logger.warning(f"No symbols passed filtering for market {market_code}!")
            
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
