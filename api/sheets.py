import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from http.server import BaseHTTPRequestHandler

# Set up Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './hospital-434613-5eeb06d5c9f4.json'  # Store this securely

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

SPREADSHEET_ID = '1435980372'  # Replace with your Google Sheets ID

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        # Handle the request (e.g., read or write data to Google Sheets)
        sheet = service.spreadsheets()
        # Example: Append data
        range_ = "Sheet1!A1:D1"
        values = [
            [data['col1'], data['col2'], data['col3'], data['col4']]
        ]
        body = {
            'values': values
        }
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID, range=range_,
            valueInputOption="RAW", body=body).execute()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'success', 'result': result}).encode())

