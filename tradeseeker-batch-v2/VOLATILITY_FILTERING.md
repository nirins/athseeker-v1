# ATH Volatility Filtering

## Overview

The ATH (All-Time High) detection system now includes volatility filtering to exclude stocks with excessive daily price swings that may indicate manipulation, low liquidity, or data errors.

## How It Works

### Daily Volatility Calculation
```
Daily Volatility % = ((High - Low) / Low) × 100
```

### Filtering Logic
- Each daily price record is checked for excessive volatility
- Records exceeding the threshold are skipped from ATH consideration
- The filtering happens **before** ATH detection logic
- Filtered records are logged for monitoring

### Configuration

**Environment Variable**: `MAX_DAILY_VOLATILITY`
- **Default**: `100.0` (100%)
- **Type**: Float
- **Description**: Maximum allowed daily volatility percentage

### Examples

**Normal Stock** (5% volatility):
- High: $102.50, Low: $97.50, Close: $100.00
- Volatility: ((102.50 - 97.50) / 97.50) × 100 = 5.13%
- ✅ **Included** in ATH detection

**Volatile Stock** (150% volatility):
- High: $200.00, Low: $80.00, Close: $110.00  
- Volatility: ((200.00 - 80.00) / 80.00) × 100 = 150%
- ❌ **Filtered out** from ATH detection

## Benefits

1. **Quality Control**: Removes false ATH signals from manipulated stocks
2. **Data Integrity**: Filters out potential data errors or glitches
3. **Reliability**: Focuses on legitimate breakouts from stable stocks
4. **Configurable**: Threshold can be adjusted per environment

## Monitoring

Filtered records are logged with:
```
Filtering out SYMBOL on DATE due to excessive volatility: X.X% (max: Y.Y%)
```

## Deployment

The volatility filter is automatically applied to all ATH detection:
- No schema changes required
- Backward compatible
- Configurable via environment variables
- Applied at the data processing level

## Testing

Use the test script to verify filtering:
```bash
python3 tradeseeker-batch-v2/scripts/test_volatility_filter.py
```