"""
Near All-Time High (Near ATH) detection module
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()


class NearATHDetector:
    """Handles Near ATH detection for all stocks"""

    def __init__(self, environment: str, max_daily_volatility: float = 100.0, near_ath_threshold: float = 7.0):
        self.environment = environment
        self.max_daily_volatility = max_daily_volatility
        self.near_ath_threshold = near_ath_threshold

    def check_near_ath_detection(self, symbol: str, market_code: str, price_data: List[Dict], moving_averages: List[Dict] = None) -> Optional[Dict]:
        """
        Check if symbol is near its all-time high.

        Rules:
        1. Reject if any day has daily volatility > max_daily_volatility
        2. ATH must be older than 180 days
        3. No day in the recent 180 days may be >= ATH (no recent breakout)
        4. Most recent close price must be within near_ath_threshold% below ATH
        5. Today's price must be above EMA7, EMA30, EMA50, and EMA200

        Returns Near ATH detection record or None.
        """
        try:
            if not price_data or len(price_data) < 2:
                return None

            # Rule 1: Reject stocks with excessive daily volatility
            for record in price_data:
                low = float(record['low'])
                if low > 0:
                    volatility = ((float(record['high']) - low) / low) * 100
                    if volatility > self.max_daily_volatility:
                        logger.info(f"Rejecting {symbol}: excessive volatility {volatility:.1f}% on {record['date']}")
                        return None

            # Single pass: find ATH (using high price) and historical min (using close)
            all_time_high = 0.0
            ath_date = None
            historical_min = float('inf')

            for record in price_data:
                historical_min = min(historical_min, float(record['close']))
                high = float(record['high'])
                if high > all_time_high:
                    all_time_high = high
                    ath_date = record['date']

            if all_time_high == 0.0 or ath_date is None:
                return None

            # Rule 2: ATH must be older than 180 days
            days_since_ath = (datetime.now() - datetime.strptime(ath_date, '%Y-%m-%d')).days
            if days_since_ath < 180:
                logger.info(f"Skipping {symbol}: ATH set {days_since_ath} days ago (must be > 180)")
                return None

            # Rule 3: No day in the recent 180 days may be >= ATH (no recent breakout)
            cutoff_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            recent_max = max((float(r['high']) for r in price_data if r['date'] >= cutoff_date), default=0.0)
            if recent_max >= all_time_high:
                logger.info(f"Skipping {symbol}: recent 180-day high {recent_max:.2f} >= ATH {all_time_high:.2f}")
                return None

            # Rule 4: Most recent close must be within near_ath_threshold% below ATH
            last_record = price_data[-1]
            current_price = float(last_record['close'])
            near_ath_floor = all_time_high * (1 - self.near_ath_threshold / 100)

            if current_price < near_ath_floor or current_price >= all_time_high:
                logger.info(f"Skipping {symbol}: price {current_price:.2f} not in near-ATH range [{near_ath_floor:.2f}, {all_time_high:.2f})")
                return None

            # Rule 5: Today's price must be above EMA7, EMA30, EMA50, and EMA200
            if moving_averages:
                last_date = last_record['date']
                ema_record = next((r for r in reversed(moving_averages) if r['date'] == last_date), None)
                if ema_record:
                    for ema_field in ['ema_7', 'ema_30', 'ema_50', 'ema_200']:
                        ema_val = ema_record.get(ema_field)
                        if ema_val is not None and current_price < float(ema_val):
                            logger.info(f"Skipping {symbol}: price {current_price:.2f} below {ema_field} {float(ema_val):.2f}")
                            return None

            distance_from_ath = ((all_time_high - current_price) / all_time_high) * 100
            percentage_gain = ((current_price - historical_min) / historical_min) * 100

            return {
                'symbol': symbol,
                'detection_date': last_record['date'],
                'current_price': current_price,
                'ath_price': all_time_high,
                'ath_date': ath_date,
                'distance_from_ath_percentage': round(distance_from_ath, 2),
                'percentage_gain': round(percentage_gain, 2),
                'market_code': market_code,
                'detected_at': datetime.now().isoformat(),
                'ttl': int((datetime.now() + timedelta(days=2)).timestamp())
            }

        except Exception as e:
            logger.error(f"Error in Near ATH detection for {symbol}: {str(e)}")
            return None
