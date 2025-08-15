#!/usr/bin/env python
"""Download calendar events and save in native format organized by attendance status."""

import datetime
import os
import re
import json
import yaml
from pathlib import Path
from dateutil import parser
from typing import Tuple, Dict, Any, List

from wallaby.config import Config
from wallaby.auth import GoogleAuth
from wallaby.calendar_client import CalendarClient
from wallaby.drive_client import DriveClient


def get_date_range(days: int = 30) -> Tuple[str, str]:
    """
    Calculate date range for event retrieval.
    
    Args:
        days: Number of days to look back from current day
        
    Returns:
        Tuple of (time_min, time_max) in ISO format
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    
    # Start date: go back the specified number of days
    start = now - datetime.timedelta(days=days)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # End date: current day at 23:59:59 (no future events)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return start.isoformat(), end.isoformat()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Args:
        filename: The original filename string
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove or replace other problematic characters
    sanitized = re.sub(r'[\r\n\t]', '_', sanitized)
    # Limit length to avoid filesystem issues
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    # Remove trailing dots and spaces
    sanitized = sanitized.rstrip('. ')
    return sanitized


def get_attendance_status(event: Dict[str, Any], user_email: str) -> str:
    """
    Determine the user's attendance status for an event.
    
    Args:
        event: Calendar event dictionary
        user_email: User's email address
        
    Returns:
        One of: 'attended', 'rejected', 'unacknowledged'
    """
    attendees = event.get('attendees', [])
    
    # Find the user's response status
    for attendee in attendees:
        if attendee.get('email', '').lower() == user_email.lower():
            response_status = attendee.get('responseStatus', 'needsAction')
            if response_status == 'accepted':
                return 'attended'
            elif response_status == 'declined':
                return 'rejected'
            else:  # needsAction, tentative, or other
                return 'unacknowledged'
    
    # If user is not in attendees list, assume unacknowledged
    return 'unacknowledged'


def get_file_extension(event_data: Any) -> str:
    """
    Determine the appropriate file extension based on data type.
    
    Args:
        event_data: The event data (dict or other format)
        
    Returns:
        File extension string ('.yaml' or '.json')
    """
    if isinstance(event_data, dict):
        return '.yaml'
    else:
        return '.json'


def format_event_data(event: Dict[str, Any]) -> str:
    """
    Format event data in its native format (YAML for dicts, JSON otherwise).
    
    Args:
        event: Calendar event dictionary from Google Calendar API
        
    Returns:
        Formatted event data as string
    """
    if isinstance(event, dict):
        # Output as YAML for better readability
        return yaml.dump(event, default_flow_style=False, allow_unicode=True, sort_keys=False)
    else:
        # Fallback to JSON for other types
        return json.dumps(event, indent=2, ensure_ascii=False)


def download_gemini_notes(event: Dict[str, Any], drive_client: DriveClient, event_dir: Path) -> int:
    """
    Download Gemini notes attached to a calendar event.
    
    Args:
        event: Calendar event dictionary
        drive_client: Google Drive API client
        event_dir: Directory to save the notes in
        
    Returns:
        Number of Gemini notes downloaded
    """
    attachments = event.get('attachments', [])
    if not attachments:
        return 0
    
    gemini_notes_downloaded = 0
    
    for i, attachment in enumerate(attachments):
        if drive_client.is_gemini_note(attachment):
            file_id = attachment.get('fileId')
            title = attachment.get('title', f'Gemini_Note_{i}')
            
            if not file_id:
                print(f"  Warning: Gemini note '{title}' missing fileId")
                continue
            
            # Create a safe filename for the Gemini note
            safe_title = sanitize_filename(title)
            gemini_file_path = event_dir / f"{safe_title}.txt"
            
            # Handle duplicate filenames
            counter = 1
            while gemini_file_path.exists():
                name_parts = safe_title.rsplit('.', 1) if '.' in safe_title else [safe_title, '']
                if len(name_parts) == 2:
                    new_name = f"{name_parts[0]}_{counter}.txt"
                else:
                    new_name = f"{safe_title}_{counter}.txt"
                gemini_file_path = event_dir / new_name
                counter += 1
            
            # Download the document content directly to file
            success = drive_client.download_document_as_text(file_id, str(gemini_file_path))
            if success:
                print(f"  Downloaded Gemini note: {gemini_file_path.name}")
                gemini_notes_downloaded += 1
            else:
                print(f"  Failed to download: {title}")
    
    return gemini_notes_downloaded


def save_events_as_native(events: List[Dict[str, Any]], user_email: str, output_dir: str, drive_client: DriveClient = None):
    """
    Save calendar events in native format (YAML/JSON) organized by attendance status and date.
    Also downloads any attached Gemini notes.
    
    Args:
        events: List of calendar events
        user_email: User's email address for determining attendance status
        output_dir: Base output directory path
        drive_client: Google Drive client for downloading attachments (optional)
    """
    output_path = Path(output_dir)
    stats = {'attended': 0, 'rejected': 0, 'unacknowledged': 0}
    gemini_stats = {'attended': 0, 'rejected': 0, 'unacknowledged': 0}
    
    for event in events:
        # Skip events without start time
        if 'start' not in event:
            continue
            
        # Get event date
        if 'dateTime' in event['start']:
            event_date = parser.parse(event['start']['dateTime']).date()
        elif 'date' in event['start']:
            event_date = parser.parse(event['start']['date']).date()
        else:
            continue
            
        # Get attendance status
        attendance_status = get_attendance_status(event, user_email)
        stats[attendance_status] += 1
        
        # Create directory structure: output_dir/attendance_status/YYYY-MM-DD/
        date_str = event_date.strftime('%Y-%m-%d')
        event_dir = output_path / attendance_status / date_str
        event_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename from event title
        event_title = event.get('summary', 'Untitled Event')
        file_extension = get_file_extension(event)
        filename = sanitize_filename(event_title) + file_extension
        
        # Handle duplicate filenames by adding a counter
        file_path = event_dir / filename
        counter = 1
        while file_path.exists():
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                new_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                new_filename = f"{filename}_{counter}"
            file_path = event_dir / new_filename
            counter += 1
        
        # Format event in native format and save
        event_content = format_event_data(event)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(event_content)
        
        print(f"Saved: {attendance_status}/{date_str}/{file_path.name}")
        
        # Download any attached Gemini notes
        if drive_client:
            gemini_count = download_gemini_notes(event, drive_client, event_dir)
            gemini_stats[attendance_status] += gemini_count
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Attended: {stats['attended']} events")
    print(f"  Rejected: {stats['rejected']} events") 
    print(f"  Unacknowledged: {stats['unacknowledged']} events")
    print(f"  Total: {sum(stats.values())} events saved to {output_dir}")
    
    if drive_client:
        total_gemini = sum(gemini_stats.values())
        if total_gemini > 0:
            print(f"\nGemini Notes Downloaded:")
            print(f"  Attended: {gemini_stats['attended']} notes")
            print(f"  Rejected: {gemini_stats['rejected']} notes")
            print(f"  Unacknowledged: {gemini_stats['unacknowledged']} notes")
            print(f"  Total: {total_gemini} Gemini notes downloaded")


def main(days=30, output_dir="calendar_events"):
    """
    Download calendar events and save in native format (YAML/JSON) organized by attendance status.
    Also downloads any attached Gemini notes.
    
    Args:
        days: Number of days to look back from current day
        output_dir: Base output directory for saving event files
    """
    # Initialize configuration and validate
    config = Config()
    config.validate()
    
    # Authenticate and create clients
    auth = GoogleAuth(config)
    credentials = auth.get_credentials()
    calendar_client = CalendarClient(credentials)
    drive_client = DriveClient(credentials)
    
    # Get date range and events
    time_min, time_max = get_date_range(days=days)
    print(f"Getting events between:\n{time_min}\n{time_max}")
    
    events = calendar_client.get_events(
        calendar_id="primary",
        time_min=time_min,
        time_max=time_max,
        page_size=config.page_size
    )
    
    if not events:
        print("No events found.")
        return
    
    # Save events in native format and download Gemini notes
    save_events_as_native(events, config.email, output_dir, drive_client)


if __name__ == "__main__":
    main()
