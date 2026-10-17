"""
Unit tests for the golden/death cross beauty score
(cross_detector.CrossDetector.calculate_cross_beauty_score)
"""

import os
import importlib.util
from datetime import datetime, timedelta

_MODULE_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'lambdas', 'downloader', 'cross_detector.py'
)
_spec = importlib.util.spec_from_file_location('cross_detector', _MODULE_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
CrossDetector = _module.CrossDetector


def _make_merged_data(cross_index: int = 100, total_days: int = 110,
                       prior_cross_dates=None, post_momentum: bool = True):
    """
    Builds a merged price+EMA series with a clean golden cross at
    `cross_index`: EMA50 flat below EMA200 beforehand (no whipsaw unless
    `prior_cross_dates` injects extra crossings), separating cleanly above
    it at the cross, with EMA200 already drifting up over the trailing 20
    days and a volume spike on the cross day.
    """
    start = datetime(2024, 1, 1)
    data = []
    prior_cross_dates = prior_cross_dates or set()

    for i in range(total_days):
        date = (start + timedelta(days=i)).strftime('%Y-%m-%d')

        # EMA200 drifts gently upward throughout
        ema_200 = 95.0 + i * 0.05

        if i in prior_cross_dates:
            # Briefly flip EMA50 above EMA200 to simulate a whipsaw cross
            ema_50 = ema_200 + 1.0
        elif i < cross_index:
            ema_50 = ema_200 - 5.0  # below EMA200 throughout the pre-cross window
        elif i == cross_index:
            ema_50 = ema_200 + 5.0  # clean 5%+ separation right at the cross
        else:
            # After the cross: keep EMA50 above EMA200, rising if momentum continues
            if post_momentum:
                ema_50 = ema_200 + 5.0 + (i - cross_index) * 1.0
            else:
                ema_50 = ema_200 + 5.0

        close = 100.0
        if i >= cross_index and post_momentum:
            close = 100.0 * (1 + 0.02 * (i - cross_index))  # ~2%/day continuation

        volume = 5000.0 if i == cross_index else 1000.0

        data.append({
            'date': date,
            'open': close,
            'high': close + 1,
            'low': close - 1,
            'close': close,
            'volume': volume,
            'ema_7': ema_50,
            'ema_30': ema_50,
            'ema_50': ema_50,
            'ema_200': ema_200,
        })

    return data


class TestCrossBeautyScore:
    """Test cases for the golden/death cross beauty score"""

    def setup_method(self):
        self.detector = CrossDetector('test')

    def test_clean_golden_cross_scores_well(self):
        """A clean, well-confirmed golden cross with no recent whipsaw should score high"""
        merged_data = _make_merged_data(cross_index=100, total_days=110)
        cross_info = {
            'signal': 'GOLDEN_CROSS',
            'date': merged_data[100]['date'],
            'ema_50': merged_data[100]['ema_50'],
            'ema_200': merged_data[100]['ema_200'],
            'crossover_strength': merged_data[100]['ema_50'] - merged_data[100]['ema_200'],
        }

        result = self.detector.calculate_cross_beauty_score(merged_data, cross_info)

        assert 'beauty_score' in result
        assert 0 <= result['beauty_score'] <= 100
        assert result['beauty_score'] >= 70, f"Expected a strong score, got {result}"
        assert result['grade'] in {'A', 'B'}
        assert result['prior_cross_count_90d'] == 0

    def test_whipsaw_penalizes_trend_quality(self):
        """Recent crosses in the trailing 90 days should lower trend_quality_score and the overall score"""
        clean_data = _make_merged_data(cross_index=100, total_days=110)
        whipsaw_data = _make_merged_data(
            cross_index=100, total_days=110, prior_cross_dates={40, 41, 60, 61, 80, 81}
        )

        clean_info = {
            'signal': 'GOLDEN_CROSS', 'date': clean_data[100]['date'],
            'ema_50': clean_data[100]['ema_50'], 'ema_200': clean_data[100]['ema_200'],
            'crossover_strength': clean_data[100]['ema_50'] - clean_data[100]['ema_200'],
        }
        whipsaw_info = {
            'signal': 'GOLDEN_CROSS', 'date': whipsaw_data[100]['date'],
            'ema_50': whipsaw_data[100]['ema_50'], 'ema_200': whipsaw_data[100]['ema_200'],
            'crossover_strength': whipsaw_data[100]['ema_50'] - whipsaw_data[100]['ema_200'],
        }

        clean_result = self.detector.calculate_cross_beauty_score(clean_data, clean_info)
        whipsaw_result = self.detector.calculate_cross_beauty_score(whipsaw_data, whipsaw_info)

        assert whipsaw_result['prior_cross_count_90d'] > clean_result['prior_cross_count_90d']
        assert whipsaw_result['trend_quality_score'] < clean_result['trend_quality_score']
        assert whipsaw_result['beauty_score'] < clean_result['beauty_score']

    def test_weak_follow_through_scores_lower_than_strong(self):
        """No momentum continuation after the cross should score lower than a strong follow-through"""
        strong_data = _make_merged_data(cross_index=100, total_days=110, post_momentum=True)
        weak_data = _make_merged_data(cross_index=100, total_days=110, post_momentum=False)

        strong_info = {
            'signal': 'GOLDEN_CROSS', 'date': strong_data[100]['date'],
            'ema_50': strong_data[100]['ema_50'], 'ema_200': strong_data[100]['ema_200'],
            'crossover_strength': strong_data[100]['ema_50'] - strong_data[100]['ema_200'],
        }
        weak_info = {
            'signal': 'GOLDEN_CROSS', 'date': weak_data[100]['date'],
            'ema_50': weak_data[100]['ema_50'], 'ema_200': weak_data[100]['ema_200'],
            'crossover_strength': weak_data[100]['ema_50'] - weak_data[100]['ema_200'],
        }

        strong_result = self.detector.calculate_cross_beauty_score(strong_data, strong_info)
        weak_result = self.detector.calculate_cross_beauty_score(weak_data, weak_info)

        assert strong_result['momentum_continuation_score'] > weak_result['momentum_continuation_score']
        assert strong_result['beauty_score'] > weak_result['beauty_score']

    def test_death_cross_direction_is_mirrored(self):
        """A death cross should score well when price/EMAs follow through to the downside"""
        start = datetime(2024, 1, 1)
        data = []
        cross_index = 100
        for i in range(110):
            date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            ema_200 = 105.0 - i * 0.05  # drifting down
            if i < cross_index:
                ema_50 = ema_200 + 5.0
            elif i == cross_index:
                ema_50 = ema_200 - 5.0
            else:
                ema_50 = ema_200 - 5.0 - (i - cross_index) * 1.0

            close = 100.0 if i < cross_index else 100.0 * (1 - 0.02 * (i - cross_index))
            volume = 5000.0 if i == cross_index else 1000.0

            data.append({
                'date': date, 'open': close, 'high': close + 1, 'low': close - 1,
                'close': close, 'volume': volume,
                'ema_7': ema_50, 'ema_30': ema_50, 'ema_50': ema_50, 'ema_200': ema_200,
            })

        cross_info = {
            'signal': 'DEATH_CROSS', 'date': data[cross_index]['date'],
            'ema_50': data[cross_index]['ema_50'], 'ema_200': data[cross_index]['ema_200'],
            'crossover_strength': data[cross_index]['ema_200'] - data[cross_index]['ema_50'],
        }

        result = self.detector.calculate_cross_beauty_score(data, cross_info)

        assert result['beauty_score'] >= 70, f"Expected a strong death-cross confirmation score, got {result}"
        assert result['prior_cross_count_90d'] == 0

    def test_cross_date_not_found_returns_zero(self):
        """A cross date missing from merged_data should fail gracefully, not raise"""
        merged_data = _make_merged_data(cross_index=100, total_days=110)
        cross_info = {
            'signal': 'GOLDEN_CROSS', 'date': '1999-01-01',
            'ema_50': 100.0, 'ema_200': 95.0, 'crossover_strength': 5.0,
        }

        result = self.detector.calculate_cross_beauty_score(merged_data, cross_info)

        assert result['beauty_score'] == 0
        assert 'reason' in result
