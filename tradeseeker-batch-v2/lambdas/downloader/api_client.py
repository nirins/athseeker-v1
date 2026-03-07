"""
API client module for external data fetching
"""

import json
import requests
import time
import random
from typing import Dict, List
import logging

logger = logging.getLogger()


class EODHDClient:
    """Client for EODHD API operations"""
    
    def __init__(self, ssm_client, secretsmanager_client, environment: str):
        """
        Initialize EODHD Client
        
        Args:
            ssm_client: Boto3 SSM client
            secretsmanager_client: Boto3 Secrets Manager client
            environment: Environment name (dev, uat, prod)
        """
        self.ssm = ssm_client
        self.secretsmanager = secretsmanager_client
        self.environment = environment
        
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