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

from divergence_detector import DivergenceDetector

logger = logging.getLogger()


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

            reversal_score = max(0, min(100, round((facts['rsi_2'] - facts['rsi_1']) * 5)))

            logger.info(
                f"Confirmed reversal detected for {symbol}: score={reversal_score}, "
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
                'days_since_low': facts['days_since_low'],
                'detected_at': datetime.now().isoformat(),
                'ttl': int((datetime.now() + timedelta(days=2)).timestamp()),
            }

        except Exception as e:
            logger.error(f"Error in confirmed reversal detection for {symbol}: {str(e)}")
            return None
