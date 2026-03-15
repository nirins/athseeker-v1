"""
Input validation module for TradeSeekerAPI v2.

This module provides validation functions for API request parameters,
accumulating multiple validation errors to provide comprehensive feedback.
"""

import re
from datetime import datetime
from typing import Tuple, Dict, List, Any, Optional


def validate_date_format(date_str: str, param_name: str) -> Optional[str]:
    """
    Validate date string is in YYYY-MM-DD format and represents a valid date.
    
    Args:
        date_str: Date string to validate
        param_name: Parameter name for error messages
        
    Returns:
        Error message if invalid, None if valid
    """
    if not date_str:
        return None
    
    # Check format with regex
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return f"{param_name} must be in YYYY-MM-DD format"
    
    # Validate it's a real date
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return f"{param_name} is not a valid date"
    
    return None


def validate_golden_cross_params(params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate golden cross query parameters.
    
    Args:
        params: Raw query parameters dict
        
    Returns:
        Tuple of (validated_params, errors)
        - validated_params: Dict with validated and type-converted values
        - errors: List of error messages (empty if all valid)
    """
    validated = {}
    errors = []
    
    # First validate market to determine defaults
    market = None
    if 'market' in params:
        market = params['market']
        if market not in ['US', 'BK', 'CC']:
            errors.append("market must be one of: US, BK, CC")
        else:
            validated['market'] = market
    
    # Set market-specific defaults
    if market == 'CC':
        default_min_green = 30
        default_max_red_candle = -20
    else:
        default_min_green = 60
        default_max_red_candle = -8
    
    # Validate min_green (0-100, market-specific default)
    if 'min_green' in params:
        try:
            min_green = float(params['min_green'])
            if min_green < 0 or min_green > 100:
                errors.append("min_green must be between 0 and 100")
            else:
                validated['min_green'] = min_green
        except (ValueError, TypeError):
            errors.append("min_green must be a valid number")
    else:
        validated['min_green'] = default_min_green
    
    # Validate max_red_candle (-100 to 0, market-specific default)
    if 'max_red_candle' in params:
        try:
            max_red_candle = float(params['max_red_candle'])
            if max_red_candle < -100 or max_red_candle > 0:
                errors.append("max_red_candle must be between -100 and 0")
            else:
                validated['max_red_candle'] = max_red_candle
        except (ValueError, TypeError):
            errors.append("max_red_candle must be a valid number")
    else:
        validated['max_red_candle'] = default_max_red_candle
    
    # Validate date (YYYY-MM-DD format)
    if 'date' in params:
        date_error = validate_date_format(params['date'], 'date')
        if date_error:
            errors.append(date_error)
        else:
            validated['date'] = params['date']
    
    # Validate days (positive integer)
    if 'days' in params:
        try:
            days = int(params['days'])
            if days <= 0:
                errors.append("days must be a positive integer")
            else:
                validated['days'] = days
        except (ValueError, TypeError):
            errors.append("days must be a positive integer")
    
    # Validate limit (optional, positive integer, default: 40)
    if 'limit' in params:
        try:
            limit = int(params['limit'])
            if limit <= 0:
                errors.append("limit must be a positive integer")
            elif limit > 1000:
                errors.append("limit cannot exceed 1000")
            else:
                validated['limit'] = limit
        except (ValueError, TypeError):
            errors.append("limit must be a valid integer")
    else:
        validated['limit'] = 50
    
    # Validate offset (optional, non-negative integer, default: 0)
    if 'offset' in params:
        try:
            offset = int(params['offset'])
            if offset < 0:
                errors.append("offset must be >= 0")
            else:
                validated['offset'] = offset
        except (ValueError, TypeError):
            errors.append("offset must be a valid integer")
    else:
        validated['offset'] = 0
    
    return validated, errors


def validate_ath_stocks_params(params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate ATH stocks query parameters.
    
    Args:
        params: Query parameters dict
        
    Returns:
        Tuple of (validated_params, errors)
    """
    validated = {}
    errors = []
    
    # Validate min_gain (default: 0)
    default_min_gain = 0.0
    if 'min_gain' in params:
        try:
            min_gain = float(params['min_gain'])
            if min_gain < 0:
                errors.append("min_gain must be >= 0")
            else:
                validated['min_gain'] = min_gain
        except (ValueError, TypeError):
            errors.append("min_gain must be a valid number")
    else:
        validated['min_gain'] = default_min_gain
    
    # Validate market (optional)
    if 'market' in params:
        market = params['market'].upper()
        if market not in ['US', 'BK', 'CC']:
            errors.append("market must be one of: US, BK, CC")
        else:
            validated['market'] = market
    
    # Validate date (YYYY-MM-DD format)
    if 'date' in params:
        date_error = validate_date_format(params['date'], 'date')
        if date_error:
            errors.append(date_error)
        else:
            validated['date'] = params['date']
    
    # Validate days (optional, positive integer)
    if 'days' in params:
        try:
            days = int(params['days'])
            if days <= 0:
                errors.append("days must be a positive integer")
            elif days > 365:
                errors.append("days cannot exceed 365")
            else:
                validated['days'] = days
        except (ValueError, TypeError):
            errors.append("days must be a valid integer")
    
    # Validate limit (optional, positive integer, default: 40)
    if 'limit' in params:
        try:
            limit = int(params['limit'])
            if limit <= 0:
                errors.append("limit must be a positive integer")
            elif limit > 1000:
                errors.append("limit cannot exceed 1000")
            else:
                validated['limit'] = limit
        except (ValueError, TypeError):
            errors.append("limit must be a valid integer")
    else:
        validated['limit'] = 40
    
    # Validate offset (optional, non-negative integer, default: 0)
    if 'offset' in params:
        try:
            offset = int(params['offset'])
            if offset < 0:
                errors.append("offset must be >= 0")
            else:
                validated['offset'] = offset
        except (ValueError, TypeError):
            errors.append("offset must be a valid integer")
    else:
        validated['offset'] = 0
    
    return validated, errors


def validate_near_ath_stocks_params(params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate Near ATH stocks query parameters.

    Args:
        params: Query parameters dict

    Returns:
        Tuple of (validated_params, errors)
    """
    validated = {}
    errors = []

    # Validate max_distance (default: 10.0)
    if 'max_distance' in params:
        try:
            max_distance = float(params['max_distance'])
            if max_distance < 0:
                errors.append("max_distance must be >= 0")
            elif max_distance > 50:
                errors.append("max_distance cannot exceed 50")
            else:
                validated['max_distance'] = max_distance
        except (ValueError, TypeError):
            errors.append("max_distance must be a valid number")
    else:
        validated['max_distance'] = 10.0

    # Validate min_gain (default: 0)
    if 'min_gain' in params:
        try:
            min_gain = float(params['min_gain'])
            if min_gain < 0:
                errors.append("min_gain must be >= 0")
            else:
                validated['min_gain'] = min_gain
        except (ValueError, TypeError):
            errors.append("min_gain must be a valid number")
    else:
        validated['min_gain'] = 0.0

    # Validate market (optional)
    if 'market' in params:
        market = params['market'].upper()
        if market not in ['US', 'BK', 'CC']:
            errors.append("market must be one of: US, BK, CC")
        else:
            validated['market'] = market

    # Validate limit (default: 50, max: 1000)
    if 'limit' in params:
        try:
            limit = int(params['limit'])
            if limit <= 0:
                errors.append("limit must be a positive integer")
            elif limit > 1000:
                errors.append("limit cannot exceed 1000")
            else:
                validated['limit'] = limit
        except (ValueError, TypeError):
            errors.append("limit must be a valid integer")
    else:
        validated['limit'] = 50

    # Validate offset (default: 0)
    if 'offset' in params:
        try:
            offset = int(params['offset'])
            if offset < 0:
                errors.append("offset must be >= 0")
            else:
                validated['offset'] = offset
        except (ValueError, TypeError):
            errors.append("offset must be a valid integer")
    else:
        validated['offset'] = 0

    return validated, errors


def validate_death_cross_params(params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate death cross query parameters.
    
    Args:
        params: Raw query parameters dict
        
    Returns:
        Tuple of (validated_params, errors)
        - validated_params: Dict with validated and type-converted values
        - errors: List of error messages (empty if all valid)
    """
    validated = {}
    errors = []
    
    # Validate market (US, BK, or CC)
    if 'market' in params:
        market = params['market']
        if market not in ['US', 'BK', 'CC']:
            errors.append("market must be one of: US, BK, CC")
        else:
            validated['market'] = market
    
    # Validate date (YYYY-MM-DD format)
    if 'date' in params:
        date_error = validate_date_format(params['date'], 'date')
        if date_error:
            errors.append(date_error)
        else:
            validated['date'] = params['date']
    
    # Validate days (positive integer)
    if 'days' in params:
        try:
            days = int(params['days'])
            if days <= 0:
                errors.append("days must be a positive integer")
            else:
                validated['days'] = days
        except (ValueError, TypeError):
            errors.append("days must be a positive integer")
    
    # Validate limit (optional, positive integer, default: 40)
    if 'limit' in params:
        try:
            limit = int(params['limit'])
            if limit <= 0:
                errors.append("limit must be a positive integer")
            elif limit > 1000:
                errors.append("limit cannot exceed 1000")
            else:
                validated['limit'] = limit
        except (ValueError, TypeError):
            errors.append("limit must be a valid integer")
    else:
        validated['limit'] = 50
    
    # Validate offset (optional, non-negative integer, default: 0)
    if 'offset' in params:
        try:
            offset = int(params['offset'])
            if offset < 0:
                errors.append("offset must be >= 0")
            else:
                validated['offset'] = offset
        except (ValueError, TypeError):
            errors.append("offset must be a valid integer")
    else:
        validated['offset'] = 0
    
    return validated, errors


def validate_stock_price_params(symbol: str, params: Dict[str, Any]) -> Tuple[str, Dict[str, Any], List[str]]:
    """
    Validate stock price query parameters and symbol.
    
    Args:
        symbol: Stock symbol with market code
        params: Raw query parameters dict
        
    Returns:
        Tuple of (validated_symbol, validated_params, errors)
        - validated_symbol: Validated symbol string
        - validated_params: Dict with validated and type-converted values
        - errors: List of error messages (empty if all valid)
    """
    validated = {}
    errors = []
    
    # Validate symbol format (must contain market code suffix)
    validated_symbol = symbol
    if not symbol:
        errors.append("symbol is required")
    elif not re.search(r'\.(US|BK|CC)$', symbol):
        errors.append("symbol must contain a valid market code suffix (.US, .BK, or .CC)")
    
    # Validate symbol contains only valid characters (alphanumeric, dots, hyphens)
    if symbol and not re.match(r'^[A-Za-z0-9.\-]+$', symbol):
        errors.append("symbol contains invalid characters")
    
    # Validate start_date (YYYY-MM-DD format)
    if 'start_date' in params:
        date_error = validate_date_format(params['start_date'], 'start_date')
        if date_error:
            errors.append(date_error)
        else:
            validated['start_date'] = params['start_date']
    
    # Validate end_date (YYYY-MM-DD format)
    if 'end_date' in params:
        date_error = validate_date_format(params['end_date'], 'end_date')
        if date_error:
            errors.append(date_error)
        else:
            validated['end_date'] = params['end_date']
    
    # Validate start_date <= end_date if both provided
    if 'start_date' in validated and 'end_date' in validated:
        if validated['start_date'] > validated['end_date']:
            errors.append("start_date must be less than or equal to end_date")
    
    # Validate limit (positive integer)
    if 'limit' in params:
        try:
            limit = int(params['limit'])
            if limit <= 0:
                errors.append("limit must be a positive integer")
            else:
                validated['limit'] = limit
        except (ValueError, TypeError):
            errors.append("limit must be a positive integer")
    
    return validated_symbol, validated, errors


def validate_openai_summary_params(params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate OpenAI summary query parameters.
    
    Args:
        params: Raw query parameters dict
        
    Returns:
        Tuple of (validated_params, errors)
        - validated_params: Dict with validated and type-converted values
        - errors: List of error messages (empty if all valid)
    """
    validated = {}
    errors = []
    
    # Validate symbol (required)
    if 'symbol' not in params or not params['symbol']:
        errors.append("symbol is required")
    else:
        symbol = params['symbol']
        # Validate symbol format (must contain market code suffix)
        if not re.search(r'\.(US|BK|CC)$', symbol):
            errors.append("symbol must contain a valid market code suffix (.US, .BK, or .CC)")
        elif not re.match(r'^[A-Za-z0-9.\-]+$', symbol):
            errors.append("symbol contains invalid characters")
        else:
            validated['symbol'] = symbol
    
    # Validate analysis_type (optional, default: news)
    valid_analysis_types = ['news', 'technical', 'fundamental', 'all']
    if 'analysis_type' in params:
        analysis_type = params['analysis_type'].lower()
        if analysis_type not in valid_analysis_types:
            errors.append(f"analysis_type must be one of: {', '.join(valid_analysis_types)}")
        else:
            validated['analysis_type'] = analysis_type
    
    # Validate model (optional, default: gpt-4-turbo)
    valid_models = ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo']
    if 'model' in params:
        model = params['model']
        if model not in valid_models:
            errors.append(f"model must be one of: {', '.join(valid_models)}")
        else:
            validated['model'] = model
    
    return validated, errors
