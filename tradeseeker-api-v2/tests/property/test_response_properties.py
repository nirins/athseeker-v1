"""Property-based tests for response format.

Feature: tradeseeker-api-v2
These tests verify response format correctness properties.
"""

import json
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock

from src.handlers.golden_crosses import handle_golden_crosses
from src.handlers.stock_price import handle_stock_price
from src.formatters import success_response, error_response


# **Validates: Requirements 6.2, 6.3, 7.1, 7.4**
# Property 7: Response Format Consistency
@given(
    data=st.one_of(
        st.lists(st.dictionaries(st.text(), st.integers())),
        st.dictionaries(st.text(), st.integers())
    )
)
@settings(max_examples=100)
def test_property_success_response_format(data):
    """
    Property 7: For any successful response, it should have a 200 status code,
    Content-Type: application/json header, CORS headers, and a JSON body with
    a data field.
    
    **Validates: Requirements 6.2, 6.3, 7.1, 7.4**
    """
    response = success_response(data)
    
    # Check status code
    assert response['statusCode'] == 200, "Success response should have 200 status"
    
    # Check headers
    assert 'headers' in response
    assert response['headers']['Content-Type'] == 'application/json'
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
    assert 'Access-Control-Allow-Methods' in response['headers']
    assert 'Access-Control-Allow-Headers' in response['headers']
    
    # Check body structure
    assert 'body' in response
    body = json.loads(response['body'])
    assert 'data' in body
    assert body['data'] == data


@given(
    message=st.text(min_size=1, max_size=100),
    status_code=st.integers(min_value=400, max_value=599),
    errors=st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=1, max_size=5))
)
@settings(max_examples=100)
def test_property_error_response_format(message, status_code, errors):
    """
    Property 7: For any error response, it should have an appropriate error
    status code (4xx or 5xx) and a JSON body with an error field.
    
    **Validates: Requirements 6.2, 6.3, 7.1, 7.4**
    """
    response = error_response(message, status_code, errors)
    
    # Check status code
    assert response['statusCode'] == status_code
    assert 400 <= status_code < 600, "Error status should be 4xx or 5xx"
    
    # Check headers
    assert 'headers' in response
    assert response['headers']['Content-Type'] == 'application/json'
    assert 'Access-Control-Allow-Origin' in response['headers']
    
    # Check body structure
    assert 'body' in response
    body = json.loads(response['body'])
    assert 'error' in body
    assert body['error'] == message
    
    if errors:
        assert 'details' in body
        assert body['details'] == errors


# **Validates: Requirements 7.6**
# Property 8: Numeric Field Types
@given(
    ema_50=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    ema_200=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    green_days=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    max_red_candle=st.floats(min_value=-100, max_value=0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_property_numeric_field_types(ema_50, ema_200, green_days, max_red_candle):
    """
    Property 8: For any response containing numeric fields, they should be
    represented as numbers, not strings.
    
    **Validates: Requirements 7.6**
    """
    record = {
        'symbol': 'TEST.US',
        'ema_50': ema_50,
        'ema_200': ema_200,
        'green_days_30d_pct': green_days,
        'max_red_candle_30d_pct': max_red_candle
    }
    
    response = success_response([record])
    body = json.loads(response['body'])
    
    returned_record = body['data'][0]
    
    # All numeric fields should be numbers, not strings
    assert isinstance(returned_record['ema_50'], (int, float)), \
        f"ema_50 should be number, got {type(returned_record['ema_50'])}"
    assert isinstance(returned_record['ema_200'], (int, float)), \
        f"ema_200 should be number, got {type(returned_record['ema_200'])}"
    assert isinstance(returned_record['green_days_30d_pct'], (int, float)), \
        f"green_days_30d_pct should be number, got {type(returned_record['green_days_30d_pct'])}"
    assert isinstance(returned_record['max_red_candle_30d_pct'], (int, float)), \
        f"max_red_candle_30d_pct should be number, got {type(returned_record['max_red_candle_30d_pct'])}"


# Test CORS headers are always present
@given(
    status_code=st.integers(min_value=200, max_value=599)
)
@settings(max_examples=100)
def test_property_cors_headers_present(status_code):
    """
    Property: All responses should include CORS headers.
    
    **Validates: Requirements 6.2**
    """
    if 200 <= status_code < 400:
        response = success_response([], status_code)
    else:
        response = error_response("Error", status_code)
    
    headers = response['headers']
    
    assert 'Access-Control-Allow-Origin' in headers
    assert headers['Access-Control-Allow-Origin'] == '*'
    assert 'Access-Control-Allow-Methods' in headers
    assert 'Access-Control-Allow-Headers' in headers
