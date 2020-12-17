import sys
import os
import pickle
import argparse
from datetime import datetime
from pprint import pprint

from dotenv import load_dotenv

import numpy as np
import pandas as pd

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

_ = load_dotenv()

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
SCOPES = os.environ.get("SCOPES")
DATA_PATH = os.environ.get("DATA_PATH")

def get_credentials(scopes):
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

def write_sheet_data(data):
    data.to_csv(DATA_PATH)


def pull_google_sheet_data(desired_range, spreadsheet_id=SPREADSHEET_ID):
    assert isinstance(spreadsheet_id, str) and isinstance(desired_range, str)
    print(desired_range)
    creds = get_credentials(SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    sheet_data = sheet.values().get(spreadsheetId=SPREADSHEET_ID, 
                                 range=desired_range).execute()
    values = sheet_data.get('values')
    return values
 
''' TODO: 
        * Column great_total = Potential_Inv + AcumEarned
        * Column to_play = great_total*0.5 + great_total*0.5*(1-AvgRcrds)
        * Column to_buy = to_buy - Playing (D is amount playing)
        * Pull Date, All, and BuyPower from Spreadsheet'''

class DataNotFoundError(Exception):
    """Exception raised when data values are empty."""

    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.message = "No data found for spreadsheet {self.spreadsheet_id}"
        super().__init__(self.message)



def save_sheet_to_dataframe(column_list: list, tab='dt', date=None) -> int:
    "Create the datafram with desired Google Sheet columns"
    
    final_df = pd.DataFrame()
    #TODO: Get columns "B" "C" from Robin Hood API
    try:
        complete_columns_list = ["A", "B", "C"]+column_list
         
        for column in complete_columns_list:
            current_range = f'{tab}!{column}:{column}'
            rows = pull_google_sheet_data(desired_range=current_range)
            final_df[rows[0][0]] = [cell[0] if cell else '' for cell in rows[1:]]
        write_sheet_data(final_df)
    except Exception as e:
        print(e)


def load_sheet_to_dataframe():
    sheet_df = pd.read_csv(DATA_PATH)
    sheet_df.set_index("Date", inplace=True)
    return sheet_df

def convert_currency(currency_string):
    converted_currency_string = currency_string.replace('$', '').replace(',','')
    return np.float32(converted_currency_string)


def calculate_great_total(potential_inv, acum_earned):
    great_total = potential_inv + acum_earned
    return great_total

def calculate_to_play(great_total, avg_recrds):
    to_play = great_total*0.5 + great_total*0.5*(1-avg_recrds)
    return to_play

def calculate_to_buy(to_play, playing):
    to_buy = to_play - playing
    return to_buy
                
def calculations(date):
    sheet_df = load_sheet_to_dataframe()

    if not date:
        now = datetime.now()
        format = "%m/%d/%Y"
        date = now.strftime(format)
    
    desired_row = sheet_df.loc[date]
    print(desired_row)
    potential_inv = convert_currency(desired_row['Potential_Inv'])
    acum_earned = convert_currency(desired_row['AcumEarned'])
    great_total = calculate_great_total(potential_inv, acum_earned)
    avg_records = np.float32(desired_row['AvgRcrds'][:-1])/100
    to_play = calculate_to_play(great_total, avg_records)
    playing = convert_currency(desired_row['Playing'])
    to_buy = calculate_to_buy(to_play, playing)

    print(to_buy)



if __name__ == "__main__":
    desired_columns = ["D", "J", "L", "N", "O", "P"] 	
    try:
        parser = argparse.ArgumentParser(description='Calculate amount to invest based on what you are willing to invest')

        parser.add_argument('-a', '--amount', help="Amount that you are willing to invest")
        parser.add_argument('-d', '--date', help="Date you would like to use (Default = Today's Date)")

        args = parser.parse_args()
        if args.amount:
            amount = int(args.amount)
        date = args.date
        
        #save_sheet_to_dataframe(desired_columns)
        calculations(date)
    except Exception as e:
        print(e)
