#!/usr/bin/env python
"""List available Google calendars."""

from wallaby.config import Config
from wallaby.auth import GoogleAuth
from wallaby.calendar_client import CalendarClient


def main():
    """List all available Google calendars."""
    # Initialize configuration and validate
    config = Config()
    config.validate()
    
    # Authenticate and create calendar client
    auth = GoogleAuth(config)
    credentials = auth.get_credentials()
    client = CalendarClient(credentials)
    
    # Get and display calendars
    calendars = client.list_calendars()
    
    print(f"Got {len(calendars)} calendars")
    
    if not calendars:
        print("No calendars found.")
        return
    
    for cal in calendars:
        print(f"{cal['summary']}: {cal['id']}")


if __name__ == "__main__":
    main()
