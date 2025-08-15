"""Tests for configuration management."""

import os
import pytest
from unittest.mock import patch, MagicMock
from wallaby.config import Config


class TestConfig:
    """Test configuration management functionality."""
    
    def test_config_initialization_with_env_vars(self):
        """Test config initializes from environment variables."""
        with patch.dict(os.environ, {
            'GOOGLE_CREDS_PATH': '/path/to/creds.json',
            'EMAIL': 'test@example.com'
        }):
            config = Config()
            assert config.credentials_path == '/path/to/creds.json'
            assert config.email == 'test@example.com'
            assert config.page_size == 50
            assert config.scopes == ["https://www.googleapis.com/auth/calendar.readonly"]
    
    def test_config_initialization_with_parameters(self):
        """Test config can be initialized with explicit parameters."""
        config = Config(
            credentials_path='/custom/path.json',
            email='custom@example.com',
            page_size=100
        )
        assert config.credentials_path == '/custom/path.json'
        assert config.email == 'custom@example.com'
        assert config.page_size == 100
    
    def test_token_path_property(self):
        """Test token path is derived from credentials path."""
        config = Config(credentials_path='/path/to/creds.json')
        assert config.token_path == '/path/to/creds.json.token.json'
    
    def test_validate_missing_email_exits(self):
        """Test validation exits when email is missing."""
        config = Config(credentials_path='/valid/path.json')
        config.email = None
        
        with pytest.raises(SystemExit) as exc_info:
            with patch('builtins.print') as mock_print:
                config.validate()
        
        assert exc_info.value.code == 1
        mock_print.assert_called_once()
    
    @patch('wallaby.config.exists')
    def test_validate_missing_credentials_exits(self, mock_exists):
        """Test validation exits when credentials file doesn't exist."""
        mock_exists.return_value = False
        
        config = Config(
            credentials_path='/nonexistent/path.json',
            email='test@example.com'
        )
        
        with pytest.raises(SystemExit) as exc_info:
            with patch('builtins.print') as mock_print:
                config.validate()
        
        assert exc_info.value.code == 1
        mock_print.assert_called_once()
    
    @patch('wallaby.config.exists')
    def test_validate_success(self, mock_exists):
        """Test validation passes with valid configuration."""
        mock_exists.return_value = True
        
        config = Config(
            credentials_path='/valid/path.json',
            email='test@example.com'
        )
        
        # Should not raise any exception
        config.validate()
        mock_exists.assert_called_once_with('/valid/path.json')
