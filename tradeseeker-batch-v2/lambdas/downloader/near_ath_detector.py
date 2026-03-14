"""
Near All-Time High (Near ATH) detection module
"""

from typing import Dict, List
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger()


class NearATHDetector:
    """Handles Near ATH detection for all stocks"""
    
    def __init__(self, environment: str, max_daily_volatility: float = 100.0, near_ath_threshold: float = 10.0):
        """
        Initialize Near ATH Detector
        
        Args:
            environment: Environment name (dev, uat, prod)
            max_daily_volatility: Maximum allowed daily volatility percentage (default: 100%)
            near_ath_threshold: Percentage threshold for "near" ATH (default: 10% below ATH)
        """
        self.environment = environment
        self.max_daily_volatility = max_daily_volatility
        self.near_ath_threshold = near_ath_threshold
    
    def check_near_ath_detection(self, symbol: str, market_code: str, price_data: List[Dict]) -> Dict:
        """
        Check if symbol is near its all-time high in the last 21 days
        Returns the closest approach to ATH found in that period
        
        Args:
            symbol: Symbol with market code (e.g., AAPL.US)
            market_code: Market code
            price_data: List of price records sorted by date
            
        Returns:
            Near ATH detection record if near ATH detected, None otherwise
        """
        try:
            if not price_data or len(price_data) < 2:
                return None
            
            # Pre-filter: Check if stock has excessive volatility in entire history
            # If ANY day in the full price history exceeds volatility threshold, reject the entire stock
            for record in price_data:
                high_price = float(record['high'])
                low_price = float(record['low'])
                
                if low_price > 0:  # Avoid division by zero
                    daily_volatility = ((high_price - low_price) / low_price) * 100
                    if daily_volatility > self.max_daily_volatility:
                        logger.info(f"Rejecting {symbol} entirely due to excessive volatility on {record['date']}: {daily_volatility:.1f}% (max: {self.max_daily_volatility}%)")
                        return None
            
            # Find the all-time high across entire history
            all_time_high = 0.0
            ath_date = None
            
            for record in price_data:
                current_price = float(record['close'])
                if current_price > all_time_high:
                    all_time_high = current_price
                    ath_date = record['date']
            
            if all_time_high == 0.0:
                return None
            
            # Calculate the near ATH threshold price
            near_ath_price_threshold = all_time_high * (1 - self.near_ath_threshold / 100)
            
            # Track the closest approach to ATH in the last 21 records
            closest_near_ath_record = None
            
            # Calculate running minimum from all historical data for percentage gain
            historical_min = float('inf')
            for record in price_data:
                historical_min = min(historical_min, float(record['close']))
            
            # Check the last 21 records for near ATH conditions
            recent_records = price_data[-21:] if len(price_data) >= 21 else price_data
            
            for record in recent_records:
                current_price = float(record['close'])
                
                # Check if current price is within near ATH threshold but not exactly ATH
                if (current_price >= near_ath_price_threshold and 
                    current_price < all_time_high):
                    
                    # Calculate how close we are to ATH (percentage below ATH)
                    distance_from_ath = ((all_time_high - current_price) / all_time_high) * 100
                    
                    # Keep track of the closest approach (smallest distance from ATH)
                    if (closest_near_ath_record is None or 
                        distance_from_ath < closest_near_ath_record['distance_from_ath_percentage']):
                        
                        percentage_gain = ((current_price - historical_min) / historical_min) * 100
                        
                        closest_near_ath_record = {
                            'symbol': symbol,
                            'detection_date': record['date'],
                            'current_price': current_price,
                            'ath_price': all_time_high,
                            'ath_date': ath_date,
                            'distance_from_ath_percentage': round(distance_from_ath, 2),
                            'percentage_gain': round(percentage_gain, 2),
                            'market_code': market_code,
                            'detected_at': datetime.now().isoformat(),
                            'ttl': int((datetime.now() + timedelta(days=30)).timestamp())
                        }
            
            return closest_near_ath_record
                
        except Exception as e:
            logger.error(f"Error in Near ATH detection for {symbol}: {str(e)}")
            return None