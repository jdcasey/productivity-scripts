"""Integration tests for CLI functionality."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from wallaby.cli import list_calendars, list_events


class TestListCalendarsIntegration:
    """Integration tests for list_calendars CLI."""
    
    @patch.dict('os.environ', {
        'GOOGLE_CREDS_PATH': '/test/creds.json',
        'EMAIL': 'test@example.com'
    })
    @patch('wallaby.auth.InstalledAppFlow.from_client_secrets_file')
    @patch('wallaby.config.exists')
    @patch('wallaby.auth.Credentials.from_authorized_user_file')
    @patch('wallaby.calendar_client.build')
    def test_list_calendars_end_to_end(self, mock_build, mock_from_file, mock_exists, mock_flow):
        """Test complete list_calendars workflow."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock credentials
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_from_file.return_value = mock_creds
        
        # Mock Google API service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Mock calendar data
        test_calendars = [
            {'id': 'primary', 'summary': 'Primary Calendar'},
            {'id': 'work@example.com', 'summary': 'Work Calendar'}
        ]
        mock_service.calendarList().list().execute.return_value = {
            'items': test_calendars
        }
        
        with patch('builtins.print') as mock_print:
            list_calendars.main()
        
        # Verify the expected output
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert 'Loading credentials: /test/creds.json.token.json' in print_calls
        assert 'Got 2 calendars' in print_calls
        assert 'Primary Calendar: primary' in print_calls
        assert 'Work Calendar: work@example.com' in print_calls
    
    @patch.dict('os.environ', {
        'GOOGLE_CREDS_PATH': '/test/creds.json',
        'EMAIL': 'test@example.com'
    })
    @patch('wallaby.auth.InstalledAppFlow.from_client_secrets_file')
    @patch('wallaby.config.exists')
    @patch('wallaby.auth.Credentials.from_authorized_user_file')
    @patch('wallaby.calendar_client.build')
    def test_list_calendars_no_calendars(self, mock_build, mock_from_file, mock_exists, mock_flow):
        """Test list_calendars with no calendars found."""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_from_file.return_value = mock_creds
        
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.calendarList().list().execute.return_value = {}
        
        with patch('builtins.print') as mock_print:
            list_calendars.main()
        
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert 'Got 0 calendars' in print_calls
        assert 'No calendars found.' in print_calls


class TestListEventsIntegration:
    """Integration tests for list_events CLI."""
    
    @patch.dict('os.environ', {
        'GOOGLE_CREDS_PATH': '/test/creds.json',
        'EMAIL': 'test@example.com'
    })
    @patch('wallaby.auth.InstalledAppFlow.from_client_secrets_file')
    @patch('wallaby.config.exists')
    @patch('wallaby.auth.Credentials.from_authorized_user_file')
    @patch('wallaby.calendar_client.build')
    @patch('builtins.open', new_callable=mock_open)
    def test_list_events_end_to_end(self, mock_file, mock_build, mock_from_file, mock_exists, mock_flow):
        """Test complete list_events workflow."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock credentials
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_from_file.return_value = mock_creds
        
        # Mock Google API service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Mock event data - realistic meeting structure
        test_events = [
            {
                'id': 'event1',
                'summary': 'Team Meeting',
                'start': {'dateTime': '2024-01-15T10:00:00-05:00'},
                'end': {'dateTime': '2024-01-15T11:00:00-05:00'},
                'creator': {'email': 'manager@example.com', 'displayName': 'Manager'},
                'attendees': [
                    {'email': 'test@example.com', 'responseStatus': 'accepted'},
                    {'email': 'colleague@example.com', 'responseStatus': 'accepted'}
                ]
            },
            {
                'id': 'event2',
                'summary': 'Project Review',
                'start': {'dateTime': '2024-01-15T14:00:00-05:00'},
                'end': {'dateTime': '2024-01-15T15:30:00-05:00'},
                'creator': {'email': 'pm@example.com', 'displayName': 'Project Manager'},
                'attendees': [
                    {'email': 'test@example.com', 'responseStatus': 'accepted'},
                    {'email': 'stakeholder@example.com', 'responseStatus': 'accepted'}
                ]
            }
        ]
        
        mock_service.events().list().execute.return_value = {
            'items': test_events
        }
        
        with patch('builtins.print') as mock_print:
            list_events.main()
        
        # Verify CSV files were created
        assert mock_file.call_count >= 2  # meetings.csv and stats.csv
        
        # Verify expected print output
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any('Getting events between:' in call for call in print_calls)
        assert any('Got 2 events so far' in call for call in print_calls)
        assert any('Team Meeting' in call for call in print_calls)
        assert any('Project Review' in call for call in print_calls)
        assert any('2 total events written to meetings.csv' in call for call in print_calls)
    
    @patch.dict('os.environ', {
        'GOOGLE_CREDS_PATH': '/test/creds.json',
        'EMAIL': 'test@example.com'
    })
    @patch('wallaby.auth.InstalledAppFlow.from_client_secrets_file')
    @patch('wallaby.config.exists')
    @patch('wallaby.auth.Credentials.from_authorized_user_file')
    @patch('wallaby.calendar_client.build')
    def test_list_events_no_events(self, mock_build, mock_from_file, mock_exists, mock_flow):
        """Test list_events with no events found."""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_from_file.return_value = mock_creds
        
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.events().list().execute.return_value = {}
        
        with patch('builtins.print') as mock_print:
            list_events.main()
        
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert 'Got 0 events so far' in print_calls
        assert 'No events found.' in print_calls
    
    def test_get_date_range_default(self):
        """Test date range calculation with default parameters."""
        with patch('datetime.datetime') as mock_datetime:
            # Mock current time: 2024-01-15
            mock_now = MagicMock()
            mock_now.year = 2024
            mock_now.month = 1
            mock_now.replace.side_effect = lambda **kwargs: MagicMock(
                isoformat=lambda: f"{kwargs.get('year', 2024)}-{kwargs.get('month', 1):02d}-{kwargs.get('day', 1):02d}T{kwargs.get('hour', 0):02d}:{kwargs.get('minute', 0):02d}:{kwargs.get('second', 0):02d}Z"
            )
            mock_datetime.now.return_value = mock_now
            
            with patch('calendar.monthrange') as mock_monthrange:
                mock_monthrange.return_value = (0, 31)  # January has 31 days
                
                time_min, time_max = list_events.get_date_range()
                
                # Should go back 2 months (3-1) from January to November of previous year
                assert '2023-11-01T00:00:00Z' in time_min
                assert '2024-01-31T23:59:59Z' in time_max
    
    def test_get_date_range_custom_months(self):
        """Test date range calculation with custom month count."""
        with patch('datetime.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.year = 2024
            mock_now.month = 6  # June
            mock_now.replace.side_effect = lambda **kwargs: MagicMock(
                isoformat=lambda: f"{kwargs.get('year', 2024)}-{kwargs.get('month', 6):02d}-{kwargs.get('day', 1):02d}T{kwargs.get('hour', 0):02d}:{kwargs.get('minute', 0):02d}:{kwargs.get('second', 0):02d}Z"
            )
            mock_datetime.now.return_value = mock_now
            
            with patch('calendar.monthrange') as mock_monthrange:
                mock_monthrange.return_value = (0, 30)  # June has 30 days
                
                time_min, time_max = list_events.get_date_range(months=1)
                
                # Should start from current month (no offset for 1 month)
                assert '2024-06-01T00:00:00Z' in time_min
                assert '2024-06-30T23:59:59Z' in time_max
