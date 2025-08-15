"""Tests for authentication service."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from wallaby.auth import GoogleAuth
from wallaby.config import Config


class TestGoogleAuth:
    """Test Google authentication functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config(
            credentials_path='/test/creds.json',
            email='test@example.com'
        )
        self.auth = GoogleAuth(self.config)
    
    @patch('wallaby.auth.InstalledAppFlow.from_client_secrets_file')
    @patch('os.path.exists')
    @patch('wallaby.auth.Credentials.from_authorized_user_file')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_credentials_existing_valid_token(self, mock_file, mock_from_file, mock_exists, mock_flow):
        """Test loading existing valid credentials."""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.__bool__ = lambda self: True  # Ensure creds evaluates to True
        mock_creds.to_json.return_value = '{"token": "data"}'
        mock_from_file.return_value = mock_creds
        
        with patch('builtins.print') as mock_print:
            result = self.auth.get_credentials()
        
        assert result == mock_creds
        mock_from_file.assert_called_once_with(
            '/test/creds.json.token.json',
            self.config.scopes
        )
        mock_print.assert_called_with('Loading credentials: /test/creds.json.token.json')
        # Should not call the flow since credentials are valid
        mock_flow.assert_not_called()
        # Should not write file since credentials are already valid
        mock_file.assert_not_called()
    
    @patch('wallaby.auth.InstalledAppFlow.from_client_secrets_file')
    @patch('os.path.exists')
    @patch('wallaby.auth.Credentials.from_authorized_user_file')
    @patch('wallaby.auth.Request')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_credentials_expired_token_refresh(self, mock_file, mock_request, mock_from_file, mock_exists, mock_flow):
        """Test refreshing expired credentials."""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = 'refresh_token'
        mock_creds.__bool__ = lambda self: True  # Ensure creds evaluates to True
        mock_creds.to_json.return_value = '{"token": "data"}'
        mock_from_file.return_value = mock_creds
        
        # After refresh, make credentials valid
        def refresh_side_effect(request):
            mock_creds.valid = True
        mock_creds.refresh.side_effect = refresh_side_effect
        
        with patch('builtins.print') as mock_print:
            result = self.auth.get_credentials()
        
        assert result == mock_creds
        mock_creds.refresh.assert_called_once()
        mock_file.assert_called_with('/test/creds.json.token.json', 'w')
        assert 'Refreshing token' in [call.args[0] for call in mock_print.call_args_list]
        # Should not call the flow since refresh worked
        mock_flow.assert_not_called()
    
    @patch('os.path.exists')
    @patch('wallaby.auth.Credentials.from_authorized_user_file')
    @patch('wallaby.auth.InstalledAppFlow.from_client_secrets_file')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_credentials_new_auth_flow(self, mock_file, mock_flow_class, mock_from_file, mock_exists):
        """Test new authentication flow when no valid credentials exist."""
        mock_exists.return_value = False
        mock_flow = MagicMock()
        mock_creds = MagicMock()
        mock_creds.to_json.return_value = '{"token": "data"}'
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_class.return_value = mock_flow
        
        with patch('builtins.print') as mock_print:
            result = self.auth.get_credentials()
        
        assert result == mock_creds
        mock_flow_class.assert_called_once_with('/test/creds.json', self.config.scopes)
        mock_flow.run_local_server.assert_called_once_with(port=0)
        mock_file.assert_called_with('/test/creds.json.token.json', 'w')
        
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any('Loading installed App Flow' in call for call in print_calls)
        assert any('Writing:' in call for call in print_calls)
    
    @patch('os.path.exists')
    @patch('wallaby.auth.Credentials.from_authorized_user_file')
    @patch('wallaby.auth.InstalledAppFlow.from_client_secrets_file')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_credentials_invalid_no_refresh_token(self, mock_file, mock_flow_class, mock_from_file, mock_exists):
        """Test new auth flow when credentials exist but are invalid and have no refresh token."""
        mock_exists.return_value = True
        mock_existing_creds = MagicMock()
        mock_existing_creds.valid = False
        mock_existing_creds.expired = True
        mock_existing_creds.refresh_token = None
        mock_from_file.return_value = mock_existing_creds
        
        mock_flow = MagicMock()
        mock_new_creds = MagicMock()
        mock_new_creds.to_json.return_value = '{"token": "data"}'
        mock_flow.run_local_server.return_value = mock_new_creds
        mock_flow_class.return_value = mock_flow
        
        with patch('builtins.print'):
            result = self.auth.get_credentials()
        
        assert result == mock_new_creds
        mock_flow_class.assert_called_once_with('/test/creds.json', self.config.scopes)
        mock_flow.run_local_server.assert_called_once_with(port=0)
