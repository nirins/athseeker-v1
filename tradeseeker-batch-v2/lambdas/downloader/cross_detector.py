"""
Cross detection module for golden cross and death cross signals
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger()


def _get_beauty_grade(score: float) -> str:
    """Convert numeric score to letter grade (same convention as beauty_models/base_model.py)"""
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


def _find_index_by_date(merged_data: List[Dict], date: str) -> Optional[int]:
    for i, record in enumerate(merged_data):
        if record['date'] == date:
            return i
    return None


def _crossover_strength_score(sep_pct: float) -> float:
    """
    Score the EMA50/EMA200 separation right at the cross (0-100).
    Same curve shape as ema_model.py's separation score.
    """
    sep_pct = max(0.0, sep_pct)
    if sep_pct >= 5.0:
        return 100.0
    elif sep_pct >= 3.0:
        return 80 + (sep_pct - 3.0) * 10
    elif sep_pct >= 1.0:
        return 60 + (sep_pct - 1.0) * 10
    elif sep_pct >= 0.5:
        return 40 + (sep_pct - 0.5) * 40
    else:
        return sep_pct * 80


def _volume_confirmation_score(volume_ratio: float) -> float:
    """Same curve shape as original_model.py's _calculate_volume_score"""
    if volume_ratio >= 3.0:
        return 100.0
    elif volume_ratio >= 2.0:
        return 80 + (volume_ratio - 2.0) * 20
    elif volume_ratio >= 1.5:
        return 60 + (volume_ratio - 1.5) * 40
    elif volume_ratio >= 1.0:
        return 40 + (volume_ratio - 1.0) * 40
    else:
        return max(0.0, volume_ratio * 40)


def _trend_quality_score(prior_cross_count: int) -> float:
    """Penalize whipsaw: crosses (either direction) in the 90 days before this one"""
    if prior_cross_count <= 0:
        return 100.0
    elif prior_cross_count == 1:
        return 70.0
    elif prior_cross_count == 2:
        return 40.0
    else:
        return 10.0


def _long_term_slope_score(slope_pct: float) -> float:
    """
    Score the EMA200 slope over the trailing 20 days (0-100). slope_pct should
    already be direction-adjusted by the caller (positive = favorable).
    """
    if slope_pct >= 1.0:
        return 100.0
    elif slope_pct >= 0.0:
        return 50 + slope_pct * 50
    else:
        return max(0.0, 50 + slope_pct * 25)


def _momentum_continuation_score(merged_data: List[Dict], cross_index: int, bullish: bool) -> float:
    """
    Score price follow-through over the 5 trading days after the cross
    (0-100). Same curve shape as original_model.py's momentum score;
    direction-adjusted so a death cross is rewarded for continued downside.
    """
    post = merged_data[cross_index:min(len(merged_data), cross_index + 6)]
    if len(post) < 2:
        return 50.0

    cross_close = float(post[0]['close'])
    if cross_close <= 0:
        return 50.0

    total_days = min(5, len(post) - 1)
    momentum_points = 0
    for i in range(1, total_days + 1):
        current_close = float(post[i]['close'])
        price_change = (current_close - cross_close) / cross_close * 100
        if not bullish:
            price_change = -price_change  # downside follow-through is "good" for a death cross

        if price_change > 5:
            momentum_points += 25
        elif price_change > 2:
            momentum_points += 20
        elif price_change > 0:
            momentum_points += 15
        elif price_change > -2:
            momentum_points += 10

    return min(100.0, (momentum_points / total_days) * 4)


class CrossDetector:
    """Handles cross signal detection"""
    
    def __init__(self, environment: str):
        """
        Initialize Cross Detector
        
        Args:
            environment: Environment name (dev, uat, prod)
        """
        self.environment = environment
    
    def detect_golden_cross(self, moving_averages: List[Dict], scan_days: int = 30) -> Dict:
        """
        Detect golden cross or death cross from moving averages
        Returns the MOST RECENT cross within scan_days
        
        Args:
            moving_averages: List of MA records sorted by date
            scan_days: Number of recent days to scan (default: 30)
            
        Returns:
            dict with most recent cross info or None
        """
        if len(moving_averages) < 2:
            return None
        
        # Only scan the last N days for performance
        start_index = max(0, len(moving_averages) - scan_days)
        
        # Scan through recent data to find the most recent golden cross
        most_recent_cross = None
        
        for i in range(start_index + 1, len(moving_averages)):
            today = moving_averages[i]
            yesterday = moving_averages[i-1]
            
            # Check if both EMAs exist
            if (today['ema_50'] is None or today['ema_200'] is None or
                yesterday['ema_50'] is None or yesterday['ema_200'] is None):
                continue
            
            # Convert Decimal to float for comparison
            today_50 = float(today['ema_50'])
            today_200 = float(today['ema_200'])
            yesterday_50 = float(yesterday['ema_50'])
            yesterday_200 = float(yesterday['ema_200'])
            
            # Golden Cross: 50 crosses above 200
            if today_50 > today_200 and yesterday_50 <= yesterday_200:
                most_recent_cross = {
                    'signal': 'GOLDEN_CROSS',
                    'date': today['date'],
                    'ema_50': today_50,
                    'ema_200': today_200,
                    'crossover_strength': round(today_50 - today_200, 2)
                }
            
            # Death Cross: 50 crosses below 200 (bearish)
            elif today_50 < today_200 and yesterday_50 >= yesterday_200:
                most_recent_cross = {
                    'signal': 'DEATH_CROSS',
                    'date': today['date'],
                    'ema_50': today_50,
                    'ema_200': today_200,
                    'crossover_strength': round(today_200 - today_50, 2)
                }

        return most_recent_cross

    def calculate_cross_beauty_score(self, merged_data: List[Dict], cross_info: Dict) -> Dict:
        """
        Calculate a beauty score for a golden/death cross (0-100 scale),
        mirroring the ATH breakout beauty score convention
        (beauty_models/original_model.py) but built around the cross event
        instead of a breakout day. See
        .local/design/beauty-score-remaining-strategies.md for the design.

        Components:
          - Crossover Strength (20%): how far EMA50 separated from EMA200
            right at the cross, normalized by price (not raw dollars/points,
            since markets span THB/HKD/CNY/KRW/TWD/USD)
          - Volume Confirmation (20%): volume on the cross day vs trailing
            30-day average
          - Momentum Continuation (25%): price follow-through over the 5
            trading days after the cross
          - Trend Quality (20%): penalizes whipsaw — crosses (either
            direction) in the 90 days before this one
          - Long-Term Trend Slope (15%): whether EMA200 itself was already
            turning in the cross's favor, not just EMA50 catching up to a
            still-opposite-trending EMA200

        Args:
            merged_data: Price records merged with ema_7/30/50/200, sorted
                by date (see downloader.py's _merge_price_and_ema_data)
            cross_info: Result of detect_golden_cross() — must have 'date',
                'signal' ('GOLDEN_CROSS' or 'DEATH_CROSS'), 'ema_50', 'ema_200'

        Returns:
            Dict with beauty_score, grade, and component scores. Falls back
            to a neutral 50/'D' result (not 0) when there isn't enough
            surrounding data to score a component, consistent with the ATH
            beauty model's handling of thin data.
        """
        try:
            cross_index = _find_index_by_date(merged_data, cross_info['date'])
            if cross_index is None:
                return {'beauty_score': 0, 'reason': 'Cross date not found in merged data'}

            is_golden = cross_info['signal'] == 'GOLDEN_CROSS'
            ema_50 = cross_info['ema_50']
            ema_200 = cross_info['ema_200']

            # 1. Crossover Strength
            if ema_200 > 0:
                sep_pct = ((ema_50 - ema_200) / ema_200 * 100) if is_golden else ((ema_200 - ema_50) / ema_200 * 100)
            else:
                sep_pct = 0.0
            crossover_strength_score = _crossover_strength_score(sep_pct)

            # 2. Volume Confirmation
            baseline_window = merged_data[max(0, cross_index - 30):cross_index]
            baseline_volumes = [float(r.get('volume', 0)) for r in baseline_window]
            avg_baseline_volume = sum(baseline_volumes) / len(baseline_volumes) if baseline_volumes else 0.0
            cross_volume = float(merged_data[cross_index].get('volume', 0))
            volume_ratio = (cross_volume / avg_baseline_volume) if avg_baseline_volume > 0 else 1.0
            volume_confirmation_score = _volume_confirmation_score(volume_ratio)

            # 3. Momentum Continuation
            momentum_continuation_score = _momentum_continuation_score(merged_data, cross_index, is_golden)

            # 4. Trend Quality (whipsaw penalty) — crosses in the trailing 90 days before this one
            window_start = max(0, cross_index - 90)
            prior_window = merged_data[window_start:cross_index]
            prior_cross_count = 0
            for i in range(1, len(prior_window)):
                prev, curr = prior_window[i - 1], prior_window[i]
                if any(prev.get(f'ema_{p}') is None or curr.get(f'ema_{p}') is None for p in [50, 200]):
                    continue
                prev_50, prev_200 = float(prev['ema_50']), float(prev['ema_200'])
                curr_50, curr_200 = float(curr['ema_50']), float(curr['ema_200'])
                crossed = (prev_50 <= prev_200 and curr_50 > curr_200) or (prev_50 >= prev_200 and curr_50 < curr_200)
                if crossed:
                    prior_cross_count += 1
            trend_quality_score = _trend_quality_score(prior_cross_count)

            # 5. Long-Term Trend Slope — EMA200 over the trailing 20 days before the cross
            slope_index = max(0, cross_index - 20)
            ema_200_then = merged_data[slope_index].get('ema_200')
            if ema_200_then is not None and float(ema_200_then) > 0:
                raw_slope_pct = (ema_200 - float(ema_200_then)) / float(ema_200_then) * 100
                slope_pct = raw_slope_pct if is_golden else -raw_slope_pct
            else:
                slope_pct = 0.0
            long_term_slope_score = _long_term_slope_score(slope_pct)

            beauty_score = (
                crossover_strength_score * 0.20 +
                volume_confirmation_score * 0.20 +
                momentum_continuation_score * 0.25 +
                trend_quality_score * 0.20 +
                long_term_slope_score * 0.15
            )
            beauty_score = round(max(0.0, min(100.0, beauty_score)), 1)

            result = {
                'beauty_score': beauty_score,
                'crossover_strength_score': round(crossover_strength_score, 1),
                'volume_confirmation_score': round(volume_confirmation_score, 1),
                'momentum_continuation_score': round(momentum_continuation_score, 1),
                'trend_quality_score': round(trend_quality_score, 1),
                'long_term_slope_score': round(long_term_slope_score, 1),
                'prior_cross_count_90d': prior_cross_count,
                'grade': _get_beauty_grade(beauty_score),
                'model_name': 'cross_model',
                'model_version': '1.0',
            }

            logger.info(
                f"Cross beauty score for {cross_info['signal']} on {cross_info['date']}: "
                f"{beauty_score} ({result['grade']}) — crossover={crossover_strength_score:.1f}, "
                f"volume={volume_confirmation_score:.1f}, momentum={momentum_continuation_score:.1f}, "
                f"trend_quality={trend_quality_score:.1f} (prior_crosses_90d={prior_cross_count}), "
                f"slope={long_term_slope_score:.1f}"
            )

            return result

        except Exception as e:
            logger.error(f"Error calculating cross beauty score: {str(e)}")
            return {'beauty_score': 0, 'reason': f'Error: {str(e)}'}


# Backward compatibility: keep the function for existing code
def detect_golden_cross(moving_averages: List[Dict], scan_days: int = 30) -> Dict:
    """
    Detect golden cross or death cross from moving averages (backward compatibility function)
    
    Args:
        moving_averages: List of MA records sorted by date
        scan_days: Number of recent days to scan (default: 30)
        
    Returns:
        dict with most recent cross info or None
    """
    # Create a temporary detector instance for backward compatibility
    detector = CrossDetector("temp", None)
    return detector.detect_golden_cross(moving_averages, scan_days)