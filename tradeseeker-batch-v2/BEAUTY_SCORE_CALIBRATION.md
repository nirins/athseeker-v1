# Beauty Score Model Calibration

This document describes the beauty score calibration system that uses manually labeled training data to improve the automated beauty score calculation model.

## Overview

The beauty score model calculates a 0-100 score for stock breakouts based on five components:
- **Consolidation Score** (25%): How well the price consolidated before breakout
- **Volume Score** (20%): Volume surge on breakout day
- **Momentum Score** (25%): Momentum continuation after breakout
- **Green Candle Score** (20%): Percentage of green candles around breakout
- **Gap Score** (10%): Gap up on breakout day

The calibration system analyzes manually labeled training data to optimize these component weights.

## Training Data Collection

Users can manually label stock charts through the web application:

1. **Enable Label Mode**: Click "Label Training" button in dashboard
2. **Label Charts**: Click the 🏷️ button on individual charts
3. **Select Grade**: Choose from A, B, C, D, F grades
4. **Data Storage**: Labeled data is stored in S3 bucket `tradeseeker-training-data`

### S3 Structure
```
tradeseeker-training-data/
├── A/
│   ├── AAPL-1709123456789.json
│   └── MSFT-1709123456790.json
├── B/
│   ├── GOOGL-1709123456791.json
│   └── TSLA-1709123456792.json
├── C/
├── D/
└── F/
```

## Calibration Process

### 1. Install Dependencies

```bash
cd tradeseeker-batch-v2/scripts
pip install -r requirements-calibration.txt
```

### 2. Run Calibration Analysis

```bash
python calibrate_beauty_model.py
```

This script will:
- Load all training data from S3
- Calculate beauty scores using current algorithm
- Analyze correlations between manual grades and calculated scores
- Use machine learning to optimize component weights
- Generate a comprehensive calibration report

### 3. Review Results

The script generates `beauty_model_calibration_report.json` containing:

```json
{
  "summary": {
    "total_samples": 150,
    "grade_distribution": {"A": 30, "B": 45, "C": 40, "D": 25, "F": 10},
    "current_model_r2": 0.652,
    "optimized_model_r2": 0.784
  },
  "analysis": {
    "correlations": {
      "consolidation_score": 0.45,
      "volume_score": 0.62,
      "momentum_score": 0.71,
      "green_candle_score": 0.38,
      "gap_score": 0.29
    }
  },
  "optimization": {
    "current_weights": {
      "consolidation": 0.25,
      "volume": 0.20,
      "momentum": 0.25,
      "green_candle": 0.20,
      "gap": 0.10
    },
    "optimized_weights": {
      "consolidation": 0.22,
      "volume": 0.28,
      "momentum": 0.35,
      "green_candle": 0.12,
      "gap": 0.03
    }
  },
  "recommendations": [
    "✅ Optimized weights could improve model performance (R² 0.652 → 0.784)",
    "🔧 Consider increase momentum weight from 0.25 to 0.35",
    "📊 Need more grade F samples (10 samples, 6.7%)"
  ]
}
```

### 4. Apply Optimized Weights

```bash
python update_beauty_weights.py
```

This script will:
- Load calibration results
- Show proposed weight changes and performance improvement
- Ask for confirmation
- Update the breakout analyzer files with new weights
- Create backups of original files

### 5. Deploy Updated Model

```bash
cd ..
make batch
```

## Interpreting Results

### Correlation Analysis
- **High correlation (>0.6)**: Component strongly predicts manual grades
- **Medium correlation (0.3-0.6)**: Component moderately predicts manual grades  
- **Low correlation (<0.3)**: Component weakly predicts manual grades

### R² Score (Coefficient of Determination)
- **R² > 0.8**: Excellent model performance
- **R² 0.6-0.8**: Good model performance
- **R² 0.4-0.6**: Fair model performance
- **R² < 0.4**: Poor model performance

### Weight Optimization
The system uses linear regression to find optimal weights that minimize the difference between calculated beauty scores and manual grade scores.

## Best Practices

### Data Collection
1. **Balanced Distribution**: Aim for roughly equal samples across all grades
2. **Minimum Samples**: Collect at least 20 samples per grade for reliable analysis
3. **Quality Over Quantity**: Focus on clear, representative examples
4. **Regular Updates**: Re-run calibration as more training data is collected

### Calibration Frequency
- **Initial Setup**: Run after collecting 100+ samples
- **Regular Updates**: Re-calibrate monthly or after collecting 50+ new samples
- **Performance Monitoring**: Monitor beauty score accuracy and re-calibrate if performance degrades

### Validation
1. **Cross-Validation**: Reserve some labeled data for testing
2. **A/B Testing**: Compare old vs new model performance
3. **User Feedback**: Monitor user satisfaction with beauty scores

## Troubleshooting

### Common Issues

**"No training data available"**
- Ensure S3 bucket `tradeseeker-training-data` exists
- Check AWS credentials and permissions
- Verify training data has been labeled through web app

**"Insufficient data for weight optimization"**
- Collect more training samples (minimum 10 per grade)
- Ensure data is properly formatted JSON files

**"Low correlation with manual grades"**
- Review component calculation logic
- Consider adding new components or modifying existing ones
- Check for data quality issues

**"Minimal improvement"**
- Current model may already be well-calibrated
- Collect more diverse training samples
- Consider non-linear optimization techniques

### Debug Mode

Add debug logging to calibration script:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Usage

### Custom Grade Mapping

Modify grade-to-score mapping in calibration script:

```python
self.grade_to_score = {
    'A': 95,  # Excellent
    'B': 80,  # Good  
    'C': 65,  # Average
    'D': 45,  # Poor
    'F': 20   # Failed
}
```

### Component Analysis

Analyze individual component performance:

```python
# Add to calibration script
def analyze_component_performance(self, component_name: str):
    # Detailed analysis of specific component
    pass
```

### Non-Linear Optimization

For advanced users, consider using non-linear optimization:

```python
from scipy.optimize import minimize

def optimize_nonlinear_weights(self, analysis_data):
    # Non-linear weight optimization
    pass
```

## Monitoring

### Performance Metrics
- Track R² score over time
- Monitor grade distribution balance
- Measure user satisfaction with beauty scores

### Alerts
Set up alerts for:
- R² score drops below threshold
- Significant changes in grade distribution
- Calibration script failures

## Future Enhancements

1. **Real-time Calibration**: Automatically update weights as new training data arrives
2. **Component Evolution**: Add new beauty score components based on analysis
3. **Market-Specific Models**: Separate calibration for different markets (US, crypto, etc.)
4. **Ensemble Methods**: Combine multiple models for better performance
5. **Deep Learning**: Explore neural network approaches for beauty score calculation