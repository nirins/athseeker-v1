"""
Breakout Beauty Score Analysis Module
Analyzes ATH breakouts and assigns a beauty score based on technical characteristics
"""

from typing import Dict, List
import logging
import sys
import os

# Add the src directory to the path to import beauty models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

try:
    from beauty_models.model_factory import get_active_beauty_model
    MODEL_SYSTEM_AVAILABLE = True
except ImportError:
    # Fallback to original calculation if model system not available
    MODEL_SYSTEM_AVAILABLE = False

# Always import statistics for fallback method
from statistics import mean, stdev

logger = logging.getLogger()


class BreakoutAnalyzer:
    """Analyzes ATH breakouts and calculates beauty scores"""
    
    def __init__(self):
        """Initialize Breakout Analyzer"""
        pass
    
    def calculate_breakout_beauty_score(self, price_data: List[Dict], ath_date: str, ath_price: float) -> Dict:
        """
        Calculate a beauty score for an ATH breakout (0-100 scale)
        
        Args:
            price_data: List of price records sorted by date
            ath_date: Date of the ATH
            ath_price: Price of the ATH
            
        Returns:
            Dict with beauty score and component scores
        """
        try:
            logger.info(f"Calculating beauty score for ATH on {ath_date} at ${ath_price}")
            
            # Find ATH index
            ath_index = None
            for i, record in enumerate(price_data):
                if record['date'] == ath_date:
                    ath_index = i
                    break
            
            if ath_index is None:
                logger.warning(f"ATH date {ath_date} not found in price data")
                return {'beauty_score': 0, 'reason': 'ATH date not found in price data'}
            
            logger.info(f"ATH found at index {ath_index} out of {len(price_data)} records")
            
            # Use new model system if available
            if MODEL_SYSTEM_AVAILABLE:
                return self._calculate_with_model_system(price_data, ath_index)
            else:
                # Fallback to original calculation
                return self._calculate_with_original_method(price_data, ath_index)
                
        except Exception as e:
            logger.error(f"Error calculating breakout beauty score: {str(e)}")
            return {'beauty_score': 0, 'reason': f'Error: {str(e)}'}
    
    def _calculate_with_model_system(self, price_data: List[Dict], ath_index: int) -> Dict:
        """Calculate beauty score using the new model system"""
        try:
            # Get the active beauty model
            model = get_active_beauty_model()
            
            # Prepare data segments for the model
            pre_breakout = price_data[max(0, ath_index - 20):ath_index]
            breakout_day = price_data[ath_index]
            post_breakout = price_data[ath_index:min(len(price_data), ath_index + 10)]
            
            # Calculate beauty score using the model
            result = model.calculate_beauty_score(pre_breakout, breakout_day, post_breakout)
            
            logger.info(f"Beauty score calculated using model: {model.model_name} v{model.version}")
            return result
            
        except Exception as e:
            logger.error(f"Error with model system, falling back to original: {str(e)}")
            return self._calculate_with_original_method(price_data, ath_index)
    
    def _calculate_with_original_method(self, price_data: List[Dict], ath_index: int) -> Dict:
        """Fallback to original beauty score calculation method"""
        try:
            # Require at least 10 days before ATH (reduced from 20)
            if ath_index < 10:
                logger.warning(f"Insufficient data before ATH: only {ath_index} records")
                return {'beauty_score': 0, 'reason': f'Insufficient data before ATH: only {ath_index} records'}
            
            # Get data windows (use available data, minimum 10 days before)
            days_before = min(20, ath_index)  # Use up to 20 days or whatever is available
            pre_breakout = price_data[max(0, ath_index-days_before):ath_index]
            breakout_day = price_data[ath_index]
            post_breakout = price_data[ath_index:min(len(price_data), ath_index+5)]  # 5 days after
            
            logger.info(f"Data windows: {len(pre_breakout)} pre-breakout, {len(post_breakout)} post-breakout")
            
            # Calculate component scores
            consolidation_score = self._calculate_consolidation_score(pre_breakout)
            volume_score = self._calculate_volume_score(pre_breakout, breakout_day)
            momentum_score = self._calculate_momentum_score(pre_breakout, post_breakout)
            green_candle_score = self._calculate_green_candle_score(post_breakout)
            gap_score = self._calculate_gap_score(pre_breakout, breakout_day)
            
            logger.info(f"Component scores: consolidation={consolidation_score}, volume={volume_score}, momentum={momentum_score}, green={green_candle_score}, gap={gap_score}")
            
            # Weighted beauty score (0-100) - Original fixed weights
            beauty_score = (
                consolidation_score * 0.25 +  # 25% - How well consolidated before breakout
                volume_score * 0.20 +         # 20% - Volume surge on breakout
                momentum_score * 0.25 +       # 25% - Momentum continuation after breakout
                green_candle_score * 0.20 +   # 20% - Green candles around breakout
                gap_score * 0.10              # 10% - Gap up on breakout
            )
            
            result = {
                'beauty_score': round(beauty_score, 1),
                'consolidation_score': round(consolidation_score, 1),
                'volume_score': round(volume_score, 1),
                'momentum_score': round(momentum_score, 1),
                'green_candle_score': round(green_candle_score, 1),
                'gap_score': round(gap_score, 1),
                'grade': self._get_beauty_grade(beauty_score),
                'model_name': 'original_fallback',
                'model_version': '1.0'
            }
            
            logger.info(f"Final beauty score: {result['beauty_score']} ({result['grade']})")
            return result
            
        except Exception as e:
            logger.error(f"Error in original calculation method: {str(e)}")
            return {'beauty_score': 0, 'reason': f'Error: {str(e)}'}
    
    def _calculate_consolidation_score(self, pre_breakout: List[Dict]) -> float:
        """
        Score how well the price consolidated before breakout (0-100)
        Lower volatility = higher score
        """
        if len(pre_breakout) < 5:  # Reduced from 10 to 5
            return 50  # Default score instead of 0
        
        # Calculate price volatility (coefficient of variation)
        closes = [float(record['close']) for record in pre_breakout]
        avg_price = mean(closes)
        
        if avg_price == 0:
            return 50
        
        try:
            price_std = stdev(closes)
            coefficient_of_variation = (price_std / avg_price) * 100
            
            # Lower CV = better consolidation (invert and scale)
            # CV < 5% = excellent (90-100), CV > 20% = poor (0-20)
            if coefficient_of_variation <= 5:
                score = 90 + (5 - coefficient_of_variation) * 2
            elif coefficient_of_variation <= 20:
                score = 90 - ((coefficient_of_variation - 5) * 6)
            else:
                score = max(0, 20 - (coefficient_of_variation - 20))
            
            return min(100, max(0, score))
            
        except:
            return 50  # Default if calculation fails
    
    def _calculate_volume_score(self, pre_breakout: List[Dict], breakout_day: Dict) -> float:
        """
        Score volume surge on breakout day (0-100)
        Higher relative volume = higher score
        """
        if len(pre_breakout) < 5:
            return 50
        
        # Calculate average volume before breakout
        pre_volumes = [float(record['volume']) for record in pre_breakout[-10:]]
        avg_volume = mean(pre_volumes) if pre_volumes else 1
        
        breakout_volume = float(breakout_day['volume'])
        
        if avg_volume == 0:
            return 50
        
        # Volume ratio
        volume_ratio = breakout_volume / avg_volume
        
        # Score based on volume surge
        if volume_ratio >= 3.0:      # 3x+ volume = excellent
            return 100
        elif volume_ratio >= 2.0:    # 2x volume = very good
            return 80 + (volume_ratio - 2.0) * 20
        elif volume_ratio >= 1.5:    # 1.5x volume = good
            return 60 + (volume_ratio - 1.5) * 40
        elif volume_ratio >= 1.0:    # Normal volume = average
            return 40 + (volume_ratio - 1.0) * 40
        else:                        # Below average volume = poor
            return max(0, volume_ratio * 40)
    
    def _calculate_momentum_score(self, pre_breakout: List[Dict], post_breakout: List[Dict]) -> float:
        """
        Score momentum continuation after breakout (0-100)
        Continued upward movement = higher score
        """
        if len(post_breakout) < 2:
            return 50
        
        breakout_price = float(post_breakout[0]['close'])
        
        # Calculate price movement in days following breakout
        momentum_points = 0
        total_days = min(5, len(post_breakout) - 1)
        
        for i in range(1, total_days + 1):
            if i < len(post_breakout):
                current_price = float(post_breakout[i]['close'])
                price_change = (current_price - breakout_price) / breakout_price * 100
                
                # Award points for continued upward movement
                if price_change > 5:      # >5% gain = excellent
                    momentum_points += 25
                elif price_change > 2:    # >2% gain = good
                    momentum_points += 20
                elif price_change > 0:    # Any gain = okay
                    momentum_points += 15
                elif price_change > -2:   # Small loss = neutral
                    momentum_points += 10
                else:                     # Large loss = poor
                    momentum_points += 0
        
        return min(100, (momentum_points / total_days) * 4)  # Scale to 0-100
    
    def _calculate_green_candle_score(self, post_breakout: List[Dict]) -> float:
        """
        Score percentage of green candles around breakout (0-100)
        More green candles = higher score
        """
        if len(post_breakout) < 2:
            return 50
        
        green_candles = 0
        total_candles = min(5, len(post_breakout))
        
        for record in post_breakout[:total_candles]:
            open_price = float(record['open'])
            close_price = float(record['close'])
            
            if close_price > open_price:  # Green candle
                green_candles += 1
        
        green_percentage = (green_candles / total_candles) * 100
        return green_percentage
    
    def _calculate_gap_score(self, pre_breakout: List[Dict], breakout_day: Dict) -> float:
        """
        Score gap up on breakout day (0-100)
        Larger gap = higher score
        """
        if len(pre_breakout) == 0:
            return 50
        
        previous_close = float(pre_breakout[-1]['close'])
        breakout_open = float(breakout_day['open'])
        
        gap_percentage = ((breakout_open - previous_close) / previous_close) * 100
        
        # Score based on gap size
        if gap_percentage >= 5:       # 5%+ gap = excellent
            return 100
        elif gap_percentage >= 2:     # 2%+ gap = very good
            return 70 + (gap_percentage - 2) * 10
        elif gap_percentage >= 0.5:   # Small gap = good
            return 50 + (gap_percentage - 0.5) * 13.33
        elif gap_percentage >= 0:     # No gap but higher open = okay
            return 30 + gap_percentage * 40
        else:                         # Gap down = poor
            return max(0, 30 + gap_percentage * 10)
    
    def _get_beauty_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'