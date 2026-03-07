"""
EMA-Based Beauty Score Model (v1.0)

A beauty score model that uses EMA (Exponential Moving Average) relationships
as primary features. The core concept is that faster EMAs should be above
slower EMAs for bullish momentum, resulting in higher beauty scores.

EMA Hierarchy (fastest to slowest): EMA7 > EMA30 > EMA50 > EMA200
"""

from typing import Dict, List, Any
from statistics import mean
from .base_model import BaseBeautyModel

class EMABeautyModel(BaseBeautyModel):
    """EMA-based beauty score model focusing on moving average relationships"""
    
    def __init__(self):
        super().__init__("ema_model", "1.0")
        
        # Component weights for EMA-based scoring
        self.weights = {
            'ema_alignment': 0.40,      # 40% - EMA hierarchy alignment (7>30>50>200)
            'ema_separation': 0.15,     # 15% - Distance between EMAs (reduced from 25%)
            'ema_momentum': 0.10,       # 10% - EMA slope/momentum (reduced from 20%)
            'price_vs_emas': 0.30,      # 30% - Price position relative to EMAs (increased from 10%)
            'ema_convergence': 0.05     # 5% - EMA convergence/divergence patterns
        }
    
    def calculate_beauty_score(self, pre_breakout: List[Dict], breakout_day: Dict, 
                             post_breakout: List[Dict]) -> Dict[str, Any]:
        """Calculate beauty score using EMA relationships"""
        
        if not self.validate_input_data(pre_breakout, breakout_day, post_breakout):
            return {'beauty_score': 0, 'reason': 'Invalid input data'}
        
        try:
            # Calculate EMA-based component scores
            ema_alignment_score = self._calculate_ema_alignment_score(pre_breakout, breakout_day, post_breakout)
            ema_separation_score = self._calculate_ema_separation_score(pre_breakout, breakout_day, post_breakout)
            ema_momentum_score = self._calculate_ema_momentum_score(pre_breakout, breakout_day, post_breakout)
            price_vs_emas_score = self._calculate_price_vs_emas_score(pre_breakout, breakout_day, post_breakout)
            ema_convergence_score = self._calculate_ema_convergence_score(pre_breakout, breakout_day, post_breakout)
            
            self.logger.info(f"EMA component scores: alignment={ema_alignment_score}, "
                           f"separation={ema_separation_score}, momentum={ema_momentum_score}, "
                           f"price_vs_emas={price_vs_emas_score}, convergence={ema_convergence_score}")
            
            # Weighted beauty score (0-100)
            beauty_score = (
                ema_alignment_score * self.weights['ema_alignment'] +
                ema_separation_score * self.weights['ema_separation'] +
                ema_momentum_score * self.weights['ema_momentum'] +
                price_vs_emas_score * self.weights['price_vs_emas'] +
                ema_convergence_score * self.weights['ema_convergence']
            )
            
            result = {
                'beauty_score': round(beauty_score, 1),
                'ema_alignment_score': round(ema_alignment_score, 1),
                'ema_separation_score': round(ema_separation_score, 1),
                'ema_momentum_score': round(ema_momentum_score, 1),
                'price_vs_emas_score': round(price_vs_emas_score, 1),
                'ema_convergence_score': round(ema_convergence_score, 1),
                'grade': self._get_beauty_grade(beauty_score),
                'model_name': self.model_name,
                'model_version': self.version
            }
            
            self.logger.info(f"Final EMA beauty score: {result['beauty_score']} ({result['grade']})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating EMA beauty score: {str(e)}")
            return {'beauty_score': 0, 'reason': f'Error: {str(e)}'}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get EMA model information"""
        return {
            'name': self.model_name,
            'version': self.version,
            'description': 'EMA-based beauty score model emphasizing price position and EMA alignment with recent data emphasis',
            'weights': self.weights.copy(),
            'components': [
                'ema_alignment_score',
                'ema_separation_score', 
                'ema_momentum_score',
                'price_vs_emas_score',
                'ema_convergence_score'
            ],
            'ema_periods': [7, 30, 50, 200],
            'created_date': '2024-03-07',
            'is_trainable': True,
            'features': [
                'EMA hierarchy alignment (7>30>50>200) - weighted toward last 21 days (40%)',
                'Price position vs EMAs - weighted toward last 21 days (30%)',
                'EMA separation distances - weighted toward last 21 days (15%)',
                'EMA slope momentum (10%)',
                'EMA convergence patterns (5%)'
            ],
            'weighting_strategy': 'Recent 21 days weighted more heavily (1.0x recent, 0.3x oldest). Emphasis on price position relative to EMAs.',
            'rationale': 'Price above EMAs is the most direct indicator of bullish momentum after EMA alignment'
        }
    
    def _get_ema_values(self, record: Dict) -> Dict[str, float]:
        """Extract EMA values from a price record, handling None values"""
        return {
            'ema_7': float(record.get('ema_7', 0)) if record.get('ema_7') is not None else None,
            'ema_30': float(record.get('ema_30', 0)) if record.get('ema_30') is not None else None,
            'ema_50': float(record.get('ema_50', 0)) if record.get('ema_50') is not None else None,
            'ema_200': float(record.get('ema_200', 0)) if record.get('ema_200') is not None else None
        }
    
    def _calculate_ema_alignment_score(self, pre_breakout: List[Dict], breakout_day: Dict, 
                                     post_breakout: List[Dict]) -> float:
        """
        Score EMA hierarchy alignment (0-100)
        Perfect alignment: EMA7 > EMA30 > EMA50 > EMA200
        Weights recent data (last 21 days) more heavily
        """
        # Combine all data for analysis
        all_data = pre_breakout + [breakout_day] + post_breakout
        
        # Focus on the last 21 records (most recent data)
        recent_data = all_data[-21:] if len(all_data) >= 21 else all_data
        
        alignment_scores = []
        weights = []
        
        for i, record in enumerate(recent_data):
            emas = self._get_ema_values(record)
            
            # Skip if any EMA is missing
            if any(ema is None for ema in emas.values()):
                continue
            
            # Check each EMA relationship
            score = 0
            total_checks = 6  # Number of pairwise comparisons
            
            # EMA7 > EMA30
            if emas['ema_7'] > emas['ema_30']:
                score += 1
            
            # EMA7 > EMA50
            if emas['ema_7'] > emas['ema_50']:
                score += 1
            
            # EMA7 > EMA200
            if emas['ema_7'] > emas['ema_200']:
                score += 1
            
            # EMA30 > EMA50
            if emas['ema_30'] > emas['ema_50']:
                score += 1
            
            # EMA30 > EMA200
            if emas['ema_30'] > emas['ema_200']:
                score += 1
            
            # EMA50 > EMA200
            if emas['ema_50'] > emas['ema_200']:
                score += 1
            
            alignment_score = (score / total_checks) * 100
            alignment_scores.append(alignment_score)
            
            # Weight calculation: more recent data gets higher weight
            # Most recent day gets weight 1.0, oldest day gets weight 0.3
            position_from_end = len(recent_data) - i - 1  # 0 = most recent
            weight = 1.0 - (position_from_end * 0.7 / max(1, len(recent_data) - 1))
            weights.append(weight)
        
        if not alignment_scores:
            return 50  # Neutral score if no valid data
        
        # Calculate weighted average (recent data weighted more heavily)
        weighted_sum = sum(score * weight for score, weight in zip(alignment_scores, weights))
        total_weight = sum(weights)
        
        weighted_average = weighted_sum / total_weight if total_weight > 0 else 50
        
        self.logger.info(f"EMA alignment: {len(alignment_scores)} periods analyzed, "
                        f"recent weight emphasis, score: {weighted_average:.1f}")
        
        return weighted_average
    
    def _calculate_ema_separation_score(self, pre_breakout: List[Dict], breakout_day: Dict, 
                                      post_breakout: List[Dict]) -> float:
        """
        Score EMA separation distances (0-100)
        Wider separation indicates stronger trend
        Weights recent data (last 21 days) more heavily
        """
        # Combine all data for analysis
        all_data = pre_breakout + [breakout_day] + post_breakout
        
        # Focus on the last 21 records (most recent data)
        recent_data = all_data[-21:] if len(all_data) >= 21 else all_data
        
        separation_scores = []
        weights = []
        
        for i, record in enumerate(recent_data):
            emas = self._get_ema_values(record)
            
            # Skip if any EMA is missing
            if any(ema is None for ema in emas.values()):
                continue
            
            # Calculate percentage separations
            separations = []
            
            # EMA7 vs EMA30 separation
            if emas['ema_30'] > 0:
                sep = ((emas['ema_7'] - emas['ema_30']) / emas['ema_30']) * 100
                separations.append(max(0, sep))  # Only positive separations count
            
            # EMA30 vs EMA50 separation
            if emas['ema_50'] > 0:
                sep = ((emas['ema_30'] - emas['ema_50']) / emas['ema_50']) * 100
                separations.append(max(0, sep))
            
            # EMA50 vs EMA200 separation
            if emas['ema_200'] > 0:
                sep = ((emas['ema_50'] - emas['ema_200']) / emas['ema_200']) * 100
                separations.append(max(0, sep))
            
            if separations:
                # Average separation, capped at reasonable levels
                avg_separation = mean(separations)
                
                # Score based on separation percentage
                if avg_separation >= 5.0:
                    score = 100
                elif avg_separation >= 3.0:
                    score = 80 + (avg_separation - 3.0) * 10
                elif avg_separation >= 1.0:
                    score = 60 + (avg_separation - 1.0) * 10
                elif avg_separation >= 0.5:
                    score = 40 + (avg_separation - 0.5) * 40
                else:
                    score = avg_separation * 80
                
                separation_scores.append(min(100, score))
                
                # Weight calculation: more recent data gets higher weight
                position_from_end = len(recent_data) - i - 1  # 0 = most recent
                weight = 1.0 - (position_from_end * 0.7 / max(1, len(recent_data) - 1))
                weights.append(weight)
        
        if not separation_scores:
            return 50  # Neutral score if no valid data
        
        # Calculate weighted average (recent data weighted more heavily)
        weighted_sum = sum(score * weight for score, weight in zip(separation_scores, weights))
        total_weight = sum(weights)
        
        weighted_average = weighted_sum / total_weight if total_weight > 0 else 50
        
        self.logger.info(f"EMA separation: {len(separation_scores)} periods analyzed, "
                        f"recent weight emphasis, score: {weighted_average:.1f}")
        
        return weighted_average
    
    def _calculate_ema_momentum_score(self, pre_breakout: List[Dict], breakout_day: Dict, 
                                    post_breakout: List[Dict]) -> float:
        """
        Score EMA momentum/slope (0-100)
        Rising EMAs indicate bullish momentum
        """
        # Need at least 3 periods to calculate momentum
        all_data = pre_breakout[-5:] + [breakout_day] + post_breakout[:3]
        
        if len(all_data) < 3:
            return 50
        
        momentum_scores = []
        
        # Calculate momentum for each EMA
        for ema_period in ['ema_7', 'ema_30', 'ema_50', 'ema_200']:
            ema_values = []
            
            for record in all_data:
                emas = self._get_ema_values(record)
                if emas[ema_period] is not None:
                    ema_values.append(emas[ema_period])
            
            if len(ema_values) >= 3:
                # Calculate slope (momentum) over the period
                momentum = 0
                for i in range(1, len(ema_values)):
                    if ema_values[i-1] > 0:
                        change = ((ema_values[i] - ema_values[i-1]) / ema_values[i-1]) * 100
                        momentum += change
                
                # Average momentum per period
                avg_momentum = momentum / (len(ema_values) - 1)
                
                # Score based on momentum
                if avg_momentum >= 2.0:
                    score = 100
                elif avg_momentum >= 1.0:
                    score = 80 + (avg_momentum - 1.0) * 20
                elif avg_momentum >= 0.5:
                    score = 60 + (avg_momentum - 0.5) * 40
                elif avg_momentum >= 0:
                    score = 50 + avg_momentum * 20
                else:
                    score = max(0, 50 + avg_momentum * 25)  # Penalty for declining EMAs
                
                momentum_scores.append(score)
        
        if not momentum_scores:
            return 50
        
        return mean(momentum_scores)
    
    def _calculate_price_vs_emas_score(self, pre_breakout: List[Dict], breakout_day: Dict, 
                                     post_breakout: List[Dict]) -> float:
        """
        Score price position relative to EMAs (0-100)
        Price above all EMAs is bullish
        Weights recent data (last 21 days) more heavily
        """
        # Combine all data for analysis
        all_data = pre_breakout + [breakout_day] + post_breakout
        
        # Focus on the last 21 records (most recent data)
        recent_data = all_data[-21:] if len(all_data) >= 21 else all_data
        
        position_scores = []
        weights = []
        
        for i, record in enumerate(recent_data):
            emas = self._get_ema_values(record)
            close_price = float(record.get('close', 0))
            
            if close_price <= 0 or any(ema is None for ema in emas.values()):
                continue
            
            # Count how many EMAs the price is above
            above_count = 0
            total_emas = 4
            
            if close_price > emas['ema_7']:
                above_count += 1
            if close_price > emas['ema_30']:
                above_count += 1
            if close_price > emas['ema_50']:
                above_count += 1
            if close_price > emas['ema_200']:
                above_count += 1
            
            # Score based on how many EMAs price is above
            score = (above_count / total_emas) * 100
            position_scores.append(score)
            
            # Weight calculation: more recent data gets higher weight
            position_from_end = len(recent_data) - i - 1  # 0 = most recent
            weight = 1.0 - (position_from_end * 0.7 / max(1, len(recent_data) - 1))
            weights.append(weight)
        
        if not position_scores:
            return 50
        
        # Calculate weighted average (recent data weighted more heavily)
        weighted_sum = sum(score * weight for score, weight in zip(position_scores, weights))
        total_weight = sum(weights)
        
        weighted_average = weighted_sum / total_weight if total_weight > 0 else 50
        
        self.logger.info(f"Price vs EMAs: {len(position_scores)} periods analyzed, "
                        f"recent weight emphasis, score: {weighted_average:.1f}")
        
        return weighted_average
    
    def _calculate_ema_convergence_score(self, pre_breakout: List[Dict], breakout_day: Dict, 
                                       post_breakout: List[Dict]) -> float:
        """
        Score EMA convergence/divergence patterns (0-100)
        EMAs converging before breakout then diverging is bullish
        """
        # Need sufficient data to analyze convergence patterns
        all_data = pre_breakout[-10:] + [breakout_day] + post_breakout[:5]
        
        if len(all_data) < 5:
            return 50
        
        # Calculate EMA spreads over time
        spreads = []
        
        for record in all_data:
            emas = self._get_ema_values(record)
            
            if any(ema is None for ema in emas.values()):
                continue
            
            # Calculate spread between fastest and slowest EMA
            spread = emas['ema_7'] - emas['ema_200']
            if emas['ema_200'] > 0:
                spread_pct = (spread / emas['ema_200']) * 100
                spreads.append(spread_pct)
        
        if len(spreads) < 3:
            return 50
        
        # Find breakout point in spreads
        breakout_idx = len(pre_breakout[-10:])
        if breakout_idx >= len(spreads):
            breakout_idx = len(spreads) // 2
        
        # Analyze convergence before breakout
        pre_spreads = spreads[:breakout_idx]
        post_spreads = spreads[breakout_idx:]
        
        convergence_score = 50  # Default neutral
        
        if len(pre_spreads) >= 2 and len(post_spreads) >= 2:
            # Check if spreads were converging (getting smaller) before breakout
            pre_trend = pre_spreads[-1] - pre_spreads[0] if len(pre_spreads) > 1 else 0
            
            # Check if spreads are diverging (getting larger) after breakout
            post_trend = post_spreads[-1] - post_spreads[0] if len(post_spreads) > 1 else 0
            
            # Ideal pattern: convergence before, divergence after
            if pre_trend <= 0 and post_trend > 0:  # Converging then diverging
                convergence_score = 90
            elif pre_trend <= 0:  # Just converging before
                convergence_score = 70
            elif post_trend > 0:  # Just diverging after
                convergence_score = 70
            else:
                convergence_score = 30  # Poor pattern
        
        return convergence_score