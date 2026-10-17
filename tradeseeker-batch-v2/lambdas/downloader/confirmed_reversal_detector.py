"""
Confirmed reversal detection module ("CR")

A bullish divergence tells you a bottom *might* be forming. This detector
adds the missing piece: has price actually started bouncing off that low
yet? Most divergence candidates are structurally valid but still flat or
dipping further — a confirmed reversal has already recovered meaningfully
off the swing low, the difference between "might turn" and "is turning".

Built on top of DivergenceDetector.find_lower_low_higher_rsi() (reused, not
duplicated) but deliberately does NOT apply divergence's RSI ceiling: a
stock bouncing hard enough can push RSI back above 50, and that's exactly
the case we want to keep, not drop.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from divergence_detector import DivergenceDetector, _rsi_gap_score, _recency_score

logger = logging.getLogger()


def _bounce_strength_score(bounce_pct: float) -> float:
    """
    Score how far price has already recovered off the swing low (0-100).
    Callers gate on bounce_pct >= min_bounce_pct (5.0 by default), so the
    ramp starts there.
    """
    if bounce_pct <= 5:
        return 40.0
    elif bounce_pct >= 15:
        return 100.0
    else:
        return 40 + ((bounce_pct - 5) / 10) * 60


def _bounce_volume_score(price_data: List[Dict], low_date: str) -> float:
    """
    Score volume during the bounce (low_date through the latest record)
    against the trailing-30-trading-day average volume *before* the low —
    confirms the bounce is real buying, not a low-volume drift up.
    Same curve shape as original_model.py's volume score.
    """
    low_index = next((i for i, r in enumerate(price_data) if r['date'] == low_date), None)
    if low_index is None or low_index < 5:
        return 50.0

    baseline_window = price_data[max(0, low_index - 30):low_index]
    baseline_volumes = [float(r.get('volume', 0)) for r in baseline_window]
    avg_baseline_volume = sum(baseline_volumes) / len(baseline_volumes) if baseline_volumes else 0.0
    if avg_baseline_volume <= 0:
        return 50.0

    bounce_window = price_data[low_index:]
    bounce_volumes = [float(r.get('volume', 0)) for r in bounce_window]
    avg_bounce_volume = sum(bounce_volumes) / len(bounce_volumes) if bounce_volumes else 0.0

    volume_ratio = avg_bounce_volume / avg_baseline_volume

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


class ConfirmedReversalDetector:
    """Handles confirmed-reversal detection for all stocks"""

    def __init__(
        self,
        environment: str,
        min_bounce_pct: float = 5.0,
        max_days_since_low: int = 20,
        divergence_detector: DivergenceDetector = None,
    ):
        """
        Initialize Confirmed Reversal Detector

        Args:
            environment: Environment name (dev, uat, prod)
            min_bounce_pct: Minimum (current_price - low_price) / low_price
                to count as an already-confirmed bounce off the swing low,
                not just a structural divergence signal (default: 5.0%)
            max_days_since_low: The swing low must be within this many
                trading days of today (default: 20, matches DivergenceDetector)
            divergence_detector: Optional shared DivergenceDetector instance
                (reuses its swing-low logic rather than duplicating it); a
                new one is created if not provided
        """
        self.environment = environment
        self.min_bounce_pct = min_bounce_pct
        self.max_days_since_low = max_days_since_low
        self._divergence_detector = divergence_detector or DivergenceDetector(environment)

    def check_confirmed_reversal_detection(
        self, symbol: str, market_code: str, price_data: List[Dict]
    ) -> Optional[Dict]:
        """
        Check whether a symbol has a bullish divergence AND has already
        bounced meaningfully off the swing low.

        Args:
            symbol: Symbol with market code (e.g., AAPL.US)
            market_code: Market code
            price_data: List of price records sorted by date

        Returns:
            Confirmed reversal detection record if flagged, None otherwise
        """
        try:
            facts = self._divergence_detector.find_lower_low_higher_rsi(price_data)
            if facts is None:
                return None

            if facts['days_since_low'] > self.max_days_since_low:
                return None

            price_2 = facts['price_2']
            current_price = facts['current_price']
            bounce_pct = ((current_price - price_2) / price_2) * 100 if price_2 > 0 else 0.0

            if bounce_pct < self.min_bounce_pct:
                return None

            bounce_strength = _bounce_strength_score(bounce_pct)
            rsi_gap = _rsi_gap_score(facts['rsi_2'], facts['rsi_1'])
            recency = _recency_score(facts['days_since_low'])
            bounce_volume = _bounce_volume_score(price_data, facts['low_2_date'])

            reversal_score = round(
                bounce_strength * 0.35 +
                rsi_gap * 0.25 +
                recency * 0.20 +
                bounce_volume * 0.20
            )
            reversal_score = max(0, min(100, reversal_score))

            logger.info(
                f"Confirmed reversal detected for {symbol}: score={reversal_score} "
                f"(bounce_strength={bounce_strength:.1f}, rsi_gap={rsi_gap:.1f}, "
                f"recency={recency:.1f}, bounce_volume={bounce_volume:.1f}), "
                f"bounce={bounce_pct:.1f}% off low {price_2:.2f} ({facts['low_2_date']})"
            )

            return {
                'symbol': symbol,
                'market_code': market_code,
                'detection_date': facts['current_date'],
                'current_price': round(current_price, 2),
                'low_price': round(price_2, 2),
                'low_date': facts['low_2_date'],
                'prior_low_price': round(facts['price_1'], 2),
                'prior_low_date': facts['low_1_date'],
                'rsi_at_low': round(facts['rsi_2'], 2),
                'prior_rsi_at_low': round(facts['rsi_1'], 2),
                'bounce_pct': round(bounce_pct, 2),
                'confirmed_reversal_score': reversal_score,
                'bounce_strength_score': round(bounce_strength, 1),
                'rsi_gap_score': round(rsi_gap, 1),
                'recency_score': round(recency, 1),
                'bounce_volume_score': round(bounce_volume, 1),
                'days_since_low': facts['days_since_low'],
                'detected_at': datetime.now().isoformat(),
                'ttl': int((datetime.now() + timedelta(days=2)).timestamp()),
            }

        except Exception as e:
            logger.error(f"Error in confirmed reversal detection for {symbol}: {str(e)}")
            return None
