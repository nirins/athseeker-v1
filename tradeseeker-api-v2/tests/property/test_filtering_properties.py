"""Property-based tests for filtering logic.

Feature: tradeseeker-api-v2
These tests verify correctness properties across all valid inputs.
"""

import json
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock

from src.handlers.golden_crosses import handle_golden_crosses, _apply_filters


# **Validates: Requirements 1.2**
# Property 1: Golden Cross Default Filters
@given(
    records=st.lists(
        st.fixed_dictionaries({
            'symbol': st.text(min_size=1),
            'green_days_30d_pct': st.floats(min_value=0, max_value=100),
            'max_red_candle_30d_pct': st.floats(min_value=-100, max_value=0)
        }),
        min_size=0,
        max_size=20
    )
)
@settings(max_examples=100)
def test_property_default_filters(records):
    """
    Property 1: For any request without query parameters, all returned records
    should have green_days_30d_pct >= 70 and max_red_candle_30d_pct >= -5.
    
    **Validates: Requirements 1.2**
    """
    with patch('src.handlers.golden_crosses.DynamoDBClient') as mock_db_class:
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.scan_golden_crosses.return_value = records
        
        response = handle_golden_crosses({})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # All returned records must satisfy default filters
        for record in body['data']:
            assert record['green_days_30d_pct'] >= 70, \
                f"Record {record['symbol']} has green_days {record['green_days_30d_pct']} < 70"
            assert record['max_red_candle_30d_pct'] >= -5, \
                f"Record {record['symbol']} has max_red_candle {record['max_red_candle_30d_pct']} < -5"


# **Validates: Requirements 1.3, 1.4**
# Property 2: Golden Cross Filter Compliance
@given(
    min_green=st.floats(min_value=0, max_value=100),
    max_red_candle=st.floats(min_value=-100, max_value=0),
    records=st.lists(
        st.fixed_dictionaries({
            'symbol': st.text(min_size=1),
            'green_days_30d_pct': st.floats(min_value=0, max_value=100),
            'max_red_candle_30d_pct': st.floats(min_value=-100, max_value=0)
        }),
        min_size=0,
        max_size=20
    )
)
@settings(max_examples=100)
def test_property_filter_compliance(min_green, max_red_candle, records):
    """
    Property 2: For any request with min_green and max_red_candle parameters,
    all returned records should satisfy both green_days_30d_pct >= min_green
    AND max_red_candle_30d_pct >= max_red_candle.
    
    **Validates: Requirements 1.3, 1.4**
    """
    with patch('src.handlers.golden_crosses.DynamoDBClient') as mock_db_class:
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.scan_golden_crosses.return_value = records
        
        response = handle_golden_crosses({
            'min_green': str(min_green),
            'max_red_candle': str(max_red_candle)
        })
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # All returned records must satisfy both filters
        for record in body['data']:
            assert record['green_days_30d_pct'] >= min_green, \
                f"Record {record['symbol']} has green_days {record['green_days_30d_pct']} < {min_green}"
            assert record['max_red_candle_30d_pct'] >= max_red_candle, \
                f"Record {record['symbol']} has max_red_candle {record['max_red_candle_30d_pct']} < {max_red_candle}"


# **Validates: Requirements 2.3, 2.4**
# Property 4: Date Range Filtering
@given(
    start_date=st.dates(min_value=__import__('datetime').date(2020, 1, 1), max_value=__import__('datetime').date(2024, 12, 31)),
    end_date=st.dates(min_value=__import__('datetime').date(2020, 1, 1), max_value=__import__('datetime').date(2024, 12, 31))
)
@settings(max_examples=100)
def test_property_date_range_filtering(start_date, end_date):
    """
    Property 4: For any request with start_date and/or end_date parameters,
    all returned price records should have dates within the specified range
    (date >= start_date AND date <= end_date).
    
    **Validates: Requirements 2.3, 2.4**
    """
    from src.handlers.stock_price import _filter_prices_by_date
    
    # Ensure start_date <= end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    # Generate test data with dates spanning the range
    stock_data = {
        'symbol': 'TEST.US',
        'prices': [
            {'date': '2020-01-01', 'close': 100.0},
            {'date': start_date.strftime('%Y-%m-%d'), 'close': 110.0},
            {'date': end_date.strftime('%Y-%m-%d'), 'close': 120.0},
            {'date': '2024-12-31', 'close': 130.0}
        ]
    }
    
    filtered = _filter_prices_by_date(
        stock_data,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    
    # All returned prices must be within range
    for price in filtered['prices']:
        assert price['date'] >= start_date.strftime('%Y-%m-%d'), \
            f"Price date {price['date']} < start_date {start_date}"
        assert price['date'] <= end_date.strftime('%Y-%m-%d'), \
            f"Price date {price['date']} > end_date {end_date}"


# Test that filtering logic is correct
@given(
    min_green=st.floats(min_value=0, max_value=100),
    max_red_candle=st.floats(min_value=-100, max_value=0),
    green_days=st.floats(min_value=0, max_value=100),
    red_candle=st.floats(min_value=-100, max_value=0)
)
@settings(max_examples=100)
def test_property_apply_filters_logic(min_green, max_red_candle, green_days, red_candle):
    """
    Property: _apply_filters should include a record if and only if
    green_days >= min_green AND red_candle >= max_red_candle.
    """
    records = [{
        'symbol': 'TEST.US',
        'green_days_30d_pct': green_days,
        'max_red_candle_30d_pct': red_candle
    }]
    
    filtered = _apply_filters(records, min_green, max_red_candle)
    
    should_include = (green_days >= min_green) and (red_candle >= max_red_candle)
    
    if should_include:
        assert len(filtered) == 1, \
            f"Record should be included: green_days={green_days} >= {min_green}, red_candle={red_candle} >= {max_red_candle}"
    else:
        assert len(filtered) == 0, \
            f"Record should be excluded: green_days={green_days} >= {min_green} is {green_days >= min_green}, red_candle={red_candle} >= {max_red_candle} is {red_candle >= max_red_candle}"
