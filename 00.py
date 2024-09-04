from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)  # Allow all origins by default

@app.route('/api', methods=['GET'])
def get_data():
    # Authenticate and build the service
    SERVICE_ACCOUNT_FILE = '/client_sec.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    
    # Example function to read data
    def fetch_data(range_name):
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId='your-spreadsheet-id',
                                    range=range_name).execute()
        return result.get('values', [])
    
    # Get data and format response
    data = fetch_data('Sheet1!A:D')
    return jsonify(data)

if __name__ == '__main__':
    app.run()
