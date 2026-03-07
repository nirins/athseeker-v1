"""Property-based tests for validation logic.

Feature: tradeseeker-api-v2
These tests verify validation correctness properties.
"""

import json
from hypothesis import given, strategies as st, settings, assume

from src.validators import validate_golden_cross_params, validate_stock_price_params


# **Validates: Requirements 2.2**
# Property 3: Symbol Validation
@given(
    symbol=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
)
@settings(max_examples=100)
def test_property_symbol_validation(symbol):
    """
    Property 3: For any symbol path parameter, if it does not contain a valid
    market code suffix (.US, .BK, or .CC), the validation should return an error.
    
    **Validates: Requirements 2.2**
    """
    # Add market code suffix to some symbols
    has_valid_suffix = any(symbol.endswith(suffix) for suffix in ['.US', '.BK', '.CC'])
    
    validated_symbol, validated_params, errors = validate_stock_price_params(symbol, {})
    
    if has_valid_suffix:
        # Should not have market code error
        assert not any('market code suffix' in e for e in errors), \
            f"Symbol {symbol} has valid suffix but got error"
    else:
        # Should have market code error
        assert any('market code suffix' in e for e in errors), \
            f"Symbol {symbol} missing valid suffix but no error"


# **Validates: Requirements 3.1, 3.2, 3.5, 3.6**
# Property 5: Parameter Validation
@given(
    min_green=st.one_of(
        st.floats(min_value=-100, max_value=200),
        st.text(min_size=1, max_size=10)
    ),
    max_red_candle=st.one_of(
        st.floats(min_value=-200, max_value=100),
        st.text(min_size=1, max_size=10)
    ),
    days=st.one_of(
        st.integers(min_value=-100, max_value=1000),
        st.text(min_size=1, max_size=10)
    )
)
@settings(max_examples=100)
def test_property_parameter_validation(min_green, max_red_candle, days):
    """
    Property 5: For any request with invalid parameters, the validation
    should return appropriate error messages.
    
    **Validates: Requirements 3.1, 3.2, 3.5, 3.6**
    """
    params = {}
    
    # Add min_green if it's a valid type
    if isinstance(min_green, (int, float)):
        params['min_green'] = str(min_green)
    elif isinstance(min_green, str):
        params['min_green'] = min_green
    
    # Add max_red_candle if it's a valid type
    if isinstance(max_red_candle, (int, float)):
        params['max_red_candle'] = str(max_red_candle)
    elif isinstance(max_red_candle, str):
        params['max_red_candle'] = max_red_candle
    
    # Add days if it's a valid type
    if isinstance(days, (int, float)):
        params['days'] = str(int(days))
    elif isinstance(days, str):
        params['days'] = days
    
    validated, errors = validate_golden_cross_params(params)
    
    # Check min_green validation
    if 'min_green' in params:
        try:
            val = float(params['min_green'])
            if val < 0 or val > 100:
                assert any('min_green' in e for e in errors), \
                    f"min_green={val} out of range but no error"
        except (ValueError, TypeError):
            assert any('min_green' in e for e in errors), \
                f"min_green={params['min_green']} invalid type but no error"
    
    # Check max_red_candle validation
    if 'max_red_candle' in params:
        try:
            val = float(params['max_red_candle'])
            if val < -100 or val > 0:
                assert any('max_red_candle' in e for e in errors), \
                    f"max_red_candle={val} out of range but no error"
        except (ValueError, TypeError):
            assert any('max_red_candle' in e for e in errors), \
                f"max_red_candle={params['max_red_candle']} invalid type but no error"
    
    # Check days validation
    if 'days' in params:
        try:
            val = int(params['days'])
            if val <= 0:
                assert any('days' in e for e in errors), \
                    f"days={val} non-positive but no error"
        except (ValueError, TypeError):
            assert any('days' in e for e in errors), \
                f"days={params['days']} invalid type but no error"


# Test that valid parameters pass validation
@given(
    min_green=st.floats(min_value=0, max_value=100),
    max_red_candle=st.floats(min_value=-100, max_value=0),
    days=st.integers(min_value=1, max_value=365)
)
@settings(max_examples=100)
def test_property_valid_parameters_pass(min_green, max_red_candle, days):
    """
    Property: Valid parameters should pass validation without errors.
    """
    params = {
        'min_green': str(min_green),
        'max_red_candle': str(max_red_candle),
        'days': str(days)
    }
    
    validated, errors = validate_golden_cross_params(params)
    
    assert len(errors) == 0, f"Valid parameters got errors: {errors}"
    assert validated['min_green'] == min_green
    assert validated['max_red_candle'] == max_red_candle
    assert validated['days'] == days


# Test market validation
@given(
    market=st.text(min_size=1, max_size=10)
)
@settings(max_examples=100)
def test_property_market_validation(market):
    """
    Property: Market parameter should only accept US, BK, or CC.
    
    **Validates: Requirements 3.3**
    """
    params = {'market': market}
    validated, errors = validate_golden_cross_params(params)
    
    if market in ['US', 'BK', 'CC']:
        assert not any('market' in e for e in errors), \
            f"Valid market {market} got error"
        assert validated.get('market') == market
    else:
        assert any('market' in e for e in errors), \
            f"Invalid market {market} passed validation"
