"""
Unit tests for Speculative Activity detector
"""

import os
import importlib.util
import pytest
from datetime import datetime, timedelta

# Load speculative_detector.py directly by file path rather than mutating
# sys.path (as tests/test_downloader.py does): several lambdas share module
# names (e.g. downloader/handler.py vs task-generator/handler.py), and
# inserting lambdas/downloader onto sys.path here can shadow the wrong one
# for other test files collected later in the same pytest session.
_MODULE_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'lambdas', 'downloader', 'speculative_detector.py'
)
_spec = importlib.util.spec_from_file_location('speculative_detector', _MODULE_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
SpeculativeDetector = _module.SpeculativeDetector


def _make_baseline(days: int = 31):
    """
    31 quiet trading days: ~5% daily swing, flat close, steady volume.
    None of the four signals should trigger on this baseline.
    """
    price_data = []
    start = datetime(2024, 1, 1)
    for i in range(days):
        date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
        price_data.append({
            'date': date,
            'open': 100.0,
            'high': 103.0,
            'low': 98.0,
            'close': 101.0,
            'volume': 1000.0,
        })
    return price_data


class TestSpeculativeDetector:
    """Test cases for speculative-activity detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = SpeculativeDetector('test')

    def test_no_detection_on_quiet_stock(self):
        """A quiet, low-volatility stock should never be flagged"""
        price_data = _make_baseline()

        result = self.detector.check_speculative_detection('AAPL.US', 'US', price_data)

        assert result is None

    def test_single_signal_alone_does_not_trigger(self):
        """One signal (25 points) is below the 50-point (2-of-4) gate"""
        price_data = _make_baseline()
        price_data[-1]['volume'] = 5000.0  # 5x avg volume -> volume_spike only

        result = self.detector.check_speculative_detection('AAPL.US', 'US', price_data)

        assert result is None

    def test_volume_spike_plus_volatility_triggers(self):
        """Two independent signals (volume + volatility) should flag at score 50"""
        price_data = _make_baseline()
        price_data[-1]['volume'] = 5000.0  # ratio 5.0x >= 3.0 threshold
        price_data[-1]['high'] = 140.0
        price_data[-1]['low'] = 98.0  # swing 42.9% >= 30% threshold

        result = self.detector.check_speculative_detection('AAPL.US', 'US', price_data)

        assert result is not None
        assert result['symbol'] == 'AAPL.US'
        assert result['market_code'] == 'US'
        assert result['speculative_score'] == 50
        assert set(result['reasons']) == {'volume_spike', 'volatility_spike'}
        assert result['volume_spike_ratio'] == 5.0

    def test_red_candle_signal_from_candle_metrics(self):
        """Severe red candle (passed via candle_metrics) counts as a signal"""
        price_data = _make_baseline()
        price_data[-1]['volume'] = 5000.0  # second signal to cross the gate
        candle_metrics = {'max_red_candle_pct': -20.0}  # <= -15% threshold

        result = self.detector.check_speculative_detection('AAPL.US', 'US', price_data, candle_metrics)

        assert result is not None
        assert set(result['reasons']) == {'volume_spike', 'severe_red_candle'}
        assert result['max_red_candle_30d_pct'] == -20.0

    def test_parabolic_run_up_signal(self):
        """A >=50% run-up over 10 trading days counts as a signal"""
        price_data = _make_baseline()
        price_data[-11]['close'] = 60.0  # (101 - 60) / 60 = 68.3% >= 50% threshold
        price_data[-1]['volume'] = 5000.0  # second signal to cross the gate

        result = self.detector.check_speculative_detection('AAPL.US', 'US', price_data)

        assert result is not None
        assert 'parabolic_run_up' in result['reasons']
        assert result['cumulative_return_10d_pct'] > 50.0

    def test_all_four_signals_score_100(self):
        """All four signals firing together caps the score at 100"""
        price_data = _make_baseline()
        price_data[-1]['volume'] = 5000.0  # volume_spike
        price_data[-1]['high'] = 140.0
        price_data[-1]['low'] = 98.0  # volatility_spike
        price_data[-11]['close'] = 60.0  # parabolic_run_up
        candle_metrics = {'max_red_candle_pct': -20.0}  # severe_red_candle

        result = self.detector.check_speculative_detection('AAPL.US', 'US', price_data, candle_metrics)

        assert result is not None
        assert result['speculative_score'] == 100
        assert set(result['reasons']) == {
            'volume_spike', 'volatility_spike', 'parabolic_run_up', 'severe_red_candle'
        }

    def test_insufficient_data(self):
        """Fewer than 11 records is not enough for the 10-day windows"""
        price_data = _make_baseline(days=5)

        result = self.detector.check_speculative_detection('AAPL.US', 'US', price_data)

        assert result is None

    def test_custom_thresholds(self):
        """Custom, stricter thresholds should flag what the defaults would not"""
        detector = SpeculativeDetector(
            'test', volume_spike_threshold=1.5, volatility_threshold=10.0
        )
        price_data = _make_baseline()
        price_data[-1]['volume'] = 1600.0  # 1.6x avg, below default 3.0x but above custom 1.5x
        price_data[-1]['high'] = 108.0
        price_data[-1]['low'] = 98.0  # ~10.2% swing, below default 30% but above custom 10%

        result = detector.check_speculative_detection('AAPL.US', 'US', price_data)

        assert result is not None
        assert set(result['reasons']) == {'volume_spike', 'volatility_spike'}
