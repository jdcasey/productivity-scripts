#!/usr/bin/env python
"""Main CLI entry point for work-life balance tools."""

import argparse
import sys
from typing import List, Optional

from .list_calendars import main as list_calendars_main
from .list_events import main as list_events_main
from .download_notes import main as download_notes_main


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with sub-commands."""
    parser = argparse.ArgumentParser(
        prog="wlb",
        description="Work-Life Balance: Tools for managing calendar data and productivity insights"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND"
    )
    
    # List calendars sub-command
    list_calendars_parser = subparsers.add_parser(
        "list-calendars",
        help="List all available Google calendars",
        description="Display all Google calendars accessible with current credentials"
    )
    
    # List events sub-command
    list_events_parser = subparsers.add_parser(
        "list-events", 
        help="List and analyze calendar events",
        description="Extract calendar events and export analysis to CSV files"
    )
    list_events_parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Number of months to look back from current month (default: 3)"
    )
    list_events_parser.add_argument(
        "--output",
        default="meetings.csv",
        help="Output CSV filename for events (default: meetings.csv)"
    )
    
    # Download notes sub-command
    download_notes_parser = subparsers.add_parser(
        "download-notes",
        help="Download calendar events in native format organized by attendance",
        description="Save calendar events in native format (YAML/JSON) organized by attendance status and date"
    )
    download_notes_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back from current day (default: 30)"
    )
    download_notes_parser.add_argument(
        "--output-dir",
        default="calendar_events",
        help="Output directory for event files (default: calendar_events)"
    )
    
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """
    Main CLI entry point.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if not parsed_args.command:
        parser.print_help()
        return 1
    
    try:
        if parsed_args.command == "list-calendars":
            list_calendars_main()
        elif parsed_args.command == "list-events":
            list_events_main(
                months=parsed_args.months,
                output=parsed_args.output
            )
        elif parsed_args.command == "download-notes":
            download_notes_main(
                days=parsed_args.days,
                output_dir=parsed_args.output_dir
            )
        else:
            print(f"Unknown command: {parsed_args.command}", file=sys.stderr)
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
