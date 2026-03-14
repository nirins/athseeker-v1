# Stock Downloader implementation

import json
import os
import boto3
from typing import Dict, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from technical_analysis import calculate_ema_series, calculate_candle_metrics
from cross_detector import CrossDetector
from ath_detector import ATHDetector
from near_ath_detector import NearATHDetector
from breakout_analyzer import BreakoutAnalyzer
from storage import StorageManager
from api_client import EODHDClient

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
        
        # Initialize specialized modules with configurable volatility filter
        max_daily_volatility = float(os.environ.get('MAX_DAILY_VOLATILITY', '100.0'))
        near_ath_threshold = float(os.environ.get('NEAR_ATH_THRESHOLD', '7.0'))
        
        self.api_client = EODHDClient(self.ssm, self.secretsmanager, environment)
        self.storage = StorageManager(environment, s3_bucket, dynamodb_table, self.s3, self.dynamodb)
        self.cross_detector = CrossDetector(environment)
        self.ath_detector = ATHDetector(environment, max_daily_volatility)
        self.near_ath_detector = NearATHDetector(environment, max_daily_volatility, near_ath_threshold)
        self.breakout_analyzer = BreakoutAnalyzer()
    
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
        symbol_with_market = f"{symbol}.{market_code}"
        
        logger.info(f"Processing: {symbol_with_market} for date {date}")
        
        # Fetch stock price data with retry
        price_data = self.api_client.fetch_with_retry(task)
        
        if not price_data or len(price_data) == 0:
            logger.warning(f"No price data returned for {symbol_with_market}")
            return
        
        logger.info(f"Fetched {len(price_data)} price records for {symbol_with_market}")
        
        # Always upload raw data to S3 (complete historical archive)
        self.storage.upload_to_s3(task, price_data)
        
        # Process data and save to DynamoDB only if detections found
        self.process_and_conditionally_save(task, price_data)
        
        logger.info(f"Completed processing {symbol_with_market}")
    
    def process_and_conditionally_save(self, task: Dict, price_data: List[Dict]):
        """
        Process price data and save to DynamoDB only if detections are found
        
        Args:
            task: Task dictionary with symbol and market info
            price_data: List of price records
        """
        symbol = task['symbol']
        market_code = task['marketCode']
        symbol_with_market = f"{symbol}.{market_code}"
        
        # Prepare and filter data
        processed_data = self.prepare_data(price_data, market_code, symbol_with_market)
        if not processed_data:
            return
        
        filtered_data, moving_averages, candle_metrics = processed_data
        
        # Check for any detections
        detections = self.check_all_detections(symbol_with_market, market_code, moving_averages, filtered_data)
        
        if detections['has_any']:
            logger.info(f"Detections found for {symbol_with_market} - Cross: {detections['cross']}, ATH: {detections['ath']}")
            
            # Save to main DynamoDB table
            self.storage.save_to_dynamodb(task, filtered_data, moving_averages, candle_metrics)
            
            # Save specific detections
            self.save_detections(symbol_with_market, market_code, moving_averages, filtered_data, candle_metrics, detections)
        else:
            logger.info(f"No detections found for {symbol_with_market}, skipped DynamoDB")
    
    def prepare_data(self, price_data: List[Dict], market_code: str, symbol_with_market: str):
        """
        Prepare and filter price data for analysis
        
        Args:
            price_data: Raw price data
            market_code: Market code
            symbol_with_market: Symbol with market code
            
        Returns:
            Tuple of (filtered_data, moving_averages, candle_metrics) or None if should skip
        """
        # Sort by date
        sorted_data = sorted(price_data, key=lambda x: x['date'])
        
        # Filter data based on market code to stay within DynamoDB item size limits (400KB)
        filtered_data = self.filter_data_by_retention(sorted_data, market_code)
        
        # Check data quality first - skip if poor quality detected
        if not self.check_data_quality(filtered_data, symbol_with_market):
            return None
        
        # Skip processing if latest price is less than $1 (penny stocks/low-value crypto)
        if filtered_data and filtered_data[-1]['close'] < 1.0:
            logger.info(f"Skipping {symbol_with_market}: latest price ${filtered_data[-1]['close']:.4f} < $1.00")
            return None
        
        # Require at least 90 records for meaningful detection across all markets
        if len(filtered_data) < 90:
            logger.info(f"Skipping {symbol_with_market}: insufficient data ({len(filtered_data)} < 90 records)")
            return None
        
        logger.info(f"Calculating EMAs for {len(filtered_data)} records (filtered from {len(sorted_data)} total)")
        
        # Calculate EMAs and build moving averages list
        moving_averages = self.calculate_moving_averages(filtered_data)
        
        # Calculate candle metrics for last 30 days
        candle_metrics = calculate_candle_metrics(filtered_data)
        
        return filtered_data, moving_averages, candle_metrics
    
    def check_data_quality(self, price_data: List[Dict], symbol_with_market: str) -> bool:
        """
        Check data quality by detecting stale/identical OHLC values
        
        Args:
            price_data: List of price records
            symbol_with_market: Symbol with market code for logging
            
        Returns:
            bool: True if data quality is good, False if poor quality detected
        """
        if not price_data or len(price_data) < 10:
            return True  # Not enough data to assess quality
        
        # Check the most recent 30 days for stale data patterns
        recent_data = price_data[-30:] if len(price_data) >= 30 else price_data
        
        consecutive_identical_days = 0
        max_consecutive_identical = 0
        total_identical_days = 0
        
        for i in range(1, len(recent_data)):
            current = recent_data[i]
            previous = recent_data[i-1]
            
            # Check if OHLC values are identical (indicating stale/suspended trading)
            current_ohlc = (current['open'], current['high'], current['low'], current['close'])
            previous_ohlc = (previous['open'], previous['high'], previous['low'], previous['close'])
            
            if current_ohlc == previous_ohlc:
                consecutive_identical_days += 1
                total_identical_days += 1
                max_consecutive_identical = max(max_consecutive_identical, consecutive_identical_days)
            else:
                consecutive_identical_days = 0
        
        # Calculate quality metrics
        total_days_checked = len(recent_data) - 1
        identical_percentage = (total_identical_days / total_days_checked * 100) if total_days_checked > 0 else 0
        
        # Quality thresholds
        max_consecutive_threshold = 7  # More than 7 consecutive identical days is suspicious
        max_percentage_threshold = 50  # More than 50% identical days indicates poor quality
        
        # Determine if data quality is poor
        is_poor_quality = (
            max_consecutive_identical > max_consecutive_threshold or
            identical_percentage > max_percentage_threshold
        )
        
        if is_poor_quality:
            logger.warning(f"Poor data quality detected for {symbol_with_market}: "
                         f"{max_consecutive_identical} max consecutive identical days, "
                         f"{identical_percentage:.1f}% identical days in recent {total_days_checked} days. "
                         f"Skipping all detections.")
            return False
        
        logger.info(f"Data quality check passed for {symbol_with_market}: "
                   f"{max_consecutive_identical} max consecutive identical days, "
                   f"{identical_percentage:.1f}% identical days")
        return True
    
    def check_all_detections(self, symbol_with_market: str, market_code: str, moving_averages: List[Dict], price_data: List[Dict]) -> Dict:
        """
        Check for all types of detections
        
        Args:
            symbol_with_market: Symbol with market code
            market_code: Market code
            moving_averages: List of moving average records
            price_data: List of price records
            
        Returns:
            Dict with detection results
        """
        has_cross = self.check_cross_signals(symbol_with_market, market_code, moving_averages)
        has_ath = self.check_ath_detection(symbol_with_market, market_code, price_data)
        has_near_ath = self.check_near_ath_detection(symbol_with_market, market_code, price_data, moving_averages)
        
        return {
            'cross': has_cross,
            'ath': has_ath,
            'near_ath': has_near_ath,
            'has_any': has_cross or has_ath or has_near_ath
        }
    
    def save_detections(self, symbol_with_market: str, market_code: str, moving_averages: List[Dict], 
                       price_data: List[Dict], candle_metrics: Dict, detections: Dict):
        """
        Save specific detection results to their respective tables
        
        Args:
            symbol_with_market: Symbol with market code
            market_code: Market code
            moving_averages: List of moving average records
            price_data: List of price records
            candle_metrics: Candle metrics
            detections: Detection results
        """
        if detections['cross']:
            self.handle_cross_signals(symbol_with_market, market_code, moving_averages, candle_metrics)
        
        if detections['ath']:
            self.handle_ath_detection(symbol_with_market, market_code, price_data, moving_averages)
        
        if detections['near_ath']:
            self.handle_near_ath_detection(symbol_with_market, market_code, price_data, moving_averages)
    
    def filter_data_by_retention(self, sorted_data: List[Dict], market_code: str) -> List[Dict]:
        """
        Filter data based on market code to stay within DynamoDB item size limits
        
        Args:
            sorted_data: List of price records sorted by date
            market_code: Market code
            
        Returns:
            Filtered list of price records
        """
        # Data retention varies by market to stay within DynamoDB item size limits (400KB)
        if market_code == 'CC':
            # Crypto data is more frequent, keep only 3 years
            years_to_keep = 3
        else:
            # Stock data, keep 10 years
            years_to_keep = 10
        
        cutoff_date = (datetime.now() - timedelta(days=365*years_to_keep)).strftime('%Y-%m-%d')
        return [record for record in sorted_data if record['date'] >= cutoff_date]
    
    def calculate_moving_averages(self, filtered_data: List[Dict]) -> List[Dict]:
        """
        Calculate EMAs for all periods and build moving averages list
        
        Args:
            filtered_data: List of filtered price records
            
        Returns:
            List of moving average records
        """
        # Calculate EMAs for all periods (using filtered data)
        ema_7 = calculate_ema_series(filtered_data, 7)
        ema_30 = calculate_ema_series(filtered_data, 30)
        ema_50 = calculate_ema_series(filtered_data, 50)
        ema_200 = calculate_ema_series(filtered_data, 200)
        
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
        
        return moving_averages
    
    def check_cross_signals(self, symbol_with_market: str, market_code: str, moving_averages: List[Dict]) -> bool:
        """
        Check if there are any cross signals (without saving)
        
        Args:
            symbol_with_market: Symbol with market code
            market_code: Market code
            moving_averages: List of moving average records
            
        Returns:
            bool: True if cross signal found within 30 days, False otherwise
        """
        # Detect cross signals
        cross_info = self.cross_detector.detect_golden_cross(moving_averages)
        
        if not cross_info:
            return False
        
        cross_date = datetime.strptime(cross_info['date'], '%Y-%m-%d')
        days_ago = (datetime.now() - cross_date).days
        
        # Return True if cross is within 30 days
        return days_ago <= 30
    
    def check_ath_detection(self, symbol_with_market: str, market_code: str, price_data: List[Dict]) -> bool:
        """
        Check if there is ATH detection (without saving)
        
        Args:
            symbol_with_market: Symbol with market code
            market_code: Market code
            price_data: List of price records
            
        Returns:
            bool: True if ATH detected, False otherwise
        """
        ath_detection = self.ath_detector.check_ath_detection(symbol_with_market, market_code, price_data)
        
        return ath_detection is not None
    
    def check_near_ath_detection(self, symbol_with_market: str, market_code: str, price_data: List[Dict], moving_averages: List[Dict] = None) -> bool:
        """
        Check if there is Near ATH detection (without saving)
        
        Args:
            symbol_with_market: Symbol with market code
            market_code: Market code
            price_data: List of price records
            moving_averages: Optional moving averages for EMA50 filter
            
        Returns:
            bool: True if Near ATH detected, False otherwise
        """
        near_ath_detection = self.near_ath_detector.check_near_ath_detection(symbol_with_market, market_code, price_data, moving_averages)
        
        return near_ath_detection is not None
    
    def handle_cross_signals(self, symbol_with_market: str, market_code: str, moving_averages: List[Dict], candle_metrics: Dict):
        """
        Handle cross signal detection and saving
        
        Args:
            symbol_with_market: Symbol with market code
            market_code: Market code
            moving_averages: List of moving average records
            candle_metrics: Candle metrics
        """
        # Detect cross signals
        cross_info = self.cross_detector.detect_golden_cross(moving_averages)
        
        if not cross_info:
            return
        
        cross_date = datetime.strptime(cross_info['date'], '%Y-%m-%d')
        days_ago = (datetime.now() - cross_date).days
        
        logger.info(f"Cross detected: {cross_info['signal']} on {cross_info['date']} ({days_ago} days ago)")
        
        if days_ago <= 30:
            if cross_info['signal'] == 'GOLDEN_CROSS':
                logger.info(f"Saving golden cross to separate table (within 30 days)")
                self.storage.save_cross_signal(symbol_with_market, market_code, cross_info, 'golden', candle_metrics)
            elif cross_info['signal'] == 'DEATH_CROSS':
                logger.info(f"Saving death cross to separate table (within 30 days)")
                self.storage.save_cross_signal(symbol_with_market, market_code, cross_info, 'death', candle_metrics)
        else:
            logger.info(f"{cross_info['signal']} found but older than 30 days ({days_ago} days ago), not saving to separate table")
    
    def handle_ath_detection(self, symbol_with_market: str, market_code: str, price_data: List[Dict], moving_averages: List[Dict] = None):
        """
        Handle ATH detection and saving
        
        Args:
            symbol_with_market: Symbol with market code
            market_code: Market code
            price_data: List of price records
            moving_averages: List of moving average records (optional)
        """
        ath_detection = self.ath_detector.check_ath_detection(symbol_with_market, market_code, price_data)
        
        if ath_detection:
            # Merge price data with moving averages for beauty score calculation
            merged_data = self._merge_price_and_ema_data(price_data, moving_averages)
            
            # Calculate breakout beauty score
            beauty_analysis = self.breakout_analyzer.calculate_breakout_beauty_score(
                merged_data, 
                ath_detection['detection_date'], 
                ath_detection['ath_price']
            )
            
            # Add beauty score to ATH detection
            ath_detection.update(beauty_analysis)
            
            logger.info(f"ATH detected: {symbol_with_market} - ${ath_detection['ath_price']} (+{ath_detection['ath_percentage_gain']}%) - Beauty: {beauty_analysis.get('beauty_score', 'N/A')} ({beauty_analysis.get('grade', 'N/A')})")
            self.storage.save_ath_detection(ath_detection)
    
    def handle_near_ath_detection(self, symbol_with_market: str, market_code: str, price_data: List[Dict], moving_averages: List[Dict] = None):
        """
        Handle Near ATH detection and saving
        
        Args:
            symbol_with_market: Symbol with market code
            market_code: Market code
            price_data: List of price records
            moving_averages: List of moving average records (optional)
        """
        near_ath_detection = self.near_ath_detector.check_near_ath_detection(symbol_with_market, market_code, price_data, moving_averages)
        
        if near_ath_detection:
            # Merge price data with moving averages for beauty score calculation
            merged_data = self._merge_price_and_ema_data(price_data, moving_averages)
            
            # Calculate breakout beauty score using current price as breakout price
            beauty_analysis = self.breakout_analyzer.calculate_breakout_beauty_score(
                merged_data, 
                near_ath_detection['detection_date'], 
                near_ath_detection['current_price']
            )
            
            # Add beauty score to Near ATH detection
            near_ath_detection.update(beauty_analysis)
            
            logger.info(f"Near ATH detected: {symbol_with_market} - ${near_ath_detection['current_price']} ({near_ath_detection['distance_from_ath_percentage']}% from ATH ${near_ath_detection['ath_price']}) - Beauty: {beauty_analysis.get('beauty_score', 'N/A')} ({beauty_analysis.get('grade', 'N/A')})")
            self.storage.save_near_ath_detection(near_ath_detection)
    
    def _merge_price_and_ema_data(self, price_data: List[Dict], moving_averages: List[Dict] = None) -> List[Dict]:
        """
        Merge price data with EMA data for beauty score calculation
        
        Args:
            price_data: List of price records
            moving_averages: List of moving average records
            
        Returns:
            List of merged records with both price and EMA data
        """
        if not moving_averages:
            logger.warning("No moving averages data available for beauty score calculation")
            return price_data
        
        # Create a lookup dictionary for EMAs by date
        ema_lookup = {record['date']: record for record in moving_averages}
        
        # Merge price data with EMA data
        merged_data = []
        for price_record in price_data:
            merged_record = price_record.copy()
            
            # Add EMA data if available for this date
            date = price_record['date']
            if date in ema_lookup:
                ema_record = ema_lookup[date]
                
                # Convert Decimal to float for EMA values
                for ema_field in ['ema_7', 'ema_30', 'ema_50', 'ema_200']:
                    if ema_field in ema_record and ema_record[ema_field] is not None:
                        merged_record[ema_field] = float(ema_record[ema_field])
                    else:
                        merged_record[ema_field] = None
            else:
                # No EMA data for this date
                merged_record['ema_7'] = None
                merged_record['ema_30'] = None
                merged_record['ema_50'] = None
                merged_record['ema_200'] = None
            
            merged_data.append(merged_record)
        
        logger.info(f"Merged {len(price_data)} price records with {len(moving_averages)} EMA records")
        return merged_data