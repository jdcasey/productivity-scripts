"""Google Calendar API client."""

import datetime
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class CalendarClient:
    """Client for Google Calendar API operations."""
    
    def __init__(self, credentials: Credentials):
        """
        Initialize the calendar client.
        
        Args:
            credentials: Authenticated Google API credentials
        """
        self.service = build("calendar", "v3", credentials=credentials)
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List all calendars available to the user.
        
        Returns:
            List of calendar dictionaries
            
        Raises:
            HttpError: If the API request fails
        """
        try:
            cals_result = self.service.calendarList().list().execute()
            return cals_result.get("items", [])
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise
    
    def get_events(
        self, 
        calendar_id: str,
        time_min: str,
        time_max: str,
        page_size: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get events from a calendar within a time range.
        
        Args:
            calendar_id: ID of the calendar to query
            time_min: Start time in ISO format
            time_max: End time in ISO format  
            page_size: Number of events per page
            
        Returns:
            List of event dictionaries
            
        Raises:
            HttpError: If the API request fails
        """
        try:
            events = []
            page_token = None
            
            while True:
                events_result = (
                    self.service.events()
                    .list(
                        calendarId=calendar_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        maxResults=page_size,
                        singleEvents=True,
                        orderBy="startTime",
                        pageToken=page_token
                    )
                    .execute()
                )
                
                events.extend(events_result.get("items", []))
                print(f"Got {len(events)} events so far")
                
                page_token = events_result.get('nextPageToken', None)
                if page_token is None:
                    break
                else:
                    print(f"Grabbing next results (up to {page_size} more)")
            
            return events
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise
