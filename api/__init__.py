from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
import base64
import os
app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes and origins

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_BASE64 = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
SERVICE_ACCOUNT_JSON = base64.b64decode(SERVICE_ACCOUNT_BASE64).decode('utf-8')

credentials = Credentials.from_service_account_info(
    json.loads(SERVICE_ACCOUNT_JSON), scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

SPREADSHEET_ID = '1Q4oOByDmCIgPzjhmzpPvotRXY_Ka3fLVFnNeSbrHUKo'  # Replace with your Google Sheets ID

@app.route('/api/sheets', methods=['POST'])
def update_sheet():
    data = request.get_json()
    range_ = data.get('range', 'Sheet1!A1')  # Default range if not provided
    values = data.get('values', [])

    if not isinstance(values, list) or not all(isinstance(row, list) for row in values):
        return jsonify({'error': 'Invalid values format'}), 400

    sheet = service.spreadsheets()
    body = {
        'values': values
    }

    try:
        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID, range=range_,
            valueInputOption="RAW", body=body).execute()

        return jsonify({'status': 'success', 'result': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheets/add', methods=['POST'])
def add_data_to_sheet():
    data = request.get_json()

    # Extract values for columns A and B from the request
    column_a_value = data.get('column_a', '')
    column_b_value = data.get('column_b', '')
    column_c_value = data.get('column_c', '')
    if not column_a_value or not column_b_value or not column_c_value :
        return jsonify({'error': 'Both column_a and column_b and column_c values are required'}), 400

    # Define the range to insert into (e.g., next available row in columns A and B)
    # You can modify the range to match where you want to insert the data
    range_ = 'Sheet1!A:C'

    # Prepare the values to be added
    values = [[column_a_value, column_b_value,column_c_value]]

    body = {
        'values': values
    }

    # Use Google Sheets API to append the new row
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',  # Inserts new rows
            body=body
        ).execute()

        return jsonify({'status': 'success', 'result': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500




@app.route('/api/sheets', methods=['GET'])
def handle_get():
    params = request.args

    if 'count_in_row' in params:
        return handle_count_in_row(params)
    elif 'search' in params:
        return handle_search(params)
    elif 'mo' in params:
        return handle_CustomElement(params)
    else:
        return jsonify({'error': 'Invalid request'}), 400

def handle_count_in_row(params):
    search_query = params.get('search', '').strip()
    count_in_row = params.get('count_in_row', None)

    if not search_query:
        return jsonify({'error': 'No search query provided'}), 400

    if count_in_row:
        sheet = service.spreadsheets()
        range_ = 'Sheet1!A1:BZ1000'  # Adjust range as needed
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_).execute()
        values = result.get('values', [])

        row_number = int(count_in_row)
        if row_number < 1 or row_number > len(values):
            return jsonify({'error': 'Invalid row number'}), 400

        row_data = values[row_number - 1]
        count = row_data.count(search_query)

        return jsonify({'status': 'success', 'count': count})

def handle_search(params):
    search_query = params.get('search', '').strip()
    columns = params.get('columns', 'A').split(',')
    sheet_ = params.get('sheet', 'Sheet1').strip()

    if not search_query:
        return jsonify({'error': 'No search query provided'}), 400

    sheet = service.spreadsheets()
    range_ = f'{sheet_}!A1:BZ1000'  # Adjust range as needed
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_).execute()
    values = result.get('values', [])

    matching_rows = []
    column_indices = [ord(col.upper()) - ord('A') for col in columns]

    for row_index, row in enumerate(values, start=1):
        for index in column_indices:
            if len(row) > index and search_query in row[index]:
                matching_rows.append({'index': row_index, 'student': row})
                break
    if matching_rows != []:
        return jsonify({'status': 'success', 'matches': matching_rows})
    else:
        return jsonify({'status': 'false', 'matches': '0'})

def handle_CustomElement(params):
    search_query = params.get('mo').strip()
    sh = params.get('sh').strip()
    sheet = service.spreadsheets()
    range_ = f'{sh}!{search_query}'
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_).execute()
    values = result.get('values', [])

    return jsonify({'status': 'success', 'mo': values})
#
if __name__ == '__main__':
    app.run(debug=True)
