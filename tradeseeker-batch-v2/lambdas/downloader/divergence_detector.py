"""
Bullish divergence detection module ("turning point at the bottom")

A bullish divergence: price makes a lower swing low, but RSI makes a higher
low at the same time — selling pressure is weakening even as price dips
further, a classic precursor to a reversal. Runs for every processed symbol,
independent of ATH/cross/speculative, same as speculative_detector.py.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from technical_analysis import calculate_rsi_series

logger = logging.getLogger()


def _rsi_gap_score(rsi_2: float, rsi_1: float) -> float:
    """
    Score the RSI(latest low) - RSI(prior low) gap (0-100).
    Shared with confirmed_reversal_detector.py, which carries forward the
    same underlying divergence-strength signal.
    """
    return max(0.0, min(100.0, (rsi_2 - rsi_1) * 6))


def _price_structure_score(price_2: float, price_1: float) -> float:
    """
    Score how meaningfully the second swing low undercut the first (0-100).
    A deeper new low with the same RSI gap is a more convincing divergence
    than a marginal undercut. price_2 < price_1 is guaranteed by the caller's
    structural gate, so decline_pct is always > 0.
    """
    if price_1 <= 0:
        return 50.0
    decline_pct = (price_1 - price_2) / price_1 * 100
    if decline_pct <= 0:
        return 20.0
    elif decline_pct < 2:
        return 20 + (decline_pct / 2) * 40
    elif decline_pct < 5:
        return 60 + ((decline_pct - 2) / 3) * 40
    else:
        return 100.0


def _recency_score(days_since_low: int) -> float:
    """
    Score how fresh the swing low is (0-100). Shared with
    confirmed_reversal_detector.py. Callers already gate on
    days_since_low <= max_days_since_low (20 by default).
    """
    if days_since_low <= 5:
        return 100.0
    elif days_since_low <= 12:
        return 70.0
    else:
        return 40.0


def _rsi_floor_score(rsi_2: float) -> float:
    """
    Score how oversold the latest low itself was (0-100) — lower RSI at the
    low means a more washed-out, stronger-setup bottom.
    """
    if rsi_2 <= 30:
        return 100.0
    elif rsi_2 >= 50:
        return 0.0
    else:
        return 100 - ((rsi_2 - 30) / 20) * 100


class DivergenceDetector:
    """Handles bullish price/RSI divergence detection for all stocks"""

    def __init__(
        self,
        environment: str,
        rsi_period: int = 14,
        swing_window: int = 3,
        lookback_days: int = 120,
        max_days_since_low: int = 20,
        min_rsi_gap: float = 3.0,
        max_rsi_at_low: float = 50.0,
    ):
        """
        Initialize Divergence Detector

        Args:
            environment: Environment name (dev, uat, prod)
            rsi_period: RSI lookback period (default: 14)
            swing_window: Bars on each side a swing low must be the minimum
                of, i.e. a fractal low (default: 3 — needs 3 confirmation
                bars after it, so it can't be today)
            lookback_days: How far back to search for the two most recent
                swing lows to compare (default: 120)
            max_days_since_low: The latest swing low must be within this many
                trading days of today — the bottom must be current, not
                stale (default: 20)
            min_rsi_gap: Minimum RSI(latest low) - RSI(prior low) to count as
                a meaningful divergence, not noise (default: 3.0 points)
            max_rsi_at_low: RSI at the latest low must be below this — still
                weak/recovering territory, not mid-rally noise (default: 50.0)
        """
        self.environment = environment
        self.rsi_period = rsi_period
        self.swing_window = swing_window
        self.lookback_days = lookback_days
        self.max_days_since_low = max_days_since_low
        self.min_rsi_gap = min_rsi_gap
        self.max_rsi_at_low = max_rsi_at_low

    def _find_swing_lows(self, price_data: List[Dict], rsi_series: List) -> List[int]:
        """
        Find fractal swing-low indices: price_data[i]['low'] is the minimum
        of the window [i - swing_window, i + swing_window], and RSI is
        available at that index.
        """
        swing_lows = []
        w = self.swing_window
        for i in range(w, len(price_data) - w):
            if rsi_series[i] is None:
                continue
            window = price_data[i - w:i + w + 1]
            low_i = float(price_data[i]['low'])
            if low_i <= min(float(r['low']) for r in window):
                swing_lows.append(i)
        return swing_lows

    def find_lower_low_higher_rsi(self, price_data: List[Dict]) -> Optional[Dict]:
        """
        Core structural check, shared with other detectors built on the same
        idea (e.g. confirmed_reversal_detector.py): do the two most recent
        swing lows show a genuinely lower price low with a meaningfully
        higher RSI low? This does NOT apply the "still weak" RSI ceiling or
        the recency gate — callers with different intent (e.g. a detector
        that specifically wants a *confirmed* bounce, which can push RSI
        past the ceiling) apply their own gates on top of these raw facts.

        Args:
            price_data: List of price records sorted by date

        Returns:
            Dict of the two swing lows' facts if the lower-low/higher-RSI
            structure holds, None otherwise (not enough history, fewer than
            two swing lows, or the structure doesn't hold)
        """
        if not price_data or len(price_data) < 120:
            return None

        rsi_series = calculate_rsi_series(price_data, self.rsi_period)

        # Restrict swing-low search to the trailing lookback window
        cutoff_date = (
            datetime.strptime(price_data[-1]['date'], '%Y-%m-%d') - timedelta(days=self.lookback_days)
        ).strftime('%Y-%m-%d')
        window_start = next(
            (i for i, r in enumerate(price_data) if r['date'] >= cutoff_date), 0
        )
        search_data = price_data[window_start:]
        search_rsi = rsi_series[window_start:]

        swing_low_offsets = self._find_swing_lows(search_data, search_rsi)
        if len(swing_low_offsets) < 2:
            return None

        # Two most recent swing lows within the lookback window
        i2 = swing_low_offsets[-1]
        i1 = swing_low_offsets[-2]

        low_2 = search_data[i2]
        low_1 = search_data[i1]
        rsi_2 = search_rsi[i2]
        rsi_1 = search_rsi[i1]

        price_2 = float(low_2['low'])
        price_1 = float(low_1['low'])

        if price_2 >= price_1:
            return None
        if rsi_2 < rsi_1 + self.min_rsi_gap:
            return None

        last_date = datetime.strptime(price_data[-1]['date'], '%Y-%m-%d')
        low_2_date = datetime.strptime(low_2['date'], '%Y-%m-%d')
        days_since_low = (last_date - low_2_date).days

        return {
            'current_price': float(price_data[-1]['close']),
            'current_date': price_data[-1]['date'],
            'price_2': price_2,
            'low_2_date': low_2['date'],
            'price_1': price_1,
            'low_1_date': low_1['date'],
            'rsi_2': rsi_2,
            'rsi_1': rsi_1,
            'days_since_low': days_since_low,
        }

    def check_divergence_detection(
        self, symbol: str, market_code: str, price_data: List[Dict]
    ) -> Optional[Dict]:
        """
        Check whether a symbol is showing a bullish price/RSI divergence.

        Args:
            symbol: Symbol with market code (e.g., AAPL.US)
            market_code: Market code
            price_data: List of price records sorted by date, each with
                date/open/high/low/close/volume

        Returns:
            Divergence detection record if flagged, None otherwise
        """
        try:
            facts = self.find_lower_low_higher_rsi(price_data)
            if facts is None:
                return None

            days_since_low = facts['days_since_low']
            price_2, price_1 = facts['price_2'], facts['price_1']
            rsi_2, rsi_1 = facts['rsi_2'], facts['rsi_1']
            low_2_date, low_1_date = facts['low_2_date'], facts['low_1_date']

            # Recency gate: the latest low must be current, not old news
            if days_since_low > self.max_days_since_low:
                logger.info(
                    f"Skipping {symbol}: latest swing low {days_since_low} days ago "
                    f"(must be <= {self.max_days_since_low})"
                )
                return None

            # Still weak/recovering territory, not mid-rally noise
            if rsi_2 >= self.max_rsi_at_low:
                return None

            rsi_gap_score = _rsi_gap_score(rsi_2, rsi_1)
            price_structure_score = _price_structure_score(price_2, price_1)
            recency_score = _recency_score(days_since_low)
            rsi_floor_score = _rsi_floor_score(rsi_2)

            divergence_score = round(
                rsi_gap_score * 0.40 +
                price_structure_score * 0.25 +
                recency_score * 0.20 +
                rsi_floor_score * 0.15
            )
            divergence_score = max(0, min(100, divergence_score))

            logger.info(
                f"Bullish divergence detected for {symbol}: score={divergence_score} "
                f"(rsi_gap={rsi_gap_score:.1f}, structure={price_structure_score:.1f}, "
                f"recency={recency_score:.1f}, rsi_floor={rsi_floor_score:.1f}), "
                f"low_2={price_2:.2f} ({low_2_date}, RSI={rsi_2:.1f}), "
                f"low_1={price_1:.2f} ({low_1_date}, RSI={rsi_1:.1f})"
            )

            return {
                'symbol': symbol,
                'market_code': market_code,
                'detection_date': price_data[-1]['date'],
                'current_price': round(facts['current_price'], 2),
                'low_price': round(price_2, 2),
                'low_date': low_2_date,
                'prior_low_price': round(price_1, 2),
                'prior_low_date': low_1_date,
                'rsi_at_low': round(rsi_2, 2),
                'prior_rsi_at_low': round(rsi_1, 2),
                'divergence_score': divergence_score,
                'rsi_gap_score': round(rsi_gap_score, 1),
                'price_structure_score': round(price_structure_score, 1),
                'recency_score': round(recency_score, 1),
                'rsi_floor_score': round(rsi_floor_score, 1),
                'days_since_low': days_since_low,
                'detected_at': datetime.now().isoformat(),
                'ttl': int((datetime.now() + timedelta(days=2)).timestamp()),
            }

        except Exception as e:
            logger.error(f"Error in divergence detection for {symbol}: {str(e)}")
            return None
