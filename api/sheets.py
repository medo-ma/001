from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
import base64
import os

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_BASE64 = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
SERVICE_ACCOUNT_JSON = base64.b64decode(SERVICE_ACCOUNT_BASE64).decode('utf-8')

credentials = Credentials.from_service_account_info(
    json.loads(SERVICE_ACCOUNT_JSON), scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

SPREADSHEET_ID = '14B1_20Ix3CjgrUxijbYpIhpFQVa1ai3_'  # Replace with your Google Sheets ID

@app.route('/api/sheets', methods=['POST'])
def handle_request():
    try:
        if request.content_type != 'application/json':
            return jsonify({'error': 'Unsupported Media Type'}), 415

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

        return jsonify({'status': 'success', 'result': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
