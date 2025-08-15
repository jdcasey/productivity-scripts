"""Configuration management for work-life balance tools."""

import os
from dataclasses import dataclass, field
from typing import List
from os.path import exists


@dataclass
class Config:
    """Configuration for Google Calendar integration."""
    
    credentials_path: str = None
    email: str = None
    page_size: int = 50
    scopes: List[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ])
    
    def __post_init__(self):
        """Initialize configuration from environment variables."""
        if self.credentials_path is None:
            self.credentials_path = os.getenv('GOOGLE_CREDS_PATH')
        if self.email is None:
            self.email = os.getenv('EMAIL')
    
    @property
    def token_path(self) -> str:
        """Path to the OAuth token file."""
        return f"{self.credentials_path}.token.json"
    
    def validate(self) -> None:
        """Validate configuration and exit if invalid."""
        if self.email is None:
            print("""
            Missing environment variable $EMAIL, which should be the main 
            participant in calendar entries we're looking for.
            """)
            exit(1)
        
        if not exists(self.credentials_path):
            print(f"Missing credentials: {self.credentials_path}")
            exit(1)
