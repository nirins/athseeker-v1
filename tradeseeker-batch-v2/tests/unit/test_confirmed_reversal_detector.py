"""
Unit tests for Confirmed Reversal detector ("CR")
"""

import os
import importlib.util
import pytest
from datetime import datetime, timedelta

_DOWNLOADER_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'downloader')


def _load(module_name, file_name):
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(_DOWNLOADER_DIR, file_name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_technical_analysis = _load('technical_analysis', 'technical_analysis.py')
import sys as _sys
_sys.modules['technical_analysis'] = _technical_analysis
_divergence_detector = _load('divergence_detector', 'divergence_detector.py')
_sys.modules['divergence_detector'] = _divergence_detector
_confirmed_reversal_detector = _load('confirmed_reversal_detector', 'confirmed_reversal_detector.py')

DivergenceDetector = _divergence_detector.DivergenceDetector
ConfirmedReversalDetector = _confirmed_reversal_detector.ConfirmedReversalDetector


def _make_series(days: int = 122, tail_slope: float = 0.15):
    """
    Same steep-decline -> bounce -> gentle-lower-decline shape as
    test_divergence_detector.py, with a configurable tail recovery slope so
    tests can dial the post-low bounce strength up or down independently of
    the divergence structure itself.
    """
    price_data = []
    start = datetime(2024, 1, 1)

    def add(day_idx, price):
        date = (start + timedelta(days=day_idx)).strftime('%Y-%m-%d')
        price_data.append({
            'date': date, 'open': price, 'high': price + 1.0,
            'low': price - 0.5, 'close': price, 'volume': 1000.0,
        })

    for i in range(15):
        add(i, 100 + (i % 3) * 0.5)
    for i in range(15, 41):
        t = (i - 15) / (41 - 15)
        add(i, 100 - t * 45)
    for i in range(41, 65):
        t = (i - 41) / (65 - 41)
        add(i, 55 + t * 40)
    for i in range(65, 105):
        t = (i - 65) / (105 - 65 - 1)
        add(i, 95 - t * 47)
    for i in range(105, days):
        add(i, 48 + (i - 104) * tail_slope)

    return price_data


class TestConfirmedReversalDetector:
    """Test cases for confirmed-reversal detection"""

    def setup_method(self):
        self.detector = ConfirmedReversalDetector('test')

    def test_confirmed_reversal_detected_on_strong_bounce(self):
        """A divergence with a meaningful bounce off the low should flag"""
        price_data = _make_series(tail_slope=0.15)

        result = self.detector.check_confirmed_reversal_detection('DOHOME.BK', 'BK', price_data)

        assert result is not None, "Expected a confirmed reversal to be detected"
        assert result['symbol'] == 'DOHOME.BK'
        assert result['market_code'] == 'BK'
        assert result['low_price'] < result['prior_low_price']
        assert result['rsi_at_low'] > result['prior_rsi_at_low']
        assert result['current_price'] > result['low_price']
        assert result['bounce_pct'] >= 5.0
        assert result['confirmed_reversal_score'] >= 0
        assert result['confirmed_reversal_score'] <= 100

    def test_structural_divergence_without_confirmed_bounce_not_flagged(self):
        """The same structural divergence, but price hasn't bounced enough yet"""
        price_data = _make_series(tail_slope=0.01)

        # Sanity check: the underlying divergence structure still holds —
        # only the bounce-confirmation gate should be the reason this fails.
        divergence_detector = DivergenceDetector('test')
        divergence_result = divergence_detector.check_divergence_detection('ITC.BK', 'BK', price_data)
        assert divergence_result is not None, "Test setup error: expected the base divergence to still hold"

        result = self.detector.check_confirmed_reversal_detection('ITC.BK', 'BK', price_data)

        assert result is None

    def test_no_detection_on_steady_uptrend(self):
        """No swing lows worth comparing -> no detection regardless of bounce"""
        price_data = []
        start = datetime(2024, 1, 1)
        for i in range(130):
            date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            price = 100 + i * 0.3
            price_data.append({
                'date': date, 'open': price, 'high': price + 1,
                'low': price - 0.3, 'close': price, 'volume': 1000.0
            })

        result = self.detector.check_confirmed_reversal_detection('AAPL.US', 'US', price_data)

        assert result is None

    def test_insufficient_data(self):
        """Fewer than 120 records is not enough for a reliable check"""
        price_data = _make_series(days=60)

        result = self.detector.check_confirmed_reversal_detection('AAPL.US', 'US', price_data)

        assert result is None

    def test_custom_bounce_threshold(self):
        """A stricter min_bounce_pct should block a reversal that otherwise fires"""
        price_data = _make_series(tail_slope=0.15)
        loose_detector = ConfirmedReversalDetector('test', min_bounce_pct=5.0)
        strict_detector = ConfirmedReversalDetector('test', min_bounce_pct=50.0)

        loose_result = loose_detector.check_confirmed_reversal_detection('DOHOME.BK', 'BK', price_data)
        strict_result = strict_detector.check_confirmed_reversal_detection('DOHOME.BK', 'BK', price_data)

        assert loose_result is not None
        assert strict_result is None

    def test_shares_divergence_detector_instance(self):
        """A caller-provided DivergenceDetector should be reused, not replaced"""
        shared = DivergenceDetector('test', min_rsi_gap=80.0)  # unreasonably strict
        detector = ConfirmedReversalDetector('test', divergence_detector=shared)
        price_data = _make_series(tail_slope=0.15)

        result = detector.check_confirmed_reversal_detection('DOHOME.BK', 'BK', price_data)

        # The shared detector's strict min_rsi_gap should block the structural
        # divergence entirely, proving it's actually being used.
        assert result is None
