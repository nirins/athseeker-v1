"""
Beauty Model Factory

Factory class for creating and managing different beauty score models.
Provides model switching and configuration capabilities.
"""

from typing import Dict, Any, Optional
import os
import json
import logging
from .base_model import BaseBeautyModel
from .original_model import OriginalBeautyModel
from .calibrated_model import CalibratedBeautyModel

logger = logging.getLogger(__name__)

class BeautyModelFactory:
    """Factory for creating and managing beauty score models"""
    
    # Registry of available models
    _models = {
        'original': OriginalBeautyModel,
        'calibrated': CalibratedBeautyModel
    }
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or self._get_default_config_file()
        self.config = self._load_config()
        self._current_model = None
    
    def _get_default_config_file(self) -> str:
        """Get default path for model configuration file"""
        # Look for config file in src directory
        src_dir = os.path.dirname(__file__)
        return os.path.join(src_dir, 'model_config.json')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration from file"""
        default_config = {
            'active_model': 'original',
            'models': {
                'original': {
                    'enabled': True,
                    'description': 'Original fixed-weight model'
                },
                'calibrated': {
                    'enabled': True,
                    'description': 'ML-calibrated model with optimized weights'
                }
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                
                logger.info(f"Loaded model configuration from {self.config_file}")
                return config
            else:
                logger.info(f"No config file found, using defaults")
                return default_config
                
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}, using defaults")
            return default_config
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved model configuration to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def get_model(self, model_name: str = None) -> BaseBeautyModel:
        """Get a beauty score model instance"""
        if model_name is None:
            model_name = self.config.get('active_model', 'original')
        
        if model_name not in self._models:
            logger.error(f"Unknown model: {model_name}")
            raise ValueError(f"Unknown model: {model_name}")
        
        if not self.config['models'].get(model_name, {}).get('enabled', True):
            logger.error(f"Model {model_name} is disabled")
            raise ValueError(f"Model {model_name} is disabled")
        
        try:
            model_class = self._models[model_name]
            model = model_class()
            
            logger.info(f"Created model: {model_name} v{model.version}")
            return model
            
        except Exception as e:
            logger.error(f"Error creating model {model_name}: {str(e)}")
            raise
    
    def get_active_model(self) -> BaseBeautyModel:
        """Get the currently active model"""
        if self._current_model is None:
            self._current_model = self.get_model()
        return self._current_model
    
    def set_active_model(self, model_name: str):
        """Set the active model"""
        if model_name not in self._models:
            raise ValueError(f"Unknown model: {model_name}")
        
        if not self.config['models'].get(model_name, {}).get('enabled', True):
            raise ValueError(f"Model {model_name} is disabled")
        
        self.config['active_model'] = model_name
        self._current_model = None  # Force reload on next access
        self._save_config()
        
        logger.info(f"Set active model to: {model_name}")
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available models with their information"""
        models_info = {}
        
        for model_name, model_class in self._models.items():
            try:
                # Create temporary instance to get info
                model = model_class()
                model_info = model.get_model_info()
                
                # Add configuration info
                model_info['enabled'] = self.config['models'].get(model_name, {}).get('enabled', True)
                model_info['is_active'] = (model_name == self.config.get('active_model'))
                
                models_info[model_name] = model_info
                
            except Exception as e:
                logger.error(f"Error getting info for model {model_name}: {str(e)}")
                models_info[model_name] = {
                    'name': model_name,
                    'error': str(e),
                    'enabled': False,
                    'is_active': False
                }
        
        return models_info
    
    def enable_model(self, model_name: str):
        """Enable a model"""
        if model_name not in self._models:
            raise ValueError(f"Unknown model: {model_name}")
        
        if model_name not in self.config['models']:
            self.config['models'][model_name] = {}
        
        self.config['models'][model_name]['enabled'] = True
        self._save_config()
        
        logger.info(f"Enabled model: {model_name}")
    
    def disable_model(self, model_name: str):
        """Disable a model"""
        if model_name not in self._models:
            raise ValueError(f"Unknown model: {model_name}")
        
        # Can't disable the active model
        if model_name == self.config.get('active_model'):
            raise ValueError(f"Cannot disable active model: {model_name}")
        
        if model_name not in self.config['models']:
            self.config['models'][model_name] = {}
        
        self.config['models'][model_name]['enabled'] = False
        self._save_config()
        
        logger.info(f"Disabled model: {model_name}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()


# Global factory instance
_factory_instance = None

def get_model_factory() -> BeautyModelFactory:
    """Get global model factory instance"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = BeautyModelFactory()
    return _factory_instance

def get_beauty_model(model_name: str = None) -> BaseBeautyModel:
    """Convenience function to get a beauty model"""
    factory = get_model_factory()
    return factory.get_model(model_name)

def get_active_beauty_model() -> BaseBeautyModel:
    """Convenience function to get the active beauty model"""
    factory = get_model_factory()
    return factory.get_active_model()