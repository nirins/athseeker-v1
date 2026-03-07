"""
Cross detection module for golden cross and death cross signals
"""

from typing import Dict, List
import logging

logger = logging.getLogger()


class CrossDetector:
    """Handles cross signal detection"""
    
    def __init__(self, environment: str):
        """
        Initialize Cross Detector
        
        Args:
            environment: Environment name (dev, uat, prod)
        """
        self.environment = environment
    
    def detect_golden_cross(self, moving_averages: List[Dict], scan_days: int = 30) -> Dict:
        """
        Detect golden cross or death cross from moving averages
        Returns the MOST RECENT cross within scan_days
        
        Args:
            moving_averages: List of MA records sorted by date
            scan_days: Number of recent days to scan (default: 30)
            
        Returns:
            dict with most recent cross info or None
        """
        if len(moving_averages) < 2:
            return None
        
        # Only scan the last N days for performance
        start_index = max(0, len(moving_averages) - scan_days)
        
        # Scan through recent data to find the most recent golden cross
        most_recent_cross = None
        
        for i in range(start_index + 1, len(moving_averages)):
            today = moving_averages[i]
            yesterday = moving_averages[i-1]
            
            # Check if both EMAs exist
            if (today['ema_50'] is None or today['ema_200'] is None or
                yesterday['ema_50'] is None or yesterday['ema_200'] is None):
                continue
            
            # Convert Decimal to float for comparison
            today_50 = float(today['ema_50'])
            today_200 = float(today['ema_200'])
            yesterday_50 = float(yesterday['ema_50'])
            yesterday_200 = float(yesterday['ema_200'])
            
            # Golden Cross: 50 crosses above 200
            if today_50 > today_200 and yesterday_50 <= yesterday_200:
                most_recent_cross = {
                    'signal': 'GOLDEN_CROSS',
                    'date': today['date'],
                    'ema_50': today_50,
                    'ema_200': today_200,
                    'crossover_strength': round(today_50 - today_200, 2)
                }
            
            # Death Cross: 50 crosses below 200 (bearish)
            elif today_50 < today_200 and yesterday_50 >= yesterday_200:
                most_recent_cross = {
                    'signal': 'DEATH_CROSS',
                    'date': today['date'],
                    'ema_50': today_50,
                    'ema_200': today_200,
                    'crossover_strength': round(today_200 - today_50, 2)
                }
        
        return most_recent_cross


# Backward compatibility: keep the function for existing code
def detect_golden_cross(moving_averages: List[Dict], scan_days: int = 30) -> Dict:
    """
    Detect golden cross or death cross from moving averages (backward compatibility function)
    
    Args:
        moving_averages: List of MA records sorted by date
        scan_days: Number of recent days to scan (default: 30)
        
    Returns:
        dict with most recent cross info or None
    """
    # Create a temporary detector instance for backward compatibility
    detector = CrossDetector("temp", None)
    return detector.detect_golden_cross(moving_averages, scan_days)