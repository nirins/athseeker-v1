"""
Calibrated Beauty Score Model (v2.0)

A trainable beauty score model that uses machine learning calibrated weights
based on manually labeled training data.
"""

from typing import Dict, List, Any
import json
import os
from .original_model import OriginalBeautyModel

class CalibratedBeautyModel(OriginalBeautyModel):
    """Calibrated beauty score model with ML-optimized weights"""
    
    def __init__(self, weights_file: str = None):
        super().__init__()
        self.model_name = "calibrated"
        self.version = "2.0"
        self.weights_file = weights_file or self._get_default_weights_file()
        
        # Load calibrated weights if available
        self._load_calibrated_weights()
    
    def _get_default_weights_file(self) -> str:
        """Get default path for calibrated weights file"""
        # Look for weights file in scripts directory
        script_dir = os.path.join(os.path.dirname(__file__), '../../scripts')
        return os.path.join(script_dir, 'calibrated_weights.json')
    
    def _load_calibrated_weights(self):
        """Load calibrated weights from file if available"""
        try:
            if os.path.exists(self.weights_file):
                with open(self.weights_file, 'r') as f:
                    calibration_data = json.load(f)
                
                # Extract optimized weights
                if 'optimized_weights' in calibration_data:
                    optimized_weights = calibration_data['optimized_weights']
                    
                    # Update weights with calibrated values
                    self.weights.update({
                        'consolidation': optimized_weights.get('consolidation', self.weights['consolidation']),
                        'volume': optimized_weights.get('volume', self.weights['volume']),
                        'momentum': optimized_weights.get('momentum', self.weights['momentum']),
                        'green_candle': optimized_weights.get('green_candle', self.weights['green_candle']),
                        'gap': optimized_weights.get('gap', self.weights['gap'])
                    })
                    
                    # Store calibration metadata
                    self.calibration_info = {
                        'calibration_date': calibration_data.get('calibration_date'),
                        'training_samples': calibration_data.get('training_samples', 0),
                        'model_r2': calibration_data.get('model_r2', 0),
                        'improvement': calibration_data.get('improvement', 0)
                    }
                    
                    self.logger.info(f"Loaded calibrated weights from {self.weights_file}")
                    self.logger.info(f"Model R²: {self.calibration_info.get('model_r2', 'unknown')}")
                else:
                    self.logger.warning("No optimized weights found in calibration file")
            else:
                self.logger.info(f"No calibration file found at {self.weights_file}, using original weights")
                self.calibration_info = None
                
        except Exception as e:
            self.logger.error(f"Error loading calibrated weights: {str(e)}")
            self.calibration_info = None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get calibrated model information"""
        info = {
            'name': self.model_name,
            'version': self.version,
            'description': 'ML-calibrated beauty score model with optimized weights',
            'weights': self.weights.copy(),
            'components': [
                'consolidation_score',
                'volume_score', 
                'momentum_score',
                'green_candle_score',
                'gap_score'
            ],
            'is_trainable': True,
            'weights_file': self.weights_file
        }
        
        # Add calibration information if available
        if hasattr(self, 'calibration_info') and self.calibration_info:
            info['calibration'] = self.calibration_info.copy()
        
        return info
    
    def update_weights(self, new_weights: Dict[str, float], calibration_metadata: Dict = None):
        """Update model weights with new calibrated values"""
        try:
            # Validate weights sum to approximately 1.0
            weight_sum = sum(new_weights.values())
            if abs(weight_sum - 1.0) > 0.01:
                self.logger.warning(f"Weights sum to {weight_sum:.3f}, not 1.0")
            
            # Update weights
            self.weights.update(new_weights)
            
            # Update calibration info
            if calibration_metadata:
                self.calibration_info = calibration_metadata
            
            # Save to file
            self._save_calibrated_weights()
            
            self.logger.info("Successfully updated calibrated weights")
            
        except Exception as e:
            self.logger.error(f"Error updating weights: {str(e)}")
            raise
    
    def _save_calibrated_weights(self):
        """Save current weights and calibration info to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.weights_file), exist_ok=True)
            
            # Prepare data to save
            save_data = {
                'model_name': self.model_name,
                'model_version': self.version,
                'optimized_weights': self.weights.copy(),
                'calibration_date': self.calibration_info.get('calibration_date') if self.calibration_info else None,
                'training_samples': self.calibration_info.get('training_samples') if self.calibration_info else 0,
                'model_r2': self.calibration_info.get('model_r2') if self.calibration_info else 0,
                'improvement': self.calibration_info.get('improvement') if self.calibration_info else 0
            }
            
            # Save to file
            with open(self.weights_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            self.logger.info(f"Saved calibrated weights to {self.weights_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving calibrated weights: {str(e)}")
            raise