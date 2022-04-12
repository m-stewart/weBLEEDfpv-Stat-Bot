#!/usr/bin/env python3
from __future__ import print_function

import os.path
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Change this to the target spreadsheet ID 
SPREADSHEET_ID = '1FdQfwzq7bMpLWtqQXCvUiwE2LPraLjEJM9Nt444Q2Zk'
# Define the SS tab and range
SPREADSHEET_RANGE_NAME = 'Season Standings!A18:C31'

def sheet_auth():
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        creds = None
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            flow.redirect_uri = 'http://localhost:8080/'
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_sheet(creds):
    # Make API call
    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=SPREADSHEET_RANGE_NAME).execute()
        values = result.get('values',[])
        if not values:
            print('No data found.')
            values = []
    except HttpError as err:
        print("ERROR: {}".format(err))
    return values

def get_season_standings():
    # Auth
    google_credentials = sheet_auth()
    # Get Spreadsheet Values
    values = get_sheet(google_credentials)

    # Assign column headers to the values returned in the spreadsheet
    value_headers = ['Position', 'Points', 'Team']
    # Define the dataframe index column
    value_index = 'Position'
    # Define the final arrangement of the columns
    header_order = ['Team', 'Points']

    # Build the dataframe and set the index
    season_standings_df = pd.DataFrame(values, columns=value_headers).set_index(value_index)
    # Remove the 'Position' header from the index
    season_standings_df.index.name = None
    # Rearrange the columns
    season_standings_df = season_standings_df[header_order]
    return season_standings_df
