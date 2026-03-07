# Beauty Score Model System

This document describes the new beauty score model system that allows multiple models to coexist and be switched dynamically in the batch processing system.

## Overview

The beauty score model system provides:
- **Multiple Models**: Support for different beauty score calculation algorithms
- **Dynamic Switching**: Change active model without code deployment
- **Model Versioning**: Track different versions and their performance
- **Backward Compatibility**: Original algorithm preserved as baseline
- **Configuration Management**: Easy model enable/disable and switching

## Architecture

### Model Hierarchy
```
BaseBeautyModel (Abstract)
├── OriginalBeautyModel (v1.0) - Fixed weights, stable baseline
└── CalibratedBeautyModel (v2.0) - ML-optimized weights from training data
```

### Key Components

**1. Base Model (`base_model.py`)**
- Abstract base class for all beauty score models
- Defines common interface and validation methods
- Provides standard grade conversion (A, B, C, D, F)

**2. Original Model (`original_model.py`)**
- Preserves the existing beauty score algorithm
- Fixed component weights (consolidation: 25%, volume: 20%, etc.)
- Serves as stable baseline for comparison

**3. Calibrated Model (`calibrated_model.py`)**
- Uses machine learning optimized weights
- Loads calibration data from training analysis
- Automatically updates when new calibration is performed

**4. Model Factory (`model_factory.py`)**
- Creates and manages model instances
- Handles model switching and configuration
- Provides global access to active model

## Usage

### Command Line Management

**List Available Models:**
```bash
make model-list
```

**Switch Active Model:**
```bash
make model-switch MODEL=calibrated
make model-switch MODEL=original
```

**Test Model Performance:**
```bash
make model-test                    # Test active model
make model-test MODEL=original     # Test specific model
```

**View Configuration:**
```bash
make model-config
```

### Programmatic Usage

**Get Active Model:**
```python
from beauty_models.model_factory import get_active_beauty_model

model = get_active_beauty_model()
result = model.calculate_beauty_score(pre_breakout, breakout_day, post_breakout)
```

**Get Specific Model:**
```python
from beauty_models.model_factory import get_beauty_model

original_model = get_beauty_model('original')
calibrated_model = get_beauty_model('calibrated')
```

**Switch Models:**
```python
from beauty_models.model_factory import get_model_factory

factory = get_model_factory()
factory.set_active_model('calibrated')
```

## Model Configuration

### Configuration File Location
`tradeseeker-batch-v2/src/beauty_models/model_config.json`

### Configuration Structure
```json
{
  "active_model": "original",
  "models": {
    "original": {
      "enabled": true,
      "description": "Original fixed-weight model"
    },
    "calibrated": {
      "enabled": true,
      "description": "ML-calibrated model with optimized weights"
    }
  }
}
```

### Configuration Options
- **active_model**: Currently active model name
- **models.{name}.enabled**: Whether model is available for use
- **models.{name}.description**: Human-readable description

## Model Creation Workflow

### 1. Training Data Collection
Users label charts through the web application:
```bash
# Check training data status
make train-check

# Migrate old grade system if needed
make train-migrate
```

### 2. Model Calibration
Run calibration analysis to create new model:
```bash
# Full training workflow (creates calibrated model)
make train

# Or step by step:
make train-analyze  # Creates calibrated_weights.json
```

### 3. Model Activation
Switch to the new calibrated model:
```bash
make model-switch MODEL=calibrated
```

### 4. Deployment
Deploy the updated batch system:
```bash
make batch
```

## Model Comparison

| Feature | Original Model | Calibrated Model |
|---------|---------------|------------------|
| **Weights** | Fixed (25%, 20%, 25%, 20%, 10%) | ML-optimized from training data |
| **Performance** | Baseline | Improved accuracy with sufficient training data |
| **Stability** | Always consistent | Depends on training data quality |
| **Use Case** | Stable baseline, fallback | Production use with good training data |
| **Updates** | Never changes | Updates when retrained |

## Integration with Batch Processing

### Breakout Analyzer Integration
The `BreakoutAnalyzer` class automatically uses the model system:

```python
# In breakout_analyzer.py
def calculate_breakout_beauty_score(self, price_data, ath_date, ath_price):
    if MODEL_SYSTEM_AVAILABLE:
        return self._calculate_with_model_system(price_data, ath_index)
    else:
        return self._calculate_with_original_method(price_data, ath_index)
```

### Fallback Mechanism
- If model system fails, falls back to original calculation
- Ensures backward compatibility and reliability
- Logs which method was used for debugging

### Lambda Packaging
The model system is automatically included in Lambda packages:
```bash
# Beauty models are copied during packaging
make batch  # Includes latest model configuration
```

## Model Performance Monitoring

### Model Information
Each model provides metadata:
```python
model_info = model.get_model_info()
# Returns: name, version, description, weights, calibration info
```

### Result Tracking
Beauty score results include model information:
```python
result = {
    'beauty_score': 85.2,
    'grade': 'A',
    'model_name': 'calibrated',
    'model_version': '2.0',
    # ... component scores
}
```

### Performance Metrics
- **R² Score**: Model accuracy vs manual grades
- **Training Samples**: Number of samples used for calibration
- **Improvement**: Performance gain over baseline

## Best Practices

### Model Selection
1. **Start with Original**: Use original model as baseline
2. **Collect Training Data**: Gather 100+ balanced samples
3. **Create Calibrated Model**: Run calibration analysis
4. **Compare Performance**: Test both models with sample data
5. **Gradual Rollout**: Switch to calibrated model after validation

### Model Management
1. **Keep Original Enabled**: Always maintain baseline model
2. **Test Before Switching**: Use `make model-test` before production
3. **Monitor Results**: Track beauty score quality after switching
4. **Regular Recalibration**: Update calibrated model as training data grows

### Configuration Management
1. **Version Control**: Track model configuration changes
2. **Environment Consistency**: Ensure same model across environments
3. **Rollback Plan**: Keep original model as fallback option

## Troubleshooting

### Common Issues

**"Model system not available"**
- Check if beauty_models package is in Lambda
- Verify Python path includes src directory
- Ensure all model files are present

**"Model not found"**
- Check model name spelling (case-sensitive)
- Verify model is enabled in configuration
- Use `make model-list` to see available models

**"Calibrated model using original weights"**
- No calibration file found (calibrated_weights.json)
- Run `make train-analyze` to create calibration
- Check file permissions and paths

**"Model test fails"**
- Check model dependencies are installed
- Verify sample data format is correct
- Review error logs for specific issues

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Model Creation
Create custom models by extending BaseBeautyModel:
```python
class CustomBeautyModel(BaseBeautyModel):
    def __init__(self):
        super().__init__("custom", "1.0")
    
    def calculate_beauty_score(self, pre_breakout, breakout_day, post_breakout):
        # Custom calculation logic
        pass
```

## Future Enhancements

### Planned Features
1. **Model Ensemble**: Combine multiple models for better accuracy
2. **A/B Testing**: Compare models with live traffic splitting
3. **Auto-Switching**: Automatically use best performing model
4. **Model Metrics**: Real-time performance monitoring
5. **Custom Models**: User-defined calculation algorithms

### Advanced Models
1. **Neural Network Model**: Deep learning approach
2. **Market-Specific Models**: Different models per market (US, crypto)
3. **Time-Based Models**: Models that adapt to market conditions
4. **Ensemble Models**: Weighted combination of multiple approaches

## API Reference

### Model Factory Methods
- `get_model(name)` - Get specific model instance
- `get_active_model()` - Get currently active model
- `set_active_model(name)` - Switch active model
- `list_models()` - Get all available models with info
- `enable_model(name)` - Enable a model
- `disable_model(name)` - Disable a model

### Base Model Methods
- `calculate_beauty_score(pre, breakout, post)` - Main calculation
- `get_model_info()` - Model metadata
- `validate_input_data(pre, breakout, post)` - Input validation

### Model Result Format
```python
{
    'beauty_score': float,           # 0-100 score
    'grade': str,                    # A, B, C, D, F
    'consolidation_score': float,    # Component scores
    'volume_score': float,
    'momentum_score': float,
    'green_candle_score': float,
    'gap_score': float,
    'model_name': str,               # Model identifier
    'model_version': str             # Model version
}
```