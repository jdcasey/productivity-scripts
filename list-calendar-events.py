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

# CREDS_PATH = '.config/private-credentials.json'
# TOKEN_PATH = 'token.json'
# CREDS = join(getenv("HOME"), CREDS_PATH)

ME=getenv("EMAIL")
PAGE_SZ=50

if ME is None:
   print("Missing environment variable $EMAIL, which should be the main participant in calendar entries we're looking for.")
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

    # Call the Calendar API
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    dayrange = calendar.monthrange(now.year, now.month)

    start = now.replace(day=1, hour=0, minute=0, second=0)
    end = now.replace(day=dayrange[1], hour=23, minute=59, second=59)

    timeMin = start.isoformat()
    timeMax = end.isoformat()

    print(f"Getting events between:\n{timeMin}\n{timeMax}")
    pageToken = None
    stop = False
    events = []
    while not stop:
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=timeMin,
                timeMax=timeMax,
                maxResults=PAGE_SZ,
                singleEvents=True,
                orderBy="startTime",
                pageToken=pageToken
            )
            .execute()
        )
        events += events_result.get("items", [])

        print(f"Got {len(events)} so far")
        pageToken = events_result.get('nextPageToken', None)
        if pageToken is None:
          stop = True
        else:
          print(f"Grabbing next results (up to {PAGE_SZ} more)")

    if not events:
      print("No events found.")
      return

    # Prints the start and name of the next 10 events
    count=0
    stats = {}
    with open("meetings.csv", 'w', newline='') as csvfile:
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
                attendees = [a.get('displayName', a['email']) for a in event['attendees'] if a.get('responseStatus') == 'accepted']
                if ME in attendees:
                    count+=1
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

                    print(f"{start}: {event["summary"]}")
        
    
    with open('stats.csv', 'w', newline='') as csvfile:
        cw = writer(csvfile, delimiter='^', quotechar='|', quoting=QUOTE_MINIMAL)
        cw.writerow([
            'Date',
            'Cumulative Time',
            'Meeting Count',
        ])

        totalTime = datetime.timedelta(minutes=0)
        totalCount = 0
        for day,daystats in stats.items():
           cw.writerow([
              day,
              str(daystats['time']),
              daystats['count']
           ])
           totalTime += daystats['time']
           totalCount += daystats['count']
        
        
        cw.writerow([
           'Averages',
            str(datetime.timedelta(seconds=int(totalTime.total_seconds() / len(stats)))),
            totalCount / len(stats)
        ])
           
       
    print(f"\n\n{count} total events written to meetings.csv. Stats written to stats.csv")

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()