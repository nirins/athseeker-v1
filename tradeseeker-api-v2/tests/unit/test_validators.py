"""Unit tests for validators module."""

import pytest
from src.validators import (
    validate_date_format,
    validate_golden_cross_params,
    validate_stock_price_params,
    validate_openai_summary_params
)


class TestDateFormatValidation:
    """Tests for date format validation."""
    
    def test_valid_date(self):
        """Test valid date format."""
        error = validate_date_format('2024-01-15', 'date')
        assert error is None
    
    def test_invalid_format(self):
        """Test invalid date format."""
        error = validate_date_format('01-15-2024', 'date')
        assert error == "date must be in YYYY-MM-DD format"
    
    def test_invalid_date(self):
        """Test invalid date values."""
        error = validate_date_format('2024-02-30', 'date')
        assert error == "date is not a valid date"
    
    def test_empty_date(self):
        """Test empty date string."""
        error = validate_date_format('', 'date')
        assert error is None


class TestGoldenCrossParamsValidation:
    """Tests for golden cross parameter validation."""
    
    def test_default_values(self):
        """Test default values are applied."""
        validated, errors = validate_golden_cross_params({})
        assert errors == []
        assert validated['min_green'] == 70
        assert validated['max_red_candle'] == -8
    
    def test_valid_min_green(self):
        """Test valid min_green parameter."""
        validated, errors = validate_golden_cross_params({'min_green': '50'})
        assert errors == []
        assert validated['min_green'] == 50.0
    
    def test_invalid_min_green_range(self):
        """Test min_green out of range."""
        validated, errors = validate_golden_cross_params({'min_green': '150'})
        assert "min_green must be between 0 and 100" in errors
    
    def test_invalid_min_green_type(self):
        """Test min_green with invalid type."""
        validated, errors = validate_golden_cross_params({'min_green': 'abc'})
        assert "min_green must be a valid number" in errors
    
    def test_valid_max_red_candle(self):
        """Test valid max_red_candle parameter."""
        validated, errors = validate_golden_cross_params({'max_red_candle': '-10'})
        assert errors == []
        assert validated['max_red_candle'] == -10.0
    
    def test_invalid_max_red_candle_range(self):
        """Test max_red_candle out of range."""
        validated, errors = validate_golden_cross_params({'max_red_candle': '5'})
        assert "max_red_candle must be between -100 and 0" in errors
    
    def test_valid_market(self):
        """Test valid market parameter."""
        validated, errors = validate_golden_cross_params({'market': 'US'})
        assert errors == []
        assert validated['market'] == 'US'
    
    def test_invalid_market(self):
        """Test invalid market parameter."""
        validated, errors = validate_golden_cross_params({'market': 'JP'})
        assert "market must be one of: US, BK, CC" in errors
    
    def test_valid_date(self):
        """Test valid date parameter."""
        validated, errors = validate_golden_cross_params({'date': '2024-01-15'})
        assert errors == []
        assert validated['date'] == '2024-01-15'
    
    def test_invalid_date_format(self):
        """Test invalid date format."""
        validated, errors = validate_golden_cross_params({'date': '01/15/2024'})
        assert "date must be in YYYY-MM-DD format" in errors
    
    def test_valid_days(self):
        """Test valid days parameter."""
        validated, errors = validate_golden_cross_params({'days': '30'})
        assert errors == []
        assert validated['days'] == 30
    
    def test_invalid_days_negative(self):
        """Test negative days parameter."""
        validated, errors = validate_golden_cross_params({'days': '-5'})
        assert "days must be a positive integer" in errors
    
    def test_multiple_errors(self):
        """Test multiple validation errors are accumulated."""
        validated, errors = validate_golden_cross_params({
            'min_green': '150',
            'market': 'JP',
            'days': '-5'
        })
        assert len(errors) == 3
        assert any('min_green' in e for e in errors)
        assert any('market' in e for e in errors)
        assert any('days' in e for e in errors)


class TestStockPriceParamsValidation:
    """Tests for stock price parameter validation."""
    
    def test_valid_symbol(self):
        """Test valid symbol with market code."""
        symbol, validated, errors = validate_stock_price_params('AAPL.US', {})
        assert errors == []
        assert symbol == 'AAPL.US'
    
    def test_invalid_symbol_no_market_code(self):
        """Test symbol without market code."""
        symbol, validated, errors = validate_stock_price_params('AAPL', {})
        assert any("market code suffix" in e for e in errors)
    
    def test_invalid_symbol_characters(self):
        """Test symbol with invalid characters."""
        symbol, validated, errors = validate_stock_price_params('AAPL@US', {})
        assert "symbol contains invalid characters" in errors
    
    def test_empty_symbol(self):
        """Test empty symbol."""
        symbol, validated, errors = validate_stock_price_params('', {})
        assert "symbol is required" in errors
    
    def test_valid_start_date(self):
        """Test valid start_date parameter."""
        symbol, validated, errors = validate_stock_price_params('AAPL.US', {'start_date': '2024-01-01'})
        assert errors == []
        assert validated['start_date'] == '2024-01-01'
    
    def test_valid_end_date(self):
        """Test valid end_date parameter."""
        symbol, validated, errors = validate_stock_price_params('AAPL.US', {'end_date': '2024-12-31'})
        assert errors == []
        assert validated['end_date'] == '2024-12-31'
    
    def test_start_date_after_end_date(self):
        """Test start_date after end_date."""
        symbol, validated, errors = validate_stock_price_params('AAPL.US', {
            'start_date': '2024-12-31',
            'end_date': '2024-01-01'
        })
        assert "start_date must be less than or equal to end_date" in errors
    
    def test_valid_limit(self):
        """Test valid limit parameter."""
        symbol, validated, errors = validate_stock_price_params('AAPL.US', {'limit': '100'})
        assert errors == []
        assert validated['limit'] == 100
    
    def test_invalid_limit_negative(self):
        """Test negative limit parameter."""
        symbol, validated, errors = validate_stock_price_params('AAPL.US', {'limit': '-10'})
        assert "limit must be a positive integer" in errors


class TestOpenAISummaryParamsValidation:
    """Tests for OpenAI summary parameter validation."""
    
    def test_valid_symbol(self):
        """Test valid symbol with market code."""
        validated, errors = validate_openai_summary_params({'symbol': 'AAPL.US'})
        assert errors == []
        assert validated['symbol'] == 'AAPL.US'
    
    def test_missing_symbol(self):
        """Test missing symbol parameter."""
        validated, errors = validate_openai_summary_params({})
        assert "symbol is required" in errors
    
    def test_empty_symbol(self):
        """Test empty symbol parameter."""
        validated, errors = validate_openai_summary_params({'symbol': ''})
        assert "symbol is required" in errors
    
    def test_invalid_symbol_no_market_code(self):
        """Test symbol without market code."""
        validated, errors = validate_openai_summary_params({'symbol': 'AAPL'})
        assert any("market code suffix" in e for e in errors)
    
    def test_invalid_symbol_characters(self):
        """Test symbol with invalid characters."""
        validated, errors = validate_openai_summary_params({'symbol': 'AAPL@US'})
        assert "symbol contains invalid characters" in errors
    
    def test_valid_analysis_type(self):
        """Test valid analysis_type parameter."""
        validated, errors = validate_openai_summary_params({
            'symbol': 'AAPL.US',
            'analysis_type': 'technical'
        })
        assert errors == []
        assert validated['analysis_type'] == 'technical'
    
    def test_invalid_analysis_type(self):
        """Test invalid analysis_type parameter."""
        validated, errors = validate_openai_summary_params({
            'symbol': 'AAPL.US',
            'analysis_type': 'invalid'
        })
        assert "analysis_type must be one of: news, technical, fundamental, all" in errors
    
    def test_case_insensitive_analysis_type(self):
        """Test case insensitive analysis_type parameter."""
        validated, errors = validate_openai_summary_params({
            'symbol': 'AAPL.US',
            'analysis_type': 'TECHNICAL'
        })
        assert errors == []
        assert validated['analysis_type'] == 'technical'
    
    def test_valid_model(self):
        """Test valid model parameter."""
        validated, errors = validate_openai_summary_params({
            'symbol': 'AAPL.US',
            'model': 'gpt-4'
        })
        assert errors == []
        assert validated['model'] == 'gpt-4'
    
    def test_invalid_model(self):
        """Test invalid model parameter."""
        validated, errors = validate_openai_summary_params({
            'symbol': 'AAPL.US',
            'model': 'gpt-5'
        })
        assert "model must be one of: gpt-4, gpt-3.5-turbo, gpt-4-turbo" in errors
    
    def test_multiple_valid_parameters(self):
        """Test multiple valid parameters."""
        validated, errors = validate_openai_summary_params({
            'symbol': 'AAPL.US',
            'analysis_type': 'all',
            'model': 'gpt-4-turbo'
        })
        assert errors == []
        assert validated['symbol'] == 'AAPL.US'
        assert validated['analysis_type'] == 'all'
        assert validated['model'] == 'gpt-4-turbo'
    
    def test_multiple_errors(self):
        """Test multiple validation errors are accumulated."""
        validated, errors = validate_openai_summary_params({
            'symbol': 'INVALID',
            'analysis_type': 'invalid',
            'model': 'gpt-5'
        })
        assert len(errors) == 3
        assert any('market code suffix' in e for e in errors)
        assert any('analysis_type' in e for e in errors)
        assert any('model' in e for e in errors)