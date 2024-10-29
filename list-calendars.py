#!/usr/bin/env python

import datetime
import calendar
from dateutil import parser
from os.path import exists,join
from os import getenv
from csv import writer, QUOTE_MINIMAL

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

CREDS=getenv('GOOGLE_CREDS_PATH')
TOKEN_PATH = CREDS + ".token.json"

ME=getenv("EMAIL")
PAGE_SZ=50

if ME is None:
   print(
      """
      Missing environment variable $EMAIL, which should be the main 
      participant in calendar entries we're looking for.
      """
      )
   exit(1)

if not exists(CREDS):
  print(f"Missing credentials: {CREDS}")
  exit(1)


def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if exists(TOKEN_PATH):
    print(f"Loading credentials: {TOKEN_PATH}")
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      print("Refreshing token")
      creds.refresh(Request())
    else:
      print(f"Loading installed App Flow: {CREDS}")
      flow = InstalledAppFlow.from_client_secrets_file(
          CREDS, SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(TOKEN_PATH, "w") as token:
      print(f"Writing: {TOKEN_PATH}")
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    cals_result = (
        service.calendarList()
        .list()
        .execute()
    )
    cals = cals_result.get("items", [])

    print(f"Got {len(cals)} so far")

    if not cals:
      print("No events found.")
      return
    
    for cal in cals:
       print(f"{cal['summary']}: {cal['id']}")

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()