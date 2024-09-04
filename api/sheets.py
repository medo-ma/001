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
            
            # Check if it's a range request or a search request
            search_value = unquote(params.get('search', None))
            search_columns = unquote(params.get('columns', None))  # New parameter for specifying columns
            
            if search_value:
                if search_columns:
                    # Create query condition to search in specified columns
                    columns = search_columns.split(',')
                    query_conditions = [f"{col} CONTAINS '{search_value}'" for col in columns]
                    query = f"SELECT * WHERE {' OR '.join(query_conditions)}"
                else:
                    # Default to searching in column A if no columns are specified
                    query = f"SELECT * WHERE A CONTAINS '{search_value}'"
                
                # Construct the Google Visualization API URL
                url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tq={query}&sheet={SHEET_NAME}"
                
                # Make the HTTP request to Google Visualization API
                import requests
                response = requests.get(url)
                
                if response.status_code == 200:
                    # Extract JSON data from the response
                    json_data = response.text[response.text.find("(") + 1:-2]  # Extract the JSON part
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json_data.encode())
                else:
                    self.send_response(response.status_code)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Failed to query data'}).encode())
            else:
                # Regular range request
                range_ = unquote(params.get('range', 'Sheet1!A1:D10'))
                
                # Validate the range format
                if not range_.startswith('Sheet1!'):
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Invalid range format'}).encode())
                    return
                
                sheet = service.spreadsheets()
                result = sheet.values().get(
                    spreadsheetId=SPREADSHEET_ID, range=range_).execute()
                
                values = result.get('values', [])
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'values': values}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())



if __name__ == '__main__':
    app.run(debug=True)
