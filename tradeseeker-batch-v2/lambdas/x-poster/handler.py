"""
X (Twitter) Poster Lambda
Posts top 3 ATH stocks by beauty score to @ATHSeekerX
"""

import json
import os
import boto3
import logging
import requests
from requests_oauthlib import OAuth1
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get('AWS_REGION', 'ap-southeast-1')
ATH_TABLE = os.environ.get('ATH_TABLE_NAME')
X_SECRET_NAME = os.environ.get('X_SECRET_NAME')
MARKET_CODE = os.environ.get('MARKET_CODE', 'US')

X_POST_URL = 'https://api.twitter.com/2/tweets'


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
        ScanIndexForward=False,  # descending by beauty_score
        Limit=3
    )

    return response.get('Items', [])


def format_tweet(stocks):
    lines = ['🚀 Top ATH Breakouts Today\n']
    for i, stock in enumerate(stocks, 1):
        symbol = stock.get('symbol', '')
        ticker = symbol.split('.')[0]  # strip market suffix e.g. FDX.US -> FDX
        score = float(stock.get('beauty_score', 0)) / 10
        price = stock.get('current_price') or stock.get('ath_price')
        price_str = f'${float(price):.2f}' if price else ''
        url = f'https://athseeker.com/stock/{symbol}'
        lines.append(f'{i}. ${ticker} {price_str} | Score: {score:.1f}\n{url}')

    lines.append('\n#ATH #Stocks #Breakout')
    return '\n'.join(lines)


def post_tweet(text, creds):
    auth = OAuth1(
        creds['consumer_key'],
        creds['consumer_secret'],
        creds['access_token'],
        creds['access_token_secret']
    )
    response = requests.post(X_POST_URL, json={'text': text}, auth=auth)
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

    tweet_text = format_tweet(stocks)
    logger.info(f'Tweet:\n{tweet_text}')

    creds = get_x_credentials()
    result = post_tweet(tweet_text, creds)

    logger.info(f'Tweet posted: {result}')
    return {'statusCode': 200, 'body': json.dumps(result)}
