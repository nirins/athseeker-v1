# Golden Cross & Death Cross Feature

## Overview

The system now automatically detects golden cross and death cross signals and stores them in separate DynamoDB tables.

## What are Golden Cross and Death Cross?

A **Golden Cross** is a bullish technical indicator that occurs when:
- The 50-day EMA crosses **above** the 200-day EMA
- Signals a potential upward trend
- Stored in `golden-crosses` table

A **Death Cross** is the opposite (bearish):
- The 50-day EMA crosses **below** the 200-day EMA
- Signals a potential downward trend
- Stored in `death-crosses` table

## Implementation

### 1. Main Stock Prices Table

**Table**: `ts-batch-v2-{env}-stock-prices`

**New fields added**:
- `golden_cross`: String - "GOLDEN_CROSS", "DEATH_CROSS", or null
- `golden_cross_date`: String - Date when the golden cross occurred (YYYY-MM-DD)
- `death_cross_date`: String - Date when the death cross occurred (YYYY-MM-DD)

### 2. Golden Crosses Table (NEW)

**Table**: `ts-batch-v2-{env}-golden-crosses`

**Purpose**: Track all golden crosses that occurred in the past 30 days

**Schema**:
- `symbol` (Partition Key): Stock symbol with market code (e.g., "AAPL.US")
- `cross_date` (Sort Key): Date when the cross occurred
- `market_code`: Market code (US, BK, CC)
- `signal`: "GOLDEN_CROSS"
- `ema_50`: 50-day EMA value
- `ema_200`: 200-day EMA value
- `crossover_strength`: Difference between EMA 50 and EMA 200
- `green_days_30d_pct`: Percentage of green days in last 30 days
- `max_red_candle_30d_pct`: Largest red candle percentage in last 30 days
- `detected_at`: Timestamp when detected
- `ttl`: Time-to-live (auto-deletes after 30 days)

**GSI Indexes**:
- `cross_date-index`: Query all symbols by date
- `market_code-cross_date-index`: Query by market and date

**Features**:
- Automatically deletes records older than 30 days using DynamoDB TTL
- On-demand billing (pay per request)
- Encrypted at rest

### 3. Death Crosses Table (NEW)

**Table**: `ts-batch-v2-{env}-death-crosses`

**Purpose**: Track all death crosses that occurred in the past 30 days

**Schema**: Same as golden-crosses table but with `signal`: "DEATH_CROSS"

**GSI Indexes**:
- `cross_date-index`: Query all symbols by date
- `market_code-cross_date-index`: Query by market and date

**Features**:
- Automatically deletes records older than 30 days using DynamoDB TTL
- On-demand billing (pay per request)
- Encrypted at rest

## How It Works

1. **Download stock data** → Calculate EMAs (7, 30, 50, 200)
2. **Detect cross signals** by scanning last 30 days of EMA 50 and EMA 200
3. **Calculate candle metrics** for last 30 days (green days %, max red candle %)
4. **Save to main table** with golden_cross flag, date, and candle metrics
5. **If cross detected within past 30 days**:
   - Golden cross → Save to `golden-crosses` table with 30-day TTL
   - Death cross → Save to `death-crosses` table with 30-day TTL

## Querying Cross Signals

### Query Golden Crosses

```bash
# Get all recent golden crosses
python3 scripts/query_golden_crosses.py --all

# Get golden crosses for specific date
python3 scripts/query_golden_crosses.py --date 2024-02-15

# Get golden crosses for specific market
python3 scripts/query_golden_crosses.py --market US

# Get golden crosses from last 3 days
python3 scripts/query_golden_crosses.py --days 3

# Save to JSON
python3 scripts/query_golden_crosses.py --all --json output/golden_crosses.json
```

### Query Death Crosses

```bash
# Get all recent death crosses
python3 scripts/query_death_crosses.py --all

# Get death crosses for specific date
python3 scripts/query_death_crosses.py --date 2024-02-15

# Get death crosses for specific market
python3 scripts/query_death_crosses.py --market US

# Save to JSON
python3 scripts/query_death_crosses.py --all --json output/death_crosses.json
```

### Check specific symbol

```bash
python3 scripts/query_stock.py AAPL.US --json
# Check the "golden_cross", "golden_cross_date", and "death_cross_date" fields
```

## Deployment

1. **Apply Terraform changes** to create the golden-crosses table:
```bash
cd terraform
terraform plan
terraform apply
```

2. **Package and deploy Lambda**:
```bash
./scripts/package-downloader.sh
aws lambda update-function-code \
  --function-name ts-batch-v2-dev-downloader \
  --zip-file fileb://lambdas/downloader/downloader.zip \
  --region ap-southeast-1
```

3. **Test with a symbol**:
```bash
aws sqs send-message \
  --queue-url https://sqs.ap-southeast-1.amazonaws.com/894546098844/ts-batch-v2-dev-download-queue \
  --message-body '{"symbol":"AAPL","marketCode":"US","date":"2024-02-15","requestId":"AAPL-US-test"}' \
  --region ap-southeast-1
```

## Cost Impact

**Golden Crosses Table + Death Crosses Table**:
- Storage: ~50-200 KB total (30 days of crosses)
- Writes: Same as main table (one write per symbol per day, if cross detected)
- Reads: Depends on usage
- **Estimated cost**: < $0.10/month (both tables combined)

## Use Cases

1. **Trading alerts**: Query both tables daily to find bullish (golden) and bearish (death) signals
2. **Backtesting**: Analyze historical crosses from the main table
3. **Screening**: Filter stocks with recent golden crosses (bullish) or death crosses (bearish)
4. **Notifications**: Build alerts when crosses are detected
5. **Risk management**: Monitor death crosses to identify potential downtrends

## Example: Find All Crosses Today

```python
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
today = datetime.now().strftime('%Y-%m-%d')

# Golden crosses (bullish)
golden_table = dynamodb.Table('ts-batch-v2-dev-golden-crosses')
golden_response = golden_table.query(
    IndexName='cross_date-index',
    KeyConditionExpression='cross_date = :today',
    ExpressionAttributeValues={':today': today}
)

print("Golden Crosses (Bullish):")
for item in golden_response['Items']:
    print(f"  {item['symbol']}: EMA50={item['ema_50']}, EMA200={item['ema_200']}")

# Death crosses (bearish)
death_table = dynamodb.Table('ts-batch-v2-dev-death-crosses')
death_response = death_table.query(
    IndexName='cross_date-index',
    KeyConditionExpression='cross_date = :today',
    ExpressionAttributeValues={':today': today}
)

print("\nDeath Crosses (Bearish):")
for item in death_response['Items']:
    print(f"  {item['symbol']}: EMA50={item['ema_50']}, EMA200={item['ema_200']}")
```
