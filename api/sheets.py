import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Set up Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = '/hospital-434613-5eeb06d5c9f4.json'  # Ensure this path is correct

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

SPREADSHEET_ID = '14B1_20Ix3CjgrUxijbYpIhpFQVa1ai3'  # Replace with your Google Sheets ID

def handler(request, context):
    try:
        if request.method == 'POST':
            data = request.json

            # Handle the request (e.g., read or write data to Google Sheets)
            sheet = service.spreadsheets()
            # Example: Append data
            range_ = "Sheet1!A1:D1"
            values = [
                [data.get('col1'), data.get('col2'), data.get('col3'), data.get('col4')]
            ]
            body = {
                'values': values
            }
            result = sheet.values().append(
                spreadsheetId=SPREADSHEET_ID, range=range_,
                valueInputOption="RAW", body=body).execute()

            return {
                "statusCode": 200,
                "body": json.dumps({'status': 'success', 'result': result})
            }
        else:
            return {
                "statusCode": 405,
                "body": json.dumps({'error': 'Method Not Allowed'})
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({'error': str(e)})
        }
