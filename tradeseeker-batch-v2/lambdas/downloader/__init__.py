"""
Stock Downloader Package

This package contains modules for downloading, processing, and storing stock price data.
"""

from .downloader import StockDownloader
from .technical_analysis import calculate_ema_series, calculate_candle_metrics
from .cross_detector import CrossDetector, detect_golden_cross
from .ath_detector import ATHDetector
from .storage import StorageManager
from .api_client import EODHDClient

__all__ = [
    'StockDownloader',
    'calculate_ema_series',
    'calculate_candle_metrics',
    'CrossDetector',
    'detect_golden_cross',
    'ATHDetector',
    'StorageManager',
    'EODHDClient'
]