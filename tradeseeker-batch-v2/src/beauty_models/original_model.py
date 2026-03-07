"""
Original Beauty Score Model (v1.0)

The original beauty score calculation model with fixed weights.
This preserves the existing algorithm as a baseline.
"""

from typing import Dict, List, Any
from statistics import mean, stdev
from .base_model import BaseBeautyModel

class OriginalBeautyModel(BaseBeautyModel):
    """Original beauty score model with fixed component weights"""
    
    def __init__(self):
        super().__init__("original", "1.0")
        
        # Original fixed weights
        self.weights = {
            'consolidation': 0.25,  # 25% - How well consolidated before breakout
            'volume': 0.20,         # 20% - Volume surge on breakout
            'momentum': 0.25,       # 25% - Momentum continuation after breakout
            'green_candle': 0.20,   # 20% - Green candles around breakout
            'gap': 0.10             # 10% - Gap up on breakout
        }
    
    def calculate_beauty_score(self, pre_breakout: List[Dict], breakout_day: Dict, 
                             post_breakout: List[Dict]) -> Dict[str, Any]:
        """Calculate beauty score using original algorithm"""
        
        if not self.validate_input_data(pre_breakout, breakout_day, post_breakout):
            return {'beauty_score': 0, 'reason': 'Invalid input data'}
        
        try:
            # Calculate component scores
            consolidation_score = self._calculate_consolidation_score(pre_breakout)
            volume_score = self._calculate_volume_score(pre_breakout, breakout_day)
            momentum_score = self._calculate_momentum_score(pre_breakout, post_breakout)
            green_candle_score = self._calculate_green_candle_score(post_breakout)
            gap_score = self._calculate_gap_score(pre_breakout, breakout_day)
            
            self.logger.info(f"Component scores: consolidation={consolidation_score}, "
                           f"volume={volume_score}, momentum={momentum_score}, "
                           f"green={green_candle_score}, gap={gap_score}")
            
            # Weighted beauty score (0-100)
            beauty_score = (
                consolidation_score * self.weights['consolidation'] +
                volume_score * self.weights['volume'] +
                momentum_score * self.weights['momentum'] +
                green_candle_score * self.weights['green_candle'] +
                gap_score * self.weights['gap']
            )
            
            result = {
                'beauty_score': round(beauty_score, 1),
                'consolidation_score': round(consolidation_score, 1),
                'volume_score': round(volume_score, 1),
                'momentum_score': round(momentum_score, 1),
                'green_candle_score': round(green_candle_score, 1),
                'gap_score': round(gap_score, 1),
                'grade': self._get_beauty_grade(beauty_score),
                'model_name': self.model_name,
                'model_version': self.version
            }
            
            self.logger.info(f"Final beauty score: {result['beauty_score']} ({result['grade']})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating beauty score: {str(e)}")
            return {'beauty_score': 0, 'reason': f'Error: {str(e)}'}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get original model information"""
        return {
            'name': self.model_name,
            'version': self.version,
            'description': 'Original beauty score model with fixed component weights',
            'weights': self.weights.copy(),
            'components': [
                'consolidation_score',
                'volume_score', 
                'momentum_score',
                'green_candle_score',
                'gap_score'
            ],
            'created_date': '2024-01-01',
            'is_trainable': False
        }
    
    def _calculate_consolidation_score(self, pre_breakout: List[Dict]) -> float:
        """Score how well the price consolidated before breakout (0-100)"""
        if len(pre_breakout) < 5:
            return 50
        
        closes = [float(record['close']) for record in pre_breakout]
        avg_price = mean(closes)
        
        if avg_price == 0:
            return 50
        
        try:
            price_std = stdev(closes)
            coefficient_of_variation = (price_std / avg_price) * 100
            
            if coefficient_of_variation <= 5:
                score = 90 + (5 - coefficient_of_variation) * 2
            elif coefficient_of_variation <= 20:
                score = 90 - ((coefficient_of_variation - 5) * 6)
            else:
                score = max(0, 20 - (coefficient_of_variation - 20))
            
            return min(100, max(0, score))
        except:
            return 50
    
    def _calculate_volume_score(self, pre_breakout: List[Dict], breakout_day: Dict) -> float:
        """Score volume surge on breakout day (0-100)"""
        if len(pre_breakout) < 5:
            return 50
        
        pre_volumes = [float(record['volume']) for record in pre_breakout[-10:]]
        avg_volume = mean(pre_volumes) if pre_volumes else 1
        breakout_volume = float(breakout_day['volume'])
        
        if avg_volume == 0:
            return 50
        
        volume_ratio = breakout_volume / avg_volume
        
        if volume_ratio >= 3.0:
            return 100
        elif volume_ratio >= 2.0:
            return 80 + (volume_ratio - 2.0) * 20
        elif volume_ratio >= 1.5:
            return 60 + (volume_ratio - 1.5) * 40
        elif volume_ratio >= 1.0:
            return 40 + (volume_ratio - 1.0) * 40
        else:
            return max(0, volume_ratio * 40)
    
    def _calculate_momentum_score(self, pre_breakout: List[Dict], post_breakout: List[Dict]) -> float:
        """Score momentum continuation after breakout (0-100)"""
        if len(post_breakout) < 2:
            return 50
        
        breakout_price = float(post_breakout[0]['close'])
        momentum_points = 0
        total_days = min(5, len(post_breakout) - 1)
        
        for i in range(1, total_days + 1):
            if i < len(post_breakout):
                current_price = float(post_breakout[i]['close'])
                price_change = (current_price - breakout_price) / breakout_price * 100
                
                if price_change > 5:
                    momentum_points += 25
                elif price_change > 2:
                    momentum_points += 20
                elif price_change > 0:
                    momentum_points += 15
                elif price_change > -2:
                    momentum_points += 10
                else:
                    momentum_points += 0
        
        return min(100, (momentum_points / total_days) * 4)
    
    def _calculate_green_candle_score(self, post_breakout: List[Dict]) -> float:
        """Score percentage of green candles around breakout (0-100)"""
        if len(post_breakout) < 2:
            return 50
        
        green_candles = 0
        total_candles = min(5, len(post_breakout))
        
        for record in post_breakout[:total_candles]:
            open_price = float(record['open'])
            close_price = float(record['close'])
            
            if close_price > open_price:
                green_candles += 1
        
        return (green_candles / total_candles) * 100
    
    def _calculate_gap_score(self, pre_breakout: List[Dict], breakout_day: Dict) -> float:
        """Score gap up on breakout day (0-100)"""
        if len(pre_breakout) == 0:
            return 50
        
        previous_close = float(pre_breakout[-1]['close'])
        breakout_open = float(breakout_day['open'])
        gap_percentage = ((breakout_open - previous_close) / previous_close) * 100
        
        if gap_percentage >= 5:
            return 100
        elif gap_percentage >= 2:
            return 70 + (gap_percentage - 2) * 10
        elif gap_percentage >= 0.5:
            return 50 + (gap_percentage - 0.5) * 13.33
        elif gap_percentage >= 0:
            return 30 + gap_percentage * 40
        else:
            return max(0, 30 + gap_percentage * 10)