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

SPREADSHEET_ID = '189dHVDH5N7DQ4jTM_5ie90obYUWKX9ldybqw9g-NHm0'  # Replace with your Google Sheets ID

@app.route('/api/sheets', methods=['POST', 'GET'])
def handle_request():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            return jsonify({'error': 'Unsupported Media Type'}), 415

        try:
            data = request.json
            sheet = service.spreadsheets()
            range_ = "Sheet1!A1:A4"
            values = [
                [data['col1'], data['col2'], data['col3'], data['col4']]
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

    elif request.method == 'GET':
        try:
            range_ = "Sheet1!A1:A10"  # Adjust the range as needed
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID, range=range_).execute()
            values = result.get('values', [])

            return jsonify({'status': 'success', 'data': values})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
