"""
Speculative stock detection module

Flags stocks showing signs of speculative/risky trading activity — an
outsized volume spike, a violent single-day swing, a sharp red candle, or a
parabolic short-term run-up — independent of whether the stock also happens
to be at an ATH or crossing an EMA. Unlike ATH/near-ATH/cross, this runs for
every processed symbol.

All signals are percentage/ratio-based rather than absolute price
thresholds, since markets span very different currency scales (THB, HKD,
CNY, KRW, TWD, USD, ...).
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()


def _ramp(value: float, low: float, high: float, max_pts: float = 25.0) -> float:
    """Linear 0->max_pts ramp between [low, high], clamped outside it."""
    if value <= low:
        return 0.0
    if value >= high:
        return max_pts
    return (value - low) / (high - low) * max_pts


def _get_risk_tier(risk_score: float) -> str:
    """
    Convert the numeric risk score to a caution tier.

    Deliberately NOT the A-F beauty grade used elsewhere: a high speculative
    score means more caution is warranted, not a better opportunity, so
    reusing "Grade A" here would read as a recommendation instead of a
    warning. See .local/design/beauty-score-remaining-strategies.md.
    """
    if risk_score >= 85:
        return 'Extreme'
    elif risk_score >= 65:
        return 'High'
    elif risk_score >= 50:
        return 'Moderate'
    else:
        return 'Low'


class SpeculativeDetector:
    """Handles speculative-activity detection for all stocks"""

    def __init__(
        self,
        environment: str,
        volume_spike_threshold: float = 3.0,
        volatility_threshold: float = 30.0,
        red_candle_threshold: float = -15.0,
        run_up_threshold: float = 30.0,
    ):
        """
        Initialize Speculative Detector

        Args:
            environment: Environment name (dev, uat, prod)
            volume_spike_threshold: Latest volume / trailing 30d avg volume ratio
                that counts as a spike (default: 3.0x)
            volatility_threshold: Max single-day (high-low)/low %% over the
                trailing 10 days that counts as a volatility spike (default: 30%%)
            red_candle_threshold: max_red_candle_30d_pct at or below this counts
                as a severe red candle (default: -15%%)
            run_up_threshold: Cumulative %% return over the trailing 10 trading
                days that counts as a parabolic run-up (default: 30%%)
        """
        self.environment = environment
        self.volume_spike_threshold = volume_spike_threshold
        self.volatility_threshold = volatility_threshold
        self.red_candle_threshold = red_candle_threshold
        self.run_up_threshold = run_up_threshold

    def check_speculative_detection(
        self,
        symbol: str,
        market_code: str,
        price_data: List[Dict],
        candle_metrics: Dict = None,
    ) -> Optional[Dict]:
        """
        Check whether a symbol is showing speculative trading activity.

        Composite of 4 independent signals, each worth 25 points:
        - volume spike (latest volume vs trailing 30d average)
        - recent volatility spike (max daily high/low swing over 10d)
        - severe red candle in the trailing 30d (from candle_metrics)
        - parabolic run-up (cumulative return over 10d)

        Flagged as speculative when at least 2 of the 4 signals trigger
        (speculative_score >= 50), to avoid over-flagging a single
        earnings-day pop.

        Args:
            symbol: Symbol with market code (e.g., AAPL.US)
            market_code: Market code
            price_data: List of price records sorted by date, each with
                date/open/high/low/close/volume
            candle_metrics: Optional dict from calculate_candle_metrics(),
                used for the red-candle signal. Skipped if not provided.

        Returns:
            Speculative detection record if flagged, None otherwise
        """
        try:
            if not price_data or len(price_data) < 11:
                return None

            reasons: List[str] = []

            last_record = price_data[-1]
            latest_volume = float(last_record.get('volume', 0))

            # Signal 1: volume spike vs trailing 30d average (excluding latest day)
            volume_window = price_data[-31:-1] if len(price_data) >= 31 else price_data[:-1]
            volumes = [float(r.get('volume', 0)) for r in volume_window]
            avg_volume_30d = sum(volumes) / len(volumes) if volumes else 0.0

            volume_spike_ratio = (latest_volume / avg_volume_30d) if avg_volume_30d > 0 else 0.0
            if volume_spike_ratio >= self.volume_spike_threshold:
                reasons.append('volume_spike')

            # Signal 2: recent volatility spike — max single-day swing over trailing 10d
            recent_window = price_data[-10:]
            recent_volatility_pct = 0.0
            for record in recent_window:
                low = float(record['low'])
                if low > 0:
                    swing = ((float(record['high']) - low) / low) * 100
                    recent_volatility_pct = max(recent_volatility_pct, swing)
            if recent_volatility_pct >= self.volatility_threshold:
                reasons.append('volatility_spike')

            # Signal 3: severe red candle in the trailing 30d
            max_red_candle_30d_pct = None
            if candle_metrics and candle_metrics.get('max_red_candle_pct') is not None:
                max_red_candle_30d_pct = float(candle_metrics['max_red_candle_pct'])
                if max_red_candle_30d_pct <= self.red_candle_threshold:
                    reasons.append('severe_red_candle')

            # Signal 4: parabolic run-up over trailing 10 trading days
            close_now = float(last_record['close'])
            close_10d_ago = float(price_data[-11]['close'])
            cumulative_return_10d_pct = (
                ((close_now - close_10d_ago) / close_10d_ago) * 100 if close_10d_ago > 0 else 0.0
            )
            if cumulative_return_10d_pct >= self.run_up_threshold:
                reasons.append('parabolic_run_up')

            # Gate on flag count, same as before (2-of-4) — this decides WHICH
            # stocks get flagged, and stays unchanged so the detected
            # population doesn't silently shift. The continuous score below
            # is a separate, magnitude-aware severity measure used for
            # ranking/sorting flagged stocks, not for the gate itself.
            if len(reasons) < 2:
                return None

            # Continuous 0-25-per-signal risk score: a 3.1x volume spike and
            # a 10x spike no longer score identically the way the old
            # 25-points-per-flag formula did.
            volume_spike_pts = _ramp(volume_spike_ratio, self.volume_spike_threshold, self.volume_spike_threshold * 2)
            volatility_pts = _ramp(recent_volatility_pct, self.volatility_threshold, self.volatility_threshold * 2)
            red_candle_pts = (
                _ramp(-max_red_candle_30d_pct, -self.red_candle_threshold, -self.red_candle_threshold * 2.67)
                if max_red_candle_30d_pct is not None else 0.0
            )
            run_up_pts = _ramp(cumulative_return_10d_pct, self.run_up_threshold, self.run_up_threshold * 2.67)

            speculative_score = round(volume_spike_pts + volatility_pts + red_candle_pts + run_up_pts)
            speculative_score = max(0, min(100, speculative_score))
            risk_tier = _get_risk_tier(speculative_score)

            logger.info(
                f"Speculative activity detected for {symbol}: risk_score={speculative_score} ({risk_tier}), "
                f"reasons={reasons}, volume_spike_ratio={volume_spike_ratio:.2f}, "
                f"recent_volatility_pct={recent_volatility_pct:.2f}, "
                f"cumulative_return_10d_pct={cumulative_return_10d_pct:.2f}"
            )

            return {
                'symbol': symbol,
                'market_code': market_code,
                'detection_date': last_record['date'],
                'current_price': round(close_now, 2),
                'speculative_score': speculative_score,
                'risk_tier': risk_tier,
                'volume_spike_ratio': round(volume_spike_ratio, 2),
                'recent_volatility_pct': round(recent_volatility_pct, 2),
                'cumulative_return_10d_pct': round(cumulative_return_10d_pct, 2),
                'max_red_candle_30d_pct': (
                    round(max_red_candle_30d_pct, 2) if max_red_candle_30d_pct is not None else None
                ),
                'reasons': reasons,
                'detected_at': datetime.now().isoformat(),
                'ttl': int((datetime.now() + timedelta(days=2)).timestamp()),
            }

        except Exception as e:
            logger.error(f"Error in speculative detection for {symbol}: {str(e)}")
            return None
