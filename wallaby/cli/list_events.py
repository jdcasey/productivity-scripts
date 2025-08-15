#!/usr/bin/env python
"""List and analyze calendar events."""

import datetime
import calendar
from dateutil import parser
from csv import writer, QUOTE_MINIMAL
from typing import Tuple

from wallaby.config import Config
from wallaby.auth import GoogleAuth
from wallaby.calendar_client import CalendarClient


def get_date_range(months: int = 3) -> Tuple[str, str]:
    """
    Calculate date range for event retrieval.
    
    Args:
        months: Number of months to look back from current month
        
    Returns:
        Tuple of (time_min, time_max) in ISO format
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    dayrange = calendar.monthrange(now.year, now.month)
    
    startyear = now.year
    startmonth = now.month
    
    monthoffset = months - 1
    if monthoffset > 0:
        if startmonth <= monthoffset:
            startmonth = 12 - (monthoffset - 1)
            startyear -= 1
        else:
            startmonth = now.month - monthoffset
    
    start = now.replace(year=startyear, month=startmonth, day=1, hour=0, minute=0, second=0)
    end = now.replace(day=dayrange[1], hour=23, minute=59, second=59)
    
    return start.isoformat(), end.isoformat()


def export_events_to_csv(events, user_email, output_file="meetings.csv"):
    """
    Export events to CSV format.
    
    Args:
        events: List of calendar events
        user_email: User's email address for filtering
        output_file: Output CSV filename
    """
    count = 0
    stats = {}
    
    with open(output_file, 'w', newline='') as csvfile:
        cw = writer(csvfile, delimiter='^', quotechar='|', quoting=QUOTE_MINIMAL)
        cw.writerow([
            'Date',
            'Summary', 
            'Duration',
            'Categories',
            'Creator',
            'Accepted Count',
            'Accepted Attendees'
        ])
        
        current = None
        cumulative_time = datetime.timedelta(minutes=0)
        current_count = 0
        
        for event in events:
            if len(event.get('attendees', [])) > 1:
                attendees = [
                    a.get('displayName', a['email']) 
                    for a in event['attendees'] 
                    if a.get('responseStatus') == 'accepted'
                ]
                
                if user_email in attendees:
                    count += 1
                    start = parser.parse(event["start"].get("dateTime"))
                    end = parser.parse(event['end'].get('dateTime'))
                    duration = end - start
                    
                    datestr = start.strftime('%Y-%m-%d')
                    if current is None:
                        current = datestr
                        cumulative_time = duration
                    elif current != datestr:
                        stats[current] = {
                            'time': cumulative_time,
                            'count': current_count
                        }
                        current = datestr
                        cumulative_time = duration
                        current_count = 0
                    else:
                        cumulative_time += duration
                    
                    current_count += 1
                    cw.writerow([
                        datestr,
                        event['summary'],
                        str(duration),
                        'TBD',
                        event['creator'].get('displayName', event['creator']['email']),
                        len(attendees),
                        ", ".join(attendees)
                    ])
                    
                    print(f"{start}: {event['summary']}")
        
        # Don't forget the last day's stats
        if current is not None:
            stats[current] = {
                'time': cumulative_time,
                'count': current_count
            }
    
    # Export daily statistics
    export_stats_to_csv(stats, "stats.csv")
    
    print(f"\n\n{count} total events written to {output_file}. Stats written to stats.csv")


def export_stats_to_csv(stats, output_file="stats.csv"):
    """
    Export daily statistics to CSV.
    
    Args:
        stats: Dictionary of daily statistics
        output_file: Output CSV filename
    """
    with open(output_file, 'w', newline='') as csvfile:
        cw = writer(csvfile, delimiter='^', quotechar='|', quoting=QUOTE_MINIMAL)
        cw.writerow([
            'Date',
            'Cumulative Time',
            'Meeting Count',
        ])
        
        total_time = datetime.timedelta(minutes=0)
        total_count = 0
        
        for day, daystats in stats.items():
            cw.writerow([
                day,
                str(daystats['time']),
                daystats['count']
            ])
            total_time += daystats['time']
            total_count += daystats['count']
        
        if len(stats) > 0:
            cw.writerow([
                'Averages',
                str(datetime.timedelta(seconds=int(total_time.total_seconds() / len(stats)))),
                total_count / len(stats)
            ])


def main(months=3, output="meetings.csv"):
    """
    Analyze calendar events and export to CSV.
    
    Args:
        months: Number of months to look back from current month
        output: Output CSV filename for events
    """
    # Initialize configuration and validate
    config = Config()
    config.validate()
    
    # Authenticate and create calendar client
    auth = GoogleAuth(config)
    credentials = auth.get_credentials()
    client = CalendarClient(credentials)
    
    # Get date range and events
    time_min, time_max = get_date_range(months=months)
    print(f"Getting events between:\n{time_min}\n{time_max}")
    
    events = client.get_events(
        calendar_id="primary",
        time_min=time_min,
        time_max=time_max,
        page_size=config.page_size
    )
    
    if not events:
        print("No events found.")
        return
    
    # Export events to CSV
    export_events_to_csv(events, config.email, output)


if __name__ == "__main__":
    main()
