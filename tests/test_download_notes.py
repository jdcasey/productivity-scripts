"""Tests for download_notes CLI module."""

import datetime
import pytest
from unittest.mock import patch, MagicMock
from freezegun import freeze_time

from wallaby.cli.download_notes import (
    get_date_range,
    sanitize_filename,
    get_attendance_status,
    get_file_extension,
    format_event_data
)


class TestGetDateRange:
    """Test date range calculation functionality."""
    
    @freeze_time("2024-01-15 12:00:00")
    def test_get_date_range_default_3_months(self):
        """Test date range calculation for default 3 months."""
        time_min, time_max = get_date_range()
        
        # Should go back to November 1st, 2023
        assert time_min.startswith("2023-11-01T00:00:00")
        # Should end on January 31st, 2024
        assert time_max.startswith("2024-01-31T23:59:59")
    
    @freeze_time("2024-01-15 12:00:00")
    def test_get_date_range_single_month(self):
        """Test date range calculation for single month."""
        time_min, time_max = get_date_range(months=1)
        
        # Should start on January 1st, 2024
        assert time_min.startswith("2024-01-01T00:00:00")
        # Should end on January 31st, 2024
        assert time_max.startswith("2024-01-31T23:59:59")
    
    @freeze_time("2024-03-15 12:00:00")
    def test_get_date_range_6_months(self):
        """Test date range calculation for 6 months."""
        time_min, time_max = get_date_range(months=6)
        
        # Should go back to August 1st, 2023 (6 months back from March)
        assert time_min.startswith("2023-08-01T00:00:00")
        # Should end on March 31st, 2024
        assert time_max.startswith("2024-03-31T23:59:59")
    
    @freeze_time("2024-02-15 12:00:00")
    def test_get_date_range_cross_year_boundary(self):
        """Test date range calculation that crosses year boundary."""
        time_min, time_max = get_date_range(months=6)
        
        # Should go back to August 1st, 2023 (6 months back from February)
        assert time_min.startswith("2023-08-01T00:00:00")
        # Should end on February 29th, 2024 (leap year)
        assert time_max.startswith("2024-02-29T23:59:59")


class TestSanitizeFilename:
    """Test filename sanitization functionality."""
    
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        result = sanitize_filename("Simple Meeting")
        assert result == "Simple Meeting"
    
    def test_sanitize_filename_invalid_characters(self):
        """Test sanitization of invalid filesystem characters."""
        result = sanitize_filename("Meeting: Q4/Review <Important>")
        assert result == "Meeting_ Q4_Review _Important_"
    
    def test_sanitize_filename_special_characters(self):
        """Test sanitization of special characters."""
        result = sanitize_filename('File"with|bad*chars?')
        assert result == "File_with_bad_chars_"
    
    def test_sanitize_filename_newlines_and_tabs(self):
        """Test sanitization of newlines and tabs."""
        result = sanitize_filename("Meeting\nwith\ttabs\rand\rreturns")
        assert result == "Meeting_with_tabs_and_returns"
    
    def test_sanitize_filename_long_name(self):
        """Test sanitization of very long filenames."""
        long_name = "A" * 250
        result = sanitize_filename(long_name)
        assert len(result) == 200
        assert result == "A" * 200
    
    def test_sanitize_filename_trailing_dots_spaces(self):
        """Test removal of trailing dots and spaces."""
        result = sanitize_filename("Meeting Name... ")
        assert result == "Meeting Name"
    
    def test_sanitize_filename_empty_string(self):
        """Test handling of empty string."""
        result = sanitize_filename("")
        assert result == ""


class TestGetAttendanceStatus:
    """Test attendance status determination functionality."""
    
    def test_get_attendance_status_accepted(self):
        """Test attendance status for accepted events."""
        event = {
            "attendees": [
                {"email": "user@example.com", "responseStatus": "accepted"},
                {"email": "other@example.com", "responseStatus": "declined"}
            ]
        }
        status = get_attendance_status(event, "user@example.com")
        assert status == "attended"
    
    def test_get_attendance_status_declined(self):
        """Test attendance status for declined events."""
        event = {
            "attendees": [
                {"email": "user@example.com", "responseStatus": "declined"},
                {"email": "other@example.com", "responseStatus": "accepted"}
            ]
        }
        status = get_attendance_status(event, "user@example.com")
        assert status == "rejected"
    
    def test_get_attendance_status_needs_action(self):
        """Test attendance status for events needing action."""
        event = {
            "attendees": [
                {"email": "user@example.com", "responseStatus": "needsAction"},
                {"email": "other@example.com", "responseStatus": "accepted"}
            ]
        }
        status = get_attendance_status(event, "user@example.com")
        assert status == "unacknowledged"
    
    def test_get_attendance_status_tentative(self):
        """Test attendance status for tentative responses."""
        event = {
            "attendees": [
                {"email": "user@example.com", "responseStatus": "tentative"},
                {"email": "other@example.com", "responseStatus": "accepted"}
            ]
        }
        status = get_attendance_status(event, "user@example.com")
        assert status == "unacknowledged"
    
    def test_get_attendance_status_no_response_status(self):
        """Test attendance status when no responseStatus is present."""
        event = {
            "attendees": [
                {"email": "user@example.com"},
                {"email": "other@example.com", "responseStatus": "accepted"}
            ]
        }
        status = get_attendance_status(event, "user@example.com")
        assert status == "unacknowledged"
    
    def test_get_attendance_status_not_in_attendees(self):
        """Test attendance status when user is not in attendees list."""
        event = {
            "attendees": [
                {"email": "other1@example.com", "responseStatus": "accepted"},
                {"email": "other2@example.com", "responseStatus": "declined"}
            ]
        }
        status = get_attendance_status(event, "user@example.com")
        assert status == "unacknowledged"
    
    def test_get_attendance_status_no_attendees(self):
        """Test attendance status when event has no attendees."""
        event = {}
        status = get_attendance_status(event, "user@example.com")
        assert status == "unacknowledged"
    
    def test_get_attendance_status_case_insensitive_email(self):
        """Test attendance status with case-insensitive email matching."""
        event = {
            "attendees": [
                {"email": "USER@EXAMPLE.COM", "responseStatus": "accepted"}
            ]
        }
        status = get_attendance_status(event, "user@example.com")
        assert status == "attended"


class TestGetFileExtension:
    """Test file extension determination functionality."""
    
    def test_get_file_extension_dict(self):
        """Test file extension for dictionary data."""
        event = {"id": "test", "summary": "Test Event"}
        extension = get_file_extension(event)
        assert extension == '.yaml'
    
    def test_get_file_extension_other_type(self):
        """Test file extension for non-dictionary data."""
        event = "some string data"
        extension = get_file_extension(event)
        assert extension == '.json'


class TestFormatEventData:
    """Test native event data formatting functionality."""
    
    def test_format_event_data_basic_dict(self):
        """Test basic dictionary formatting as YAML."""
        event = {
            "id": "test-event-123",
            "summary": "Test Meeting",
            "description": "This is a test meeting",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"}
        }
        
        formatted = format_event_data(event)
        
        # Should be YAML format
        assert "id: test-event-123" in formatted
        assert "summary: Test Meeting" in formatted
        assert "description: This is a test meeting" in formatted
        assert "start:" in formatted
        assert "dateTime: '2024-01-15T10:00:00Z'" in formatted
        assert "end:" in formatted
    
    def test_format_event_data_with_special_characters(self):
        """Test formatting with special characters and unicode."""
        event = {
            "id": "special-chars",
            "summary": "Meeting with 🎉 emojis and special chars: àéîôü",
            "description": "This has\nnewlines and \"quotes\" and 'apostrophes'"
        }
        
        formatted = format_event_data(event)
        
        assert "🎉" in formatted
        assert "àéîôü" in formatted
        assert "newlines" in formatted
        assert "quotes" in formatted
        assert "apostrophes" in formatted
    
    def test_format_event_data_complex_structure(self):
        """Test formatting with complex nested structures."""
        event = {
            "id": "complex-event",
            "summary": "Team Meeting",
            "attendees": [
                {
                    "email": "attendee1@example.com",
                    "displayName": "John Doe",
                    "responseStatus": "accepted"
                },
                {
                    "email": "attendee2@example.com",
                    "displayName": "Jane Smith",
                    "responseStatus": "declined"
                }
            ],
            "organizer": {
                "email": "organizer@example.com",
                "displayName": "Meeting Organizer"
            }
        }
        
        formatted = format_event_data(event)
        
        assert "attendees:" in formatted
        assert "John Doe" in formatted
        assert "Jane Smith" in formatted
        assert "accepted" in formatted
        assert "declined" in formatted
        assert "organizer:" in formatted
        assert "Meeting Organizer" in formatted
    
    def test_format_event_data_preserves_all_fields(self):
        """Test that all event fields are preserved in output."""
        event = {
            "kind": "calendar#event",
            "etag": "\"3123456789012345\"",
            "id": "test123",
            "status": "confirmed",
            "htmlLink": "https://www.google.com/calendar/event?eid=test123",
            "created": "2024-01-10T09:00:00.000Z",
            "updated": "2024-01-12T15:30:00.000Z",
            "summary": "Test Event",
            "description": "Event description",
            "location": "Conference Room A",
            "creator": {
                "email": "creator@example.com",
                "displayName": "Event Creator"
            },
            "organizer": {
                "email": "organizer@example.com",
                "displayName": "Event Organizer"
            },
            "start": {
                "dateTime": "2024-01-15T10:00:00-08:00",
                "timeZone": "America/Los_Angeles"
            },
            "end": {
                "dateTime": "2024-01-15T11:00:00-08:00",
                "timeZone": "America/Los_Angeles"
            },
            "iCalUID": "test123@google.com",
            "sequence": 0,
            "attendees": [
                {
                    "email": "attendee@example.com",
                    "displayName": "Attendee Name",
                    "responseStatus": "accepted"
                }
            ],
            "reminders": {
                "useDefault": True
            }
        }
        
        formatted = format_event_data(event)
        
        # Check that all major fields are present
        assert "kind: calendar#event" in formatted
        assert "etag:" in formatted
        assert "status: confirmed" in formatted
        assert "htmlLink:" in formatted
        assert "created:" in formatted
        assert "updated:" in formatted
        assert "creator:" in formatted
        assert "iCalUID:" in formatted
        assert "sequence:" in formatted
        assert "reminders:" in formatted
        assert "useDefault:" in formatted
    
    def test_format_event_data_minimal_event(self):
        """Test formatting with minimal event data."""
        event = {
            "id": "minimal-event"
        }
        
        formatted = format_event_data(event)
        
        assert "id: minimal-event" in formatted


class TestIntegrationScenarios:
    """Test integration scenarios that combine multiple functions."""
    
    def test_filename_from_event_title(self):
        """Test creating a safe filename from an event title."""
        event_title = "Q4 Planning: Budget/Review <URGENT>"
        event = {"summary": event_title}
        
        sanitized = sanitize_filename(event_title)
        extension = get_file_extension(event)
        
        assert "/" not in sanitized
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert sanitized == "Q4 Planning_ Budget_Review _URGENT_"
        assert extension == ".yaml"
    
    def test_attendance_status_workflow(self):
        """Test the complete attendance status determination workflow."""
        events = [
            {
                "summary": "Accepted Meeting",
                "attendees": [
                    {"email": "user@example.com", "responseStatus": "accepted"}
                ]
            },
            {
                "summary": "Declined Meeting", 
                "attendees": [
                    {"email": "user@example.com", "responseStatus": "declined"}
                ]
            },
            {
                "summary": "Pending Meeting",
                "attendees": [
                    {"email": "user@example.com", "responseStatus": "needsAction"}
                ]
            },
            {
                "summary": "No Response Meeting",
                "attendees": [
                    {"email": "other@example.com", "responseStatus": "accepted"}
                ]
            }
        ]
        
        user_email = "user@example.com"
        
        statuses = [get_attendance_status(event, user_email) for event in events]
        
        assert statuses == ["attended", "rejected", "unacknowledged", "unacknowledged"]
    
    @freeze_time("2024-06-15 12:00:00")
    def test_date_range_edge_cases(self):
        """Test date range calculation edge cases."""
        # Test February in leap year
        with freeze_time("2024-02-15 12:00:00"):
            time_min, time_max = get_date_range(months=1)
            assert "2024-02-01" in time_min
            assert "2024-02-29" in time_max  # Leap year
        
        # Test February in non-leap year  
        with freeze_time("2023-02-15 12:00:00"):
            time_min, time_max = get_date_range(months=1)
            assert "2023-02-01" in time_min
            assert "2023-02-28" in time_max  # Non-leap year
        
        # Test December to January transition
        with freeze_time("2024-01-15 12:00:00"):
            time_min, time_max = get_date_range(months=2)
            assert "2023-12-01" in time_min
            assert "2024-01-31" in time_max
