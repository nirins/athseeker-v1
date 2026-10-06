"""
Explain-chart endpoint handler for TradeSeekerAPI v2.

POST /explain-chart
  Body: { symbol: string, image: string (base64 PNG/JPEG, with or without
          a data: URI prefix), context?: string (plain-text numeric summary
          — current price, % change over 1/3/12 months, 52-week range, EMA
          position, volume vs average — computed client-side from the same
          price data already loaded for the charts) }

Sends a screenshot of the stock chart to an OpenAI vision model and returns
one short, specific paragraph. `context` matters more than the image here:
a vision model reading numbers off a chart image is unreliable and tends to
produce the same generic language for every stock ("shows upward momentum",
"near resistance"). Passing the real computed numbers as text gives it
something concrete to reference, which is what actually makes the response
stock-specific instead of interchangeable boilerplate.

Uses `requests` directly against OpenAI's REST API rather than the `openai`
package — the installed SDK (0.28.1, see requirements.txt) predates the
vision/image-input message format, and bumping it would mean migrating
openai_summary.py's calls too. Calling the REST API directly avoids that
risk entirely and keeps this endpoint self-contained.
"""

import base64
import logging
import re
from typing import Dict, Any

import requests

from src.formatters import success_response, error_response
from src.config import get_openai_api_key

logger = logging.getLogger(__name__)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
VISION_MODEL = "gpt-4o-mini"
MAX_IMAGE_BYTES = 6 * 1024 * 1024  # raw bytes; keeps the base64 JSON body safely under API Gateway's 10MB limit

_DATA_URI_PATTERN = re.compile(r'^data:image/(png|jpeg|jpg);base64,(.+)$', re.DOTALL)


def handle_explain_chart(body: Dict[str, Any]) -> dict:
    symbol = (body or {}).get('symbol', '').strip()
    image_data = (body or {}).get('image', '')
    context = (body or {}).get('context', '').strip()

    if not symbol:
        return error_response("symbol is required", 400)
    if not image_data:
        return error_response("image is required", 400)

    match = _DATA_URI_PATTERN.match(image_data)
    image_b64 = match.group(2) if match else image_data

    try:
        raw_bytes = base64.b64decode(image_b64, validate=False)
    except Exception:
        return error_response("image must be valid base64", 400)

    if not raw_bytes:
        return error_response("image is empty", 400)
    if len(raw_bytes) > MAX_IMAGE_BYTES:
        return error_response(f"image too large (max {MAX_IMAGE_BYTES // (1024 * 1024)}MB)", 400)

    try:
        api_key = get_openai_api_key()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return error_response("OpenAI service not configured", 500)

    prompt = _build_prompt(symbol, context)

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a financial chart analyst. Write exactly one concise, "
                    "data-grounded paragraph per request. Use the specific numbers "
                    "given in the prompt rather than generic descriptions — avoid "
                    "boilerplate phrasing that could apply to any stock. Describe "
                    "the chart image itself only in ways that are visually obvious "
                    "(shape of the move, volatility); do not invent precise price "
                    "levels you can't actually read off the image."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]
            }
        ],
        "max_tokens": 220,
        "temperature": 0.3
    }

    try:
        logger.info(f"Sending chart screenshot to {VISION_MODEL} for {symbol} ({len(raw_bytes)} bytes)")
        response = requests.post(
            OPENAI_CHAT_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        analysis = result['choices'][0]['message']['content']
        usage = result.get('usage', {})

        logger.info(f"Successfully generated chart explanation for {symbol}")

        return success_response({
            "symbol": symbol,
            "model": VISION_MODEL,
            "analysis": analysis,
            "usage": {
                "prompt_tokens": usage.get('prompt_tokens'),
                "completion_tokens": usage.get('completion_tokens'),
                "total_tokens": usage.get('total_tokens')
            }
        })

    except requests.exceptions.HTTPError as e:
        error_body = getattr(e.response, 'text', '')
        logger.error(f"OpenAI API error for {symbol}: {e} - {error_body}")
        return error_response("Failed to generate chart explanation", 502)
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenAI request failed for {symbol}: {e}")
        return error_response("Failed to reach OpenAI", 502)
    except Exception as e:
        logger.error(f"Unexpected error explaining chart for {symbol}: {e}", exc_info=True)
        return error_response("Internal server error", 500)


def _build_prompt(symbol: str, context: str = "") -> str:
    base_symbol = symbol.split('.')[0]

    context_block = (
        f"\nActual recent data for {base_symbol}, computed from the real price history "
        f"(use these exact numbers, don't estimate your own):\n{context}\n"
        if context else
        "\n(No numeric data was provided — read what you can directly off the chart image "
        "and say so rather than guessing precise figures.)\n"
    )

    return f"""
    This is a multi-timeframe price chart for {base_symbol} ({symbol}).
    {context_block}
    Write ONE paragraph — 3 to 5 sentences, no bullet points, no headers, no bold labels.
    Weave together the current trend, whether there's real room to move higher from here, and
    the main risk — using the specific numbers above wherever relevant (actual price, actual
    percentage moves, actual distance from the 52-week range or moving averages) instead of
    vague phrasing like "near resistance" or "shows momentum."

    Be genuinely specific to this stock's current situation rather than something that could be
    copy-pasted onto any other stock. If something about the numbers stands out — an unusually
    large recent move, being far from its 52-week range, a volume spike well above average — lead
    with that, since it's the most useful thing to flag. End with one concrete, non-generic
    takeaway, not a "monitor closely" platitude.
    """
