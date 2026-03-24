"""
X (Twitter) Poster Lambda
Posts top 3 ATH stocks by beauty score with price chart to @ATHSeekerX
"""

import json
import os
import io
import boto3
import logging
import requests
from datetime import datetime, timedelta
from requests_oauthlib import OAuth1
from boto3.dynamodb.conditions import Key

import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get('AWS_REGION', 'ap-southeast-1')
ATH_TABLE = os.environ.get('ATH_TABLE_NAME')
PRICES_TABLE = os.environ.get('PRICES_TABLE_NAME')
X_SECRET_NAME = os.environ.get('X_SECRET_NAME')
MARKET_CODE = os.environ.get('MARKET_CODE', 'US')
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')

X_POST_URL = 'https://api.twitter.com/2/tweets'
X_MEDIA_UPLOAD_URL = 'https://upload.twitter.com/1.1/media/upload.json'


def get_x_credentials():
    client = boto3.client('secretsmanager', region_name=REGION)
    response = client.get_secret_value(SecretId=X_SECRET_NAME)
    return json.loads(response['SecretString'])


def get_top_stocks():
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(ATH_TABLE)
    response = table.query(
        IndexName='beauty_score-index',
        KeyConditionExpression=Key('market_code').eq(MARKET_CODE),
        ScanIndexForward=False,
        Limit=3
    )
    return response.get('Items', [])


def get_price_data(symbol):
    """Fetch last 90 days of price + EMA data from DynamoDB"""
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(PRICES_TABLE)
    response = table.get_item(Key={'symbol': symbol})
    item = response.get('Item')
    if not item:
        return [], []

    prices = item.get('prices', [])
    emas = item.get('moving_averages', [])

    # Keep last 90 days
    cutoff = (datetime.utcnow() - timedelta(days=90)).strftime('%Y-%m-%d')
    prices = [p for p in prices if p.get('date', '') >= cutoff]
    emas = [e for e in emas if e.get('date', '') >= cutoff]

    return prices, emas


def generate_chart(symbol, prices, emas):
    """Generate a candlestick chart with EMA 50 and EMA 200, return PNG bytes"""
    if not prices:
        return None

    # Build DataFrame for mplfinance
    df = pd.DataFrame([{
        'Date': pd.Timestamp(p['date']),
        'Open':  float(p.get('open', p['close'])),
        'High':  float(p.get('high', p['close'])),
        'Low':   float(p.get('low',  p['close'])),
        'Close': float(p['close']),
        'Volume': float(p.get('volume', 0)),
    } for p in prices])
    df.set_index('Date', inplace=True)
    df.sort_index(inplace=True)

    # Build EMA overlay lines
    ema_by_date = {e['date']: e for e in emas}
    ema50  = [float(ema_by_date[p['date']]['ema_50'])  if ema_by_date.get(p['date'], {}).get('ema_50')  else float('nan') for p in prices]
    ema200 = [float(ema_by_date[p['date']]['ema_200']) if ema_by_date.get(p['date'], {}).get('ema_200') else float('nan') for p in prices]

    ap = [
        mpf.make_addplot(ema50,  color='#f0b429', width=1.2, linestyle='--', label='EMA 50'),
        mpf.make_addplot(ema200, color='#e05252', width=1.2, linestyle='--', label='EMA 200'),
    ]

    style = mpf.make_mpf_style(
        base_mpf_style='nightclouds',
        facecolor='#0d1117',
        edgecolor='#30363d',
        figcolor='#0d1117',
        gridcolor='#21262d',
        gridstyle='--',
        y_on_right=True,
        marketcolors=mpf.make_marketcolors(
            up='#26a641', down='#e05252',
            edge={'up': '#26a641', 'down': '#e05252'},
            wick={'up': '#26a641', 'down': '#e05252'},
        ),
        rc={'axes.labelcolor': '#8b949e', 'xtick.color': '#8b949e', 'ytick.color': '#8b949e'},
    )

    ticker = symbol.split('.')[0]
    buf = io.BytesIO()
    fig, axes = mpf.plot(
        df,
        type='candle',
        style=style,
        addplot=ap,
        title=f'\n{ticker} — 90 Day',
        figsize=(10, 5),
        savefig=dict(fname=buf, format='png', dpi=120, bbox_inches='tight'),
        volume=False,
        tight_layout=True,
        returnfig=True,
    )
    # Move legend to top left using actual line handles (preserves colors)
    handles = [h for h in axes[0].get_lines() if h.get_label() in ('EMA 50', 'EMA 200')]
    axes[0].legend(
        handles=handles,
        loc='upper left',
        facecolor='#161b22',
        edgecolor='#30363d',
        labelcolor='white',
        fontsize=9,
    )
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor=fig.get_facecolor())
    import matplotlib.pyplot as plt
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def upload_media(image_bytes, creds):
    """Upload image to X and return media_id"""
    auth = OAuth1(
        creds['consumer_key'],
        creds['consumer_secret'],
        creds['access_token'],
        creds['access_token_secret']
    )
    response = requests.post(
        X_MEDIA_UPLOAD_URL,
        files={'media': ('chart.png', image_bytes, 'image/png')},
        auth=auth
    )
    response.raise_for_status()
    return response.json()['media_id_string']


def format_tweet(stocks):
    lines = ['🚀 Stocks hitting All-Time High today\n']
    for i, stock in enumerate(stocks, 1):
        symbol = stock.get('symbol', '')
        ticker = symbol.split('.')[0]
        score = float(stock.get('beauty_score', 0)) / 10
        price = stock.get('current_price') or stock.get('ath_price')
        price_str = f'${float(price):.2f}' if price else ''
        gain = stock.get('ath_percentage_gain')
        gain_str = f' +{float(gain):.1f}%' if gain else ''
        url = f'https://athseeker.com/stock/{symbol}'
        lines.append(f'{i}. {ticker} {url} {price_str} | Score: {score:.1f}')

    lines.append('\nAll big winners start like this.')
    lines.append('\n#ATH #Stocks #Breakout')
    return '\n'.join(lines)


def post_tweet(text, media_ids, creds):
    auth = OAuth1(
        creds['consumer_key'],
        creds['consumer_secret'],
        creds['access_token'],
        creds['access_token_secret']
    )
    payload = {'text': text}
    if media_ids:
        payload['media'] = {'media_ids': media_ids}

    response = requests.post(X_POST_URL, json=payload, auth=auth)
    if not response.ok:
        logger.error(f'X API error {response.status_code}: {response.text}')
    response.raise_for_status()
    return response.json()


def handler(event, context):
    logger.info('X Poster Lambda triggered')

    stocks = get_top_stocks()
    if not stocks:
        logger.warning(f'No ATH stocks found for market {MARKET_CODE}')
        return {'statusCode': 200, 'body': 'No stocks to post'}

    logger.info(f'Found {len(stocks)} stocks to post')

    creds = get_x_credentials()
    media_ids = []

    if PRICES_TABLE:
        for stock in stocks:
            symbol = stock.get('symbol', '')
            try:
                prices, emas = get_price_data(symbol)
                image_bytes = generate_chart(symbol, prices, emas)
                if image_bytes:
                    media_id = upload_media(image_bytes, creds)
                    media_ids.append(media_id)
                    logger.info(f'Chart uploaded for {symbol}, media_id: {media_id}')
            except Exception as e:
                logger.warning(f'Chart failed for {symbol}, skipping: {e}')

    tweet_text = format_tweet(stocks)
    logger.info(f'Tweet:\n{tweet_text}')

    result = post_tweet(tweet_text, media_ids or None, creds)
    logger.info(f'Tweet posted: {result}')
    return {'statusCode': 200, 'body': json.dumps(result)}
