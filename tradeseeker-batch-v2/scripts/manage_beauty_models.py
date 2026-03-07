#!/usr/bin/env python3
"""
Beauty Model Management Script

Manage beauty score models - list, switch, enable/disable models.
"""

import sys
import os
import json
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

try:
    from beauty_models.model_factory import get_model_factory
    MODEL_SYSTEM_AVAILABLE = True
except ImportError:
    MODEL_SYSTEM_AVAILABLE = False

def list_models():
    """List all available beauty score models"""
    if not MODEL_SYSTEM_AVAILABLE:
        print("❌ Model system not available")
        return
    
    try:
        factory = get_model_factory()
        models = factory.list_models()
        config = factory.get_config()
        
        print("🤖 Beauty Score Models")
        print("=" * 50)
        print(f"Active Model: {config.get('active_model', 'unknown')}")
        print()
        
        for model_name, model_info in models.items():
            status_icon = "✅" if model_info.get('enabled', False) else "❌"
            active_icon = "🔥" if model_info.get('is_active', False) else "  "
            
            print(f"{active_icon} {status_icon} {model_name}")
            print(f"     Version: {model_info.get('version', 'unknown')}")
            print(f"     Description: {model_info.get('description', 'No description')}")
            
            if 'weights' in model_info:
                print(f"     Weights: {model_info['weights']}")
            
            if 'calibration' in model_info:
                cal = model_info['calibration']
                print(f"     Calibration: R²={cal.get('model_r2', 'unknown')}, "
                      f"Samples={cal.get('training_samples', 'unknown')}")
            
            if 'error' in model_info:
                print(f"     ❌ Error: {model_info['error']}")
            
            print()
        
    except Exception as e:
        print(f"❌ Error listing models: {str(e)}")

def switch_model(model_name: str):
    """Switch to a different model"""
    if not MODEL_SYSTEM_AVAILABLE:
        print("❌ Model system not available")
        return
    
    try:
        factory = get_model_factory()
        
        # Check if model exists and is enabled
        models = factory.list_models()
        if model_name not in models:
            print(f"❌ Model '{model_name}' not found")
            print("Available models:")
            for name in models.keys():
                print(f"  - {name}")
            return
        
        if not models[model_name].get('enabled', False):
            print(f"❌ Model '{model_name}' is disabled")
            return
        
        # Switch to the model
        factory.set_active_model(model_name)
        print(f"✅ Switched to model: {model_name}")
        
        # Test the model
        model = factory.get_model(model_name)
        model_info = model.get_model_info()
        print(f"   Version: {model_info.get('version')}")
        print(f"   Description: {model_info.get('description')}")
        
    except Exception as e:
        print(f"❌ Error switching model: {str(e)}")

def enable_model(model_name: str):
    """Enable a model"""
    if not MODEL_SYSTEM_AVAILABLE:
        print("❌ Model system not available")
        return
    
    try:
        factory = get_model_factory()
        factory.enable_model(model_name)
        print(f"✅ Enabled model: {model_name}")
        
    except Exception as e:
        print(f"❌ Error enabling model: {str(e)}")

def disable_model(model_name: str):
    """Disable a model"""
    if not MODEL_SYSTEM_AVAILABLE:
        print("❌ Model system not available")
        return
    
    try:
        factory = get_model_factory()
        factory.disable_model(model_name)
        print(f"✅ Disabled model: {model_name}")
        
    except Exception as e:
        print(f"❌ Error disabling model: {str(e)}")

def show_config():
    """Show current model configuration"""
    if not MODEL_SYSTEM_AVAILABLE:
        print("❌ Model system not available")
        return
    
    try:
        factory = get_model_factory()
        config = factory.get_config()
        
        print("⚙️  Model Configuration")
        print("=" * 30)
        print(json.dumps(config, indent=2))
        
    except Exception as e:
        print(f"❌ Error showing config: {str(e)}")

def test_model(model_name: str = None):
    """Test a model with sample data"""
    if not MODEL_SYSTEM_AVAILABLE:
        print("❌ Model system not available")
        return
    
    try:
        factory = get_model_factory()
        
        if model_name:
            model = factory.get_model(model_name)
        else:
            model = factory.get_active_model()
        
        print(f"🧪 Testing model: {model.model_name} v{model.version}")
        
        # Create sample data for testing
        sample_pre_breakout = [
            {'date': '2024-01-01', 'open': 100, 'high': 102, 'low': 99, 'close': 101, 'volume': 1000000},
            {'date': '2024-01-02', 'open': 101, 'high': 103, 'low': 100, 'close': 102, 'volume': 1100000},
            {'date': '2024-01-03', 'open': 102, 'high': 104, 'low': 101, 'close': 103, 'volume': 1200000},
            {'date': '2024-01-04', 'open': 103, 'high': 105, 'low': 102, 'close': 104, 'volume': 1300000},
            {'date': '2024-01-05', 'open': 104, 'high': 106, 'low': 103, 'close': 105, 'volume': 1400000}
        ]
        
        sample_breakout_day = {
            'date': '2024-01-06', 'open': 107, 'high': 110, 'low': 106, 'close': 109, 'volume': 2500000
        }
        
        sample_post_breakout = [
            sample_breakout_day,
            {'date': '2024-01-07', 'open': 109, 'high': 112, 'low': 108, 'close': 111, 'volume': 1800000},
            {'date': '2024-01-08', 'open': 111, 'high': 114, 'low': 110, 'close': 113, 'volume': 1600000}
        ]
        
        # Calculate beauty score
        result = model.calculate_beauty_score(sample_pre_breakout, sample_breakout_day, sample_post_breakout)
        
        print("📊 Test Results:")
        print(f"   Beauty Score: {result.get('beauty_score', 'N/A')}")
        print(f"   Grade: {result.get('grade', 'N/A')}")
        
        if 'consolidation_score' in result:
            print(f"   Consolidation: {result['consolidation_score']}")
        if 'volume_score' in result:
            print(f"   Volume: {result['volume_score']}")
        if 'momentum_score' in result:
            print(f"   Momentum: {result['momentum_score']}")
        if 'green_candle_score' in result:
            print(f"   Green Candle: {result['green_candle_score']}")
        if 'gap_score' in result:
            print(f"   Gap: {result['gap_score']}")
        
        print("✅ Model test completed successfully")
        
    except Exception as e:
        print(f"❌ Error testing model: {str(e)}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🤖 Beauty Model Management")
        print("=" * 30)
        print("Usage:")
        print("  python manage_beauty_models.py list")
        print("  python manage_beauty_models.py switch <model_name>")
        print("  python manage_beauty_models.py enable <model_name>")
        print("  python manage_beauty_models.py disable <model_name>")
        print("  python manage_beauty_models.py config")
        print("  python manage_beauty_models.py test [model_name]")
        print()
        print("Examples:")
        print("  python manage_beauty_models.py list")
        print("  python manage_beauty_models.py switch calibrated")
        print("  python manage_beauty_models.py test original")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_models()
    elif command == 'switch':
        if len(sys.argv) < 3:
            print("❌ Model name required for switch command")
            return
        switch_model(sys.argv[2])
    elif command == 'enable':
        if len(sys.argv) < 3:
            print("❌ Model name required for enable command")
            return
        enable_model(sys.argv[2])
    elif command == 'disable':
        if len(sys.argv) < 3:
            print("❌ Model name required for disable command")
            return
        disable_model(sys.argv[2])
    elif command == 'config':
        show_config()
    elif command == 'test':
        model_name = sys.argv[2] if len(sys.argv) > 2 else None
        test_model(model_name)
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()