"""Tests for calendar client."""

import pytest
from unittest.mock import patch, MagicMock
from googleapiclient.errors import HttpError
from wallaby.calendar_client import CalendarClient


class TestCalendarClient:
    """Test Google Calendar client functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_credentials = MagicMock()
        
        # Mock the Google API service
        self.mock_service = MagicMock()
        
        with patch('wallaby.calendar_client.build') as mock_build:
            mock_build.return_value = self.mock_service
            self.client = CalendarClient(self.mock_credentials)
    
    def test_list_calendars_success(self):
        """Test successful calendar listing."""
        expected_calendars = [
            {'id': 'cal1', 'summary': 'Calendar 1'},
            {'id': 'cal2', 'summary': 'Calendar 2'}
        ]
        
        self.mock_service.calendarList().list().execute.return_value = {
            'items': expected_calendars
        }
        
        result = self.client.list_calendars()
        
        assert result == expected_calendars
        self.mock_service.calendarList().list().execute.assert_called_once()
    
    def test_list_calendars_empty_result(self):
        """Test calendar listing with empty result."""
        self.mock_service.calendarList().list().execute.return_value = {}
        
        result = self.client.list_calendars()
        
        assert result == []
    
    def test_list_calendars_http_error(self):
        """Test calendar listing with HTTP error."""
        error = HttpError(resp=MagicMock(), content=b'Error')
        self.mock_service.calendarList().list().execute.side_effect = error
        
        with patch('builtins.print') as mock_print:
            with pytest.raises(HttpError):
                self.client.list_calendars()
        
        mock_print.assert_called_once()
    
    def test_get_events_single_page(self):
        """Test getting events with single page of results."""
        expected_events = [
            {'id': 'event1', 'summary': 'Event 1'},
            {'id': 'event2', 'summary': 'Event 2'}
        ]
        
        self.mock_service.events().list().execute.return_value = {
            'items': expected_events
        }
        
        with patch('builtins.print') as mock_print:
            result = self.client.get_events(
                calendar_id='primary',
                time_min='2024-01-01T00:00:00Z',
                time_max='2024-01-31T23:59:59Z'
            )
        
        assert result == expected_events
        
        # Verify API call parameters - check the call that was made with parameters
        calls = self.mock_service.events().list.call_args_list
        # Find the call with parameters (not the empty call)
        param_call = None
        for call in calls:
            if call.kwargs:  # This call has parameters
                param_call = call
                break
        
        assert param_call is not None
        assert param_call.kwargs == {
            'calendarId': 'primary',
            'timeMin': '2024-01-01T00:00:00Z',
            'timeMax': '2024-01-31T23:59:59Z',
            'maxResults': 50,
            'singleEvents': True,
            'orderBy': 'startTime',
            'pageToken': None
        }
        
        mock_print.assert_called_with('Got 2 events so far')
    
    def test_get_events_multiple_pages(self):
        """Test getting events with pagination."""
        page1_events = [{'id': 'event1', 'summary': 'Event 1'}]
        page2_events = [{'id': 'event2', 'summary': 'Event 2'}]
        
        # Mock two pages of results
        self.mock_service.events().list().execute.side_effect = [
            {
                'items': page1_events,
                'nextPageToken': 'token123'
            },
            {
                'items': page2_events
            }
        ]
        
        with patch('builtins.print') as mock_print:
            result = self.client.get_events(
                calendar_id='primary',
                time_min='2024-01-01T00:00:00Z',
                time_max='2024-01-31T23:59:59Z',
                page_size=25
            )
        
        expected_all_events = page1_events + page2_events
        assert result == expected_all_events
        
        # Verify both API calls were made
        assert self.mock_service.events().list().execute.call_count == 2
        
        # Check print statements
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert 'Got 1 events so far' in print_calls
        assert 'Grabbing next results (up to 25 more)' in print_calls
        assert 'Got 2 events so far' in print_calls
    
    def test_get_events_custom_page_size(self):
        """Test getting events with custom page size."""
        expected_events = [{'id': 'event1', 'summary': 'Event 1'}]
        
        self.mock_service.events().list().execute.return_value = {
            'items': expected_events
        }
        
        with patch('builtins.print'):
            self.client.get_events(
                calendar_id='test-calendar',
                time_min='2024-01-01T00:00:00Z',
                time_max='2024-01-31T23:59:59Z',
                page_size=100
            )
        
        # Verify custom page size was used
        calls = self.mock_service.events().list.call_args_list
        # Find the call with parameters (not the empty call)
        param_call = None
        for call in calls:
            if call.kwargs:  # This call has parameters
                param_call = call
                break
        
        assert param_call is not None
        assert param_call.kwargs == {
            'calendarId': 'test-calendar',
            'timeMin': '2024-01-01T00:00:00Z',
            'timeMax': '2024-01-31T23:59:59Z',
            'maxResults': 100,
            'singleEvents': True,
            'orderBy': 'startTime',
            'pageToken': None
        }
    
    def test_get_events_http_error(self):
        """Test getting events with HTTP error."""
        error = HttpError(resp=MagicMock(), content=b'Error')
        self.mock_service.events().list().execute.side_effect = error
        
        with patch('builtins.print') as mock_print:
            with pytest.raises(HttpError):
                self.client.get_events(
                    calendar_id='primary',
                    time_min='2024-01-01T00:00:00Z',
                    time_max='2024-01-31T23:59:59Z'
                )
        
        mock_print.assert_called_once()
    
    def test_get_events_empty_result(self):
        """Test getting events with empty result."""
        self.mock_service.events().list().execute.return_value = {}
        
        with patch('builtins.print') as mock_print:
            result = self.client.get_events(
                calendar_id='primary',
                time_min='2024-01-01T00:00:00Z',
                time_max='2024-01-31T23:59:59Z'
            )
        
        assert result == []
        mock_print.assert_called_with('Got 0 events so far')
