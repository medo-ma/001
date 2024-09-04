from google.oauth2 import service_account
from googleapiclient.discovery import build

# Path to your service account credentials
SERVICE_ACCOUNT_FILE = 'path/to/credentials.json'

# Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# ID of the Google Sheet
SPREADSHEET_ID = 'your-spreadsheet-id'

# Authenticate and build the service
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

# Function to get data
def get_data(range_name):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    return result.get('values', [])

# Function to update data
def update_data(range_name, values):
    sheet = service.spreadsheets()
    body = {'values': values}
    result = sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=range_name,
                                   valueInputOption='RAW', body=body).execute()
    return result

# Example usage
data = get_data('Sheet1!A:D')
print(data)
