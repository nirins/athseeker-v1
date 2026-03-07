"""
All-Time High (ATH) detection module
"""

from typing import Dict, List
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger()


class ATHDetector:
    """Handles ATH detection for all stocks"""
    
    def __init__(self, environment: str, max_daily_volatility: float = 100.0):
        """
        Initialize ATH Detector
        
        Args:
            environment: Environment name (dev, uat, prod)
            max_daily_volatility: Maximum allowed daily volatility percentage (default: 100%)
        """
        self.environment = environment
        self.max_daily_volatility = max_daily_volatility
    
    def check_ath_detection(self, symbol: str, market_code: str, price_data: List[Dict]) -> Dict:
        """
        Check if symbol has reached a new all-time high in the last 21 days
        Returns the highest ATH found in that period
        
        Args:
            symbol: Symbol with market code (e.g., AAPL.US)
            market_code: Market code
            price_data: List of price records sorted by date
            
        Returns:
            ATH detection record if ATH detected, None otherwise
        """
        try:
            if not price_data or len(price_data) < 2:
                return None
            
            # Track running maximum and minimum as we iterate
            running_max = 0.0
            running_min = float('inf')
            highest_ath_record = None
            
            # Check each record to see if it's an ATH when it occurred
            for i, record in enumerate(price_data):
                current_price = float(record['close'])
                high_price = float(record['high'])
                low_price = float(record['low'])
                
                # Filter out stocks with excessive daily volatility
                if low_price > 0:  # Avoid division by zero
                    daily_volatility = ((high_price - low_price) / low_price) * 100
                    if daily_volatility > self.max_daily_volatility:
                        logger.info(f"Filtering out {symbol} on {record['date']} due to excessive volatility: {daily_volatility:.1f}% (max: {self.max_daily_volatility}%)")
                        continue
                
                # Skip first record (no history to compare against)
                if i == 0:
                    running_max = current_price
                    running_min = current_price
                    continue
                
                # Check if this is an ATH (current price > previous maximum)
                if current_price > running_max:
                    # Check if this record is within the last 21 records
                    if i >= len(price_data) - 21:
                        # Keep track of the highest ATH in the recent period
                        if highest_ath_record is None or current_price > highest_ath_record['ath_price']:
                            percentage_gain = ((current_price - running_min) / running_min) * 100
                            
                            highest_ath_record = {
                                'symbol': symbol,
                                'detection_date': record['date'],
                                'ath_price': current_price,
                                'ath_percentage_gain': round(percentage_gain, 2),
                                'market_code': market_code,
                                'detected_at': datetime.now().isoformat(),
                                'ttl': int((datetime.now() + timedelta(days=30)).timestamp())
                            }
                
                # Update running maximum and minimum
                running_max = max(running_max, current_price)
                running_min = min(running_min, current_price)
            
            return highest_ath_record
                
        except Exception as e:
            logger.error(f"Error in ATH detection for {symbol}: {str(e)}")
            return None