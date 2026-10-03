"""
Unit tests for bullish price/RSI divergence detector
"""

import os
import importlib.util
import pytest
from datetime import datetime, timedelta

# Load divergence_detector.py + technical_analysis.py directly by file path
# rather than mutating sys.path (see test_speculative_detector.py for why:
# several lambdas share module names, e.g. handler.py, and sys.path.insert
# here can shadow the wrong one for other test files in the same session).
_DOWNLOADER_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'downloader')


def _load(module_name, file_name):
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(_DOWNLOADER_DIR, file_name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_technical_analysis = _load('technical_analysis', 'technical_analysis.py')
__import__('sys').modules['technical_analysis'] = _technical_analysis  # divergence_detector imports it by name
_divergence_detector = _load('divergence_detector', 'divergence_detector.py')

DivergenceDetector = _divergence_detector.DivergenceDetector
calculate_rsi_series = _technical_analysis.calculate_rsi_series


def _make_series(days: int = 122):
    """
    Builds a price series with a genuine bullish divergence:
    - a steep decline to a first trough (~day 40, strong downward momentum -> low RSI)
    - a recovery bounce
    - a much gentler decline to a lower second trough (~day 100-105, weaker
      downward momentum despite the lower price -> higher RSI)
    - a short tail of confirmation/recency bars
    """
    price_data = []
    start = datetime(2024, 1, 1)

    def add(day_idx, price):
        date = (start + timedelta(days=day_idx)).strftime('%Y-%m-%d')
        price_data.append({
            'date': date,
            'open': price,
            'high': price + 1.0,
            'low': price - 0.5,
            'close': price,
            'volume': 1000.0,
        })

    # Warm-up: slow drift so RSI has real (non-degenerate) gain/loss history
    for i in range(15):
        add(i, 100 + (i % 3) * 0.5)

    # Steep decline: 100 -> 55 over 25 days (trough 1 around day 40)
    for i in range(15, 41):
        t = (i - 15) / (41 - 15)
        add(i, 100 - t * 45)

    # Recovery bounce: 55 -> 95 over 24 days
    for i in range(41, 65):
        t = (i - 41) / (65 - 41)
        add(i, 55 + t * 40)

    # Gentle decline: 95 -> 48 over ~40 days (trough 2, lower than trough 1 but far gentler)
    for i in range(65, 105):
        t = (i - 65) / (105 - 65 - 1)
        add(i, 95 - t * 47)

    # Tail: monotonic recovery off the day-104 low (confirmation bars + recency
    # window). Must be strictly increasing — a flat/tied tail creates repeated
    # "swing lows" at the same price, which would out-rank the real trough as
    # the "two most recent" and make the price_2 < price_1 check fail.
    for i in range(105, days):
        add(i, 48 + (i - 104) * 0.15)

    return price_data


class TestDivergenceDetector:
    """Test cases for bullish price/RSI divergence detection"""

    def setup_method(self):
        self.detector = DivergenceDetector('test')

    def test_divergence_detected_on_lower_low_higher_rsi(self):
        """A steep-then-gentle double decline should flag a bullish divergence"""
        price_data = _make_series()

        result = self.detector.check_divergence_detection('AAPL.US', 'US', price_data)

        assert result is not None, "Expected a divergence to be detected"
        assert result['symbol'] == 'AAPL.US'
        assert result['market_code'] == 'US'
        assert result['low_price'] < result['prior_low_price'], "Second low must be lower"
        assert result['rsi_at_low'] > result['prior_rsi_at_low'], "RSI at second low must be higher"
        assert result['divergence_score'] >= 0
        assert result['divergence_score'] <= 100
        assert result['days_since_low'] <= 20

    def test_no_divergence_on_steady_uptrend(self):
        """A clean, steady uptrend has no swing lows worth comparing -> no detection"""
        price_data = []
        start = datetime(2024, 1, 1)
        for i in range(130):
            date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            price = 100 + i * 0.3
            price_data.append({
                'date': date, 'open': price, 'high': price + 1,
                'low': price - 0.3, 'close': price, 'volume': 1000.0
            })

        result = self.detector.check_divergence_detection('AAPL.US', 'US', price_data)

        assert result is None

    def test_no_detection_when_low_is_stale(self):
        """A genuine divergence pattern that happened too long ago should not fire"""
        price_data = _make_series(days=160)
        # Append 40 more flat days after the pattern, pushing the second low
        # well outside the default 20-day recency window.
        start = datetime(2024, 1, 1)
        last_price = price_data[-1]['close']
        for i in range(160, 200):
            date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            price_data.append({
                'date': date, 'open': last_price, 'high': last_price + 1,
                'low': last_price - 0.3, 'close': last_price, 'volume': 1000.0
            })

        result = self.detector.check_divergence_detection('AAPL.US', 'US', price_data)

        assert result is None

    def test_insufficient_data(self):
        """Fewer than 120 records is not enough for a reliable divergence check"""
        price_data = _make_series(days=60)

        result = self.detector.check_divergence_detection('AAPL.US', 'US', price_data)

        assert result is None

    def test_custom_thresholds_stricter_gap_blocks_detection(self):
        """A much larger min_rsi_gap should block a divergence that otherwise fires"""
        price_data = _make_series()
        loose_detector = DivergenceDetector('test', min_rsi_gap=3.0)
        strict_detector = DivergenceDetector('test', min_rsi_gap=80.0)

        loose_result = loose_detector.check_divergence_detection('AAPL.US', 'US', price_data)
        strict_result = strict_detector.check_divergence_detection('AAPL.US', 'US', price_data)

        assert loose_result is not None
        assert strict_result is None
