# Beauty Score Model Training Workflow

This document describes how to use the automated training workflow to calibrate the beauty score model using manually labeled training data.

## Quick Start

```bash
# Run the complete training workflow
make train
```

This single command will:
1. Check training data status
2. Install calibration dependencies
3. Run calibration analysis
4. Apply optimized weights (with confirmation)

## Individual Steps

You can also run individual steps of the training workflow:

```bash
# 1. Check current training data status
make train-check

# 2. Install calibration dependencies
make train-install

# 3. Run calibration analysis
make train-analyze

# 4. Apply optimized weights
make train-apply
```

## Training Data Requirements

### Minimum Requirements
- **50+ samples** for basic calibration
- **100+ samples** for reliable results
- **20+ samples per grade** for balanced training

### Grade Distribution
The system works best with balanced data across all grades:
- **Grade A**: Excellent breakouts (20+ samples)
- **Grade B**: Good breakouts (20+ samples)
- **Grade C**: Average breakouts (20+ samples)
- **Grade D**: Poor breakouts (20+ samples)
- **Grade F**: Failed breakouts (20+ samples)

## Workflow Steps

### 1. Data Collection
Users label stock charts through the web application:
- Enable "Label Training" mode in dashboard
- Click 🏷️ button on individual charts
- Select appropriate grade (A, B, C, D, F)
- Data is automatically saved to S3 bucket

### 2. Check Training Data Status
```bash
make train-check
```

**Sample Output:**
```
📊 Training Data Summary:
   Total samples: 150

📈 Grade Distribution:
   Grade A:  30 samples ( 20.0%) ✅
   Grade B:  35 samples ( 23.3%) ✅
   Grade C:  40 samples ( 26.7%) ✅
   Grade D:  25 samples ( 16.7%) ⚠️
   Grade F:  20 samples ( 13.3%) ⚠️

💡 Recommendations:
   ✅ Ready for calibration (50+ samples)
   📈 Need more Grade D samples (current: 25, recommended: 30+)
```

### 3. Install Dependencies
```bash
make train-install
```

Installs required Python packages:
- `boto3` - AWS S3 access
- `pandas` - Data analysis
- `numpy` - Numerical computations
- `scikit-learn` - Machine learning

### 4. Run Calibration Analysis
```bash
make train-analyze
```

**What it does:**
- Loads all training data from S3
- Calculates beauty scores using current algorithm
- Analyzes correlations between manual grades and calculated scores
- Uses machine learning to optimize component weights
- Generates comprehensive calibration report

**Sample Output:**
```
🔬 Beauty Score Model Calibration
==================================================
📊 Analysis Summary:
   Total samples: 150
   Current model R²: 0.652
   Optimized model R²: 0.784

⚖️  Weight Comparison:
   consolidation: 0.250 ↘️ 0.220 (-0.030)
   volume: 0.200 ↗️ 0.280 (+0.080)
   momentum: 0.250 ↗️ 0.350 (+0.100)
   green_candle: 0.200 ↘️ 0.120 (-0.080)
   gap: 0.100 ↘️ 0.030 (-0.070)

💡 Recommendations:
   ✅ Optimized weights could improve model performance (R² 0.652 → 0.784)
   🔧 Consider increase momentum weight from 0.25 to 0.35
   🔧 Consider increase volume weight from 0.20 to 0.28
```

### 5. Apply Optimized Weights
```bash
make train-apply
```

**What it does:**
- Shows proposed weight changes and performance improvement
- Asks for confirmation before making changes
- Updates breakout analyzer files with new weights
- Creates backups of original files

**Sample Interaction:**
```
📊 Proposed Weight Changes:
Component       Current  Optimized  Change  
---------------------------------------------
consolidation   0.250    0.220      -0.030 ↘️
volume          0.200    0.280      +0.080 ↗️
momentum        0.250    0.350      +0.100 ↗️
green_candle    0.200    0.120      -0.080 ↘️
gap             0.100    0.030      -0.070 ↘️

📈 Performance Improvement:
   Current R²: 0.652
   Optimized R²: 0.784
   Improvement: +0.132

Apply these weight changes? (y/N): y

✅ Weight update completed!
   Updated 2 files
   Backups created with .backup extension
```

## After Training

### Deploy Updated Model
```bash
make batch
```

This deploys the updated beauty score model to production.

### Monitor Performance
- Track beauty score accuracy over time
- Monitor user feedback on score quality
- Re-run calibration as more training data is collected

## Best Practices

### Data Collection
1. **Quality over Quantity**: Focus on clear, representative examples
2. **Balanced Distribution**: Aim for equal samples across all grades
3. **Regular Updates**: Continuously collect new training data
4. **Diverse Examples**: Include various market conditions and stock types

### Calibration Frequency
- **Initial Setup**: Run after collecting 100+ samples
- **Regular Updates**: Re-calibrate monthly or after 50+ new samples
- **Performance Monitoring**: Re-calibrate if model performance degrades

### Validation
1. **Review Results**: Always review calibration report before applying changes
2. **Backup Safety**: Original files are automatically backed up
3. **Gradual Deployment**: Monitor performance after deploying changes
4. **Rollback Plan**: Keep backups to revert if needed

## Troubleshooting

### Common Issues

**"No training data available"**
- Check if users have labeled charts in web application
- Verify S3 bucket `tradeseeker-training-data` exists
- Ensure AWS credentials are properly configured

**"Insufficient data for calibration"**
- Collect more training samples (minimum 50 recommended)
- Ensure balanced distribution across all grades
- Check data quality and format

**"Minimal improvement"**
- Current model may already be well-calibrated
- Collect more diverse training samples
- Consider if current performance is acceptable

**"Permission denied"**
- Check AWS credentials and S3 bucket permissions
- Ensure write access to breakout analyzer files
- Verify Python package installation permissions

### Debug Mode
Add verbose logging to see detailed execution:
```bash
export PYTHONPATH=.
python3 -v tradeseeker-batch-v2/scripts/calibrate_beauty_model.py
```

## Advanced Usage

### Custom Thresholds
Modify minimum sample requirements in scripts:
```python
# In calibrate_beauty_model.py
MIN_SAMPLES_TOTAL = 50
MIN_SAMPLES_PER_GRADE = 10
```

### Manual Weight Updates
Edit weights directly in breakout analyzer:
```python
# In breakout_analyzer.py
beauty_score = (
    consolidation_score * 0.22 +  # Updated weight
    volume_score * 0.28 +         # Updated weight
    momentum_score * 0.35 +       # Updated weight
    green_candle_score * 0.12 +   # Updated weight
    gap_score * 0.03              # Updated weight
)
```

### Batch Processing
Process multiple calibration runs:
```bash
# Run calibration for different time periods
make train-analyze
# Review results, then apply if beneficial
make train-apply
```

## Files Generated

- `beauty_model_calibration_report.json` - Detailed analysis results
- `*.backup` - Backup files before weight updates
- Logs in terminal output for debugging

## Integration with CI/CD

Add to deployment pipeline:
```yaml
# Example GitHub Actions workflow
- name: Check Training Data
  run: make train-check

- name: Run Calibration (if enough data)
  run: |
    if [ $(python3 -c "import json; print(json.load(open('report.json'))['summary']['total_samples'])") -gt 100 ]; then
      make train-analyze
    fi
```