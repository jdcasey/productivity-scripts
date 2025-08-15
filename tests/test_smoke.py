"""Smoke tests to verify basic functionality of refactored code."""

import pytest
from unittest.mock import patch, MagicMock
from wallaby.config import Config
from wallaby.auth import GoogleAuth
from wallaby.calendar_client import CalendarClient


class TestSmokeTests:
    """Basic smoke tests to verify the refactored structure works."""
    
    def test_config_can_be_created(self):
        """Test that Config can be instantiated."""
        config = Config(
            credentials_path='/test/path.json',
            email='test@example.com'
        )
        assert config.credentials_path == '/test/path.json'
        assert config.email == 'test@example.com'
        assert config.token_path == '/test/path.json.token.json'
    
    def test_auth_can_be_created(self):
        """Test that GoogleAuth can be instantiated."""
        config = Config(
            credentials_path='/test/path.json',
            email='test@example.com'
        )
        auth = GoogleAuth(config)
        assert auth.config == config
    
    def test_calendar_client_can_be_created(self):
        """Test that CalendarClient can be instantiated."""
        mock_creds = MagicMock()
        
        with patch('wallaby.calendar_client.build') as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            
            client = CalendarClient(mock_creds)
            assert client.service == mock_service
            mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds)
    
    def test_imports_work(self):
        """Test that all modules can be imported without errors."""
        from wallaby.cli import list_calendars, list_events
        from wallaby import config, auth, calendar_client
        
        # If we get here without exceptions, imports work
        assert True
    
    def test_original_scripts_exist(self):
        """Test that the original script functionality is preserved."""
        import os
        
        # Check that wrapper scripts exist
        assert os.path.exists('list-calendars-new.py')
        assert os.path.exists('list-calendar-events-new.py')
        
        # Check that CLI modules exist
        from wallaby.cli import list_calendars, list_events
        
        # Check that main functions exist
        assert hasattr(list_calendars, 'main')
        assert hasattr(list_events, 'main')
        assert callable(list_calendars.main)
        assert callable(list_events.main)
