import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def handler(event, context):
    # Authenticate and build the service
    SERVICE_ACCOUNT_FILE = '/client_sec.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    
    # Example function to read data
    def get_data(range_name):
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId='your-spreadsheet-id',
                                    range=range_name).execute()
        return result.get('values', [])
    
    # Get data and format response
    data = get_data('Sheet1!A:D')
    response = {
        'statusCode': 200,
        'body': json.dumps(data),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # Allow requests from any origin
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    }
    return response
