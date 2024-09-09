from flask import Flask #, request, jsonify
from urllib.parse import unquote
#from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from http.server import BaseHTTPRequestHandler
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

SPREADSHEET_ID = '1pTBX4oVDvXaMm34910DiMMnR0auHVEEPA-QkJxTsrug'  # Replace with your Google Sheets ID

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        range_ = data.get('range', 'Sheet1!A1')  # Default range if not provided
        values = data.get('values', [])

        if not isinstance(values, list) or not all(isinstance(row, list) for row in values):
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid values format'}).encode())
            return

        sheet = service.spreadsheets()
        body = {
            'values': values
        }

        try:
            result = sheet.values().update(
                spreadsheetId=SPREADSHEET_ID, range=range_,
                valueInputOption="RAW", body=body).execute()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success', 'result': result}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())



    def do_GET(self):
        try:
            # Parse the query parameters
            query = self.path.split('?')[1] if '?' in self.path else ''
            params = dict(p.split('=') for p in query.split('&') if '=' in p)

            # Determine which action to take based on parameters
            if 'count_in_row' in params:
                self.handle_count_in_row(params)
            elif 'search' in params:
                self.handle_search(params)
            elif 'mo' in params:
                self.handle_CustomElement(params)
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid request'}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def handle_count_in_row(self, params):
        search_query = unquote(params.get('search', '')).strip()
        count_in_row = params.get('count_in_row', None)

        if not search_query:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'No search query provided'}).encode())
            return

        if count_in_row:
# Fetch data from the Google Sheets API
            sheet = service.spreadsheets()
            range_ = 'Sheet1!A1:BZ1000'  # Adjust range as needed
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_).execute()
            values = result.get('values', [])

            row_number = int(count_in_row)
            if row_number < 1 or row_number > len(values):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid row number'}).encode())
                return

            row_data = values[row_number - 1]
            count = row_data.count(search_query)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success', 'count': count}).encode())

    def handle_search(self, params):
        search_query = unquote(params.get('search', '')).strip()
        columns = params.get('columns', 'A').split(',')
        sheet_ = unquote(params.get('sheet', 'Sheet1')).strip()
        if not search_query:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'No search query provided'}).encode())
            return

# Fetch data from the Google Sheets API
        sheet = service.spreadsheets()
        range_ = f'{sheet_}!A1:BZ1000'  # Adjust range as needed
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_).execute()
        values = result.get('values', [])

        matching_rows = []
        column_indices = [ord(col.upper()) - ord('A') for col in columns]

        for row_index, row in enumerate(values, start=1):
            for index in column_indices:
                if len(row) > index and search_query in row[index]:
                    matching_rows.append({'row_number': row_index, 'row_data': row})
                    break
#send the response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'success', 'matches': matching_rows}).encode())

#this query can be customized with range and the sheet name, it will return the value of the range
    def handle_CustomElement(self, params):
        search_query = unquote(params.get('mo')).strip()
        sh = unquote(params.get('sh')).strip()
        sheet = service.spreadsheets()
        range = f'{sh}!{search_query}'
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range).execute()
        values = result.get('values', [])
#send the response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'success', 'mo ':f'{values}'}).encode())




if __name__ == '__main__':
    app.run(debug=True)
