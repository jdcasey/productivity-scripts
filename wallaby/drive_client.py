"""Google Drive API client for downloading documents."""

from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import io
from pathlib import Path

DOWNLOAD_CHUNK_SIZE = 10 * 1024 * 1024


class DriveClient:
    """Client for Google Drive API operations."""
    
    def __init__(self, credentials: Credentials):
        """
        Initialize the Drive client.
        
        Args:
            credentials: Authenticated Google API credentials
        """
        self.service = build("drive", "v3", credentials=credentials)
    
    def download_document_as_text(self, file_id: str, output_path: str) -> bool:
        """
        Download a Google Doc as plain text and stream it to a file.
        
        Args:
            file_id: Google Drive file ID
            output_path: Path where the content should be saved
            
        Returns:
            True if download was successful, False otherwise
        """
        try:
            # Export Google Doc as plain text
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType='text/plain'
            )
            
            # Create the output file and stream content directly to it
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Stream download directly to file
            with open(output_file, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request, chunksize=DOWNLOAD_CHUNK_SIZE)
                
                done = False
                while done is False:
                    _status, done = downloader.next_chunk()
            
            return True
            
        except HttpError as error:
            print(f"Error downloading file {file_id}: {error}")
            return False
        except Exception as error:
            print(f"Unexpected error downloading file {file_id}: {error}")
            return False
    

    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a file.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File metadata dictionary, or None if retrieval fails
        """
        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,createdTime,modifiedTime,size,owners'
            ).execute()
            return file_metadata
            
        except HttpError as error:
            print(f"Error getting metadata for file {file_id}: {error}")
            return None
    
    def is_gemini_note(self, attachment: Dict[str, Any]) -> bool:
        """
        Check if an attachment is a Gemini-generated note.
        
        Args:
            attachment: Attachment dictionary from calendar event
            
        Returns:
            True if this appears to be a Gemini note
        """
        title = attachment.get('title', '').lower()
        mime_type = attachment.get('mimeType', '')
        
        # Check for Gemini indicators in the title
        gemini_indicators = [
            'notes by gemini',
            'gemini notes',
            'by gemini'
        ]
        
        # Must be a Google Doc
        is_google_doc = mime_type == 'application/vnd.google-apps.document'
        
        # Check if title contains Gemini indicators
        has_gemini_indicator = any(indicator in title for indicator in gemini_indicators)
        
        return is_google_doc and has_gemini_indicator
