#!/usr/bin/env python
"""Analyze themes from downloaded meeting notes using Gemini LLM."""

import os
import sys
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from wallaby.config import Config
from wallaby.gemini_client import GeminiClient


def collect_meeting_notes(notes_dir: str, days: int = 30) -> tuple[str, List[str]]:
    """
    Collect meeting notes from the specified directory.
    
    Args:
        notes_dir: Directory containing downloaded notes (typically 'OUT')
        days: Number of days back to include notes from
        
    Returns:
        Tuple of (combined_notes_text, list_of_meeting_titles)
    """
    notes_path = Path(notes_dir)
    attended_path = notes_path / "attended"
    
    if not attended_path.exists():
        raise FileNotFoundError(f"Notes directory not found: {attended_path}")
    
    # Calculate date range
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    
    combined_notes = []
    meeting_titles = []
    
    # Process attended meetings
    for date_dir in sorted(attended_path.iterdir()):
        if not date_dir.is_dir():
            continue
            
        # Parse directory name as date (YYYY-MM-DD format)
        try:
            dir_date = datetime.datetime.strptime(date_dir.name, "%Y-%m-%d")
            if dir_date < cutoff_date:
                continue
        except ValueError:
            # Skip directories that don't match date format
            continue
        
        # Look for Gemini notes files (*.txt files with "Notes by Gemini" in name)
        for notes_file in date_dir.glob("*Notes by Gemini*.txt"):
            try:
                with open(notes_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract meeting title from filename
                title = notes_file.stem.replace(" - Notes by Gemini", "").replace("_", " ")
                meeting_titles.append(f"{date_dir.name}: {title}")
                
                # Add structured note entry
                combined_notes.append(f"""
=== MEETING: {title} ===
DATE: {date_dir.name}
{content}
==========================
""")
            except Exception as e:
                print(f"Warning: Could not read {notes_file}: {e}", file=sys.stderr)
    
    if not combined_notes:
        raise ValueError(f"No meeting notes found in {attended_path} for the last {days} days")
    
    return "\n".join(combined_notes), meeting_titles


def load_profile(profile_path: str) -> str:
    """
    Load the user's profile/context file.
    
    Args:
        profile_path: Path to the about_me.md or similar profile file
        
    Returns:
        Content of the profile file
    """
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Profile file not found: {profile_path}")
    
    with open(profile_path, 'r', encoding='utf-8') as f:
        return f.read()


def save_analysis(analysis: str, output_dir: str, filename: str = None) -> str:
    """
    Save analysis results to the output directory.
    
    Args:
        analysis: The generated analysis text
        output_dir: Directory to save the analysis
        filename: Optional custom filename
        
    Returns:
        Path to the saved file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"theme_analysis_{timestamp}.md"
    
    output_file = output_path / filename
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Meeting Theme Analysis\n\n")
        f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(analysis)
    
    return str(output_file)


def interactive_session(gemini_client: GeminiClient, meeting_notes: str, profile: str, output_dir: str):
    """
    Run an interactive analysis session.
    
    Args:
        gemini_client: Initialized Gemini client
        meeting_notes: Combined meeting notes text
        profile: User profile content
        output_dir: Directory to save outputs
    """
    print("\n=== Interactive Meeting Analysis Session ===")
    print("You can ask questions about your meeting notes or request specific analysis.")
    print("Commands:")
    print("  'themes' - Generate default theme analysis")
    print("  'save <filename>' - Save the last response to a file")
    print("  'quit' or 'exit' - End the session")
    print("  Or just ask any question about your meetings\n")
    
    last_response = None
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            if user_input.lower() == 'themes':
                print("\nGenerating default theme analysis...")
                response = gemini_client.analyze_themes(meeting_notes, profile)
                print(f"\n{response}")
                last_response = response
                
            elif user_input.lower().startswith('save '):
                if last_response is None:
                    print("No response to save. Generate an analysis first.")
                    continue
                    
                filename = user_input[5:].strip()
                if not filename.endswith('.md'):
                    filename += '.md'
                    
                saved_path = save_analysis(last_response, output_dir, filename)
                print(f"Analysis saved to: {saved_path}")
                
            elif user_input.lower() == 'save':
                if last_response is None:
                    print("No response to save. Generate an analysis first.")
                    continue
                    
                saved_path = save_analysis(last_response, output_dir)
                print(f"Analysis saved to: {saved_path}")
                
            else:
                print("\nAnalyzing...")
                response = gemini_client.interactive_analysis(meeting_notes, profile, user_input)
                print(f"\n{response}")
                last_response = response
                
        except KeyboardInterrupt:
            print("\n\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


def main(profile_path: str, notes_dir: str = "OUT", output_dir: str = "analysis", days: int = 30):
    """
    Main function for theme analysis CLI command.
    
    Args:
        profile_path: Path to the user's profile/context file
        notes_dir: Directory containing downloaded notes
        output_dir: Directory to save analysis outputs
        days: Number of days back to include notes from
    """
    config = Config()
    config.validate_gemini()
    
    try:
        # Load user profile
        print(f"Loading profile from: {profile_path}")
        profile = load_profile(profile_path)
        
        # Collect meeting notes
        print(f"Collecting meeting notes from: {notes_dir} (last {days} days)")
        meeting_notes, meeting_titles = collect_meeting_notes(notes_dir, days)
        
        print(f"\nFound {len(meeting_titles)} meetings:")
        for title in meeting_titles:
            print(f"  - {title}")
        
        # Initialize Gemini client
        print(f"\nInitializing Gemini client (model: {config.gemini_model})")
        gemini_client = GeminiClient(config)
        
        # Start interactive session
        interactive_session(gemini_client, meeting_notes, profile, output_dir)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze themes from meeting notes")
    parser.add_argument("profile_path", help="Path to your profile/context file (e.g., about_me.md)")
    parser.add_argument("--notes-dir", default="OUT", help="Directory containing downloaded notes (default: OUT)")
    parser.add_argument("--output-dir", default="analysis", help="Directory to save analysis outputs (default: analysis)")
    parser.add_argument("--days", type=int, default=30, help="Number of days back to include notes (default: 30)")
    
    args = parser.parse_args()
    main(args.profile_path, args.notes_dir, args.output_dir, args.days)
