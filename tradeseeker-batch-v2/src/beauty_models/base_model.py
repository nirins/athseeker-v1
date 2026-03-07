"""
Base Beauty Score Model

Abstract base class for all beauty score calculation models.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class BaseBeautyModel(ABC):
    """Abstract base class for beauty score models"""
    
    def __init__(self, model_name: str, version: str):
        self.model_name = model_name
        self.version = version
        self.logger = logging.getLogger(f"{__name__}.{model_name}")
    
    @abstractmethod
    def calculate_beauty_score(self, pre_breakout: List[Dict], breakout_day: Dict, 
                             post_breakout: List[Dict]) -> Dict[str, Any]:
        """
        Calculate beauty score for a breakout pattern
        
        Args:
            pre_breakout: Price data before breakout
            breakout_day: Price data for breakout day
            post_breakout: Price data after breakout
            
        Returns:
            Dict containing beauty_score, component scores, and grade
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information and configuration
        
        Returns:
            Dict containing model metadata
        """
        pass
    
    def _get_beauty_grade(self, score: float) -> str:
        """Convert numeric score to letter grade (standard 5-grade system)"""
        if score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    
    def validate_input_data(self, pre_breakout: List[Dict], breakout_day: Dict, 
                           post_breakout: List[Dict]) -> bool:
        """Validate input data for beauty score calculation"""
        try:
            # Check if we have minimum required data
            if len(pre_breakout) < 5:
                self.logger.warning("Insufficient pre-breakout data")
                return False
            
            if not breakout_day:
                self.logger.warning("Missing breakout day data")
                return False
            
            if len(post_breakout) < 2:
                self.logger.warning("Insufficient post-breakout data")
                return False
            
            # Validate required fields in breakout day
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            for field in required_fields:
                if field not in breakout_day:
                    self.logger.warning(f"Missing required field: {field}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating input data: {str(e)}")
            return False