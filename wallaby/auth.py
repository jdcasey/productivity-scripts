"""Google OAuth authentication service."""

from os.path import exists
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from .config import Config


class GoogleAuth:
    """Handles Google OAuth authentication flow."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def get_credentials(self) -> Credentials:
        """
        Get authenticated Google API credentials.
        
        Returns:
            Credentials: Authenticated Google API credentials
        """
        creds = None
        
        # Load existing token if available
        if exists(self.config.token_path):
            print(f"Loading credentials: {self.config.token_path}")
            creds = Credentials.from_authorized_user_file(
                self.config.token_path, 
                self.config.scopes
            )
        
        # Refresh or get new credentials if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing token")
                creds.refresh(Request())
            else:
                print(f"Loading installed App Flow: {self.config.credentials_path}")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.credentials_path, 
                    self.config.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.config.token_path, "w") as token:
                print(f"Writing: {self.config.token_path}")
                token.write(creds.to_json())
        
        return creds
