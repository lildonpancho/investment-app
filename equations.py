import sys
import os
import pickle
import argparse
from datetime import datetime

from dotenv import load_dotenv

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

_ = load_dotenv()

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
SCOPES = os.environ.get("SCOPES")

def get_credentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def get_avg_records(date=None):
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range='P1:P12').execute()
    if not date:
        date = datetime.now()
    values = result.get('values', [])
    if not values:
        print('No data found.')
    else:
        print(values)
    return date


if __name__ == "__main__":
	
	try:
		parser = argparse.ArgumentParser(description='Calculate amount to invest based on what you are willing to invest')

		parser.add_argument('-a', '--amount', help="Amount that you are willing to invest", required=True)
		parser.add_argument('-d', '--date', help="Date you would like to use (Default = Today's Date)")

		args = parser.parse_args()
		amount = int(args.amount)
		
		print(get_avg_records())
	except ValueError as ve:
		print('Amount must be an integer or float value.')
