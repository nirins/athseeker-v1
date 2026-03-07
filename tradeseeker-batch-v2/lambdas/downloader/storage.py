"""
Storage module for S3 and DynamoDB operations
"""

import json
import gzip
from typing import Dict, List
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()


class StorageManager:
    """Handles S3 and DynamoDB storage operations"""
    
    def __init__(self, environment: str, s3_bucket: str, dynamodb_table: str, s3_client, dynamodb_resource):
        """
        Initialize Storage Manager
        
        Args:
            environment: Environment name (dev, uat, prod)
            s3_bucket: S3 bucket name
            dynamodb_table: DynamoDB table name
            s3_client: Boto3 S3 client
            dynamodb_resource: Boto3 DynamoDB resource
        """
        self.environment = environment
        self.s3_bucket = s3_bucket
        self.dynamodb_table = dynamodb_table
        self.s3 = s3_client
        self.dynamodb = dynamodb_resource
    
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
    
    def save_to_dynamodb(self, task: Dict, price_data: List[Dict], moving_averages: List[Dict], 
                        candle_metrics: Dict):
        """
        Save OHLCV data and EMAs to DynamoDB as nested lists
        
        Args:
            task: Task dictionary with symbol and market info
            price_data: List of price records (filtered)
            moving_averages: List of moving average records
            candle_metrics: Candle metrics
        """
        symbol = task['symbol']
        market_code = task['marketCode']
        symbol_with_market = f"{symbol}.{market_code}"
        
        # Build prices list with Decimal types (reduced precision to save space)
        prices = []
        for record in price_data:
            prices.append({
                'date': record['date'],
                'open': Decimal(str(round(record['open'], 2))),
                'high': Decimal(str(round(record['high'], 2))),
                'low': Decimal(str(round(record['low'], 2))),
                'close': Decimal(str(round(record['close'], 2))),
                'adjusted_close': Decimal(str(round(record['adjusted_close'], 2))),
                'volume': int(record['volume'])
            })
        
        # Prepare item for DynamoDB
        item = {
            'symbol': symbol_with_market,
            'market_code': market_code,
            'prices': prices,
            'moving_averages': moving_averages,
            'total_records': len(price_data),
            'stored_records': len(price_data),
            'oldest_date': price_data[0]['date'] if price_data else None,
            'latest_date': price_data[-1]['date'] if price_data else None,
            'green_days_30d_pct': candle_metrics['green_days_pct'] if candle_metrics else None,
            'max_red_candle_30d_pct': candle_metrics['max_red_candle_pct'] if candle_metrics else None,
            'updated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Saving to DynamoDB: {self.dynamodb_table}/{symbol_with_market} ({len(price_data)} records)")
        
        try:
            table = self.dynamodb.Table(self.dynamodb_table)
            table.put_item(Item=item)
            
            logger.info(f"Successfully saved to DynamoDB: {symbol_with_market}")
            
        except Exception as e:
            logger.error(f"Error saving to DynamoDB: {str(e)}")
            raise
    
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
    
    def save_ath_detection(self, detection: Dict):
        """
        Save ATH detection record to DynamoDB (one record per symbol, overwrites existing)
        
        Args:
            detection: ATH detection record dictionary
        """
        try:
            table_name = f"ts-batch-v2-{self.environment}-ath"
            table = self.dynamodb.Table(table_name)
            
            # Log what we're about to save
            logger.info(f"Saving ATH detection with fields: {list(detection.keys())}")
            if 'beauty_score' in detection:
                logger.info(f"Beauty score fields: beauty_score={detection.get('beauty_score')}, grade={detection.get('grade')}")
            else:
                logger.warning("No beauty_score field found in detection record!")
            
            # Convert float values to Decimal for DynamoDB
            detection_record = {
                k: Decimal(str(v)) if isinstance(v, float) else v
                for k, v in detection.items()
            }
            
            # Save ATH record (will overwrite existing record with same symbol)
            table.put_item(Item=detection_record)
            logger.info(f"ATH detection saved: {detection['symbol']} - ${detection['ath_price']} (+{detection['ath_percentage_gain']}%)")
                
        except Exception as e:
            logger.error(f"Error saving ATH detection for {detection['symbol']}: {str(e)}")
            # Don't raise - this is not critical