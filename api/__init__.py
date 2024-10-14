from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread
import json  # Import the json module
import base64
import os
from datetime import datetime
from dotenv import load_dotenv , dotenv_values

#load the keys from .env 
load_dotenv()

#create app's instance
app = Flask(__name__)

CORS(app)  # This will enable CORS for all routes and origins

#google authncation 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SERVICE_ACCOUNT_BASE64 = os.environ.get('GOOGLE_SERVICE_ACCOUNT') #load the creds from the key 

SERVICE_ACCOUNT_JSON = base64.b64decode(SERVICE_ACCOUNT_BASE64).decode('utf-8') #decoding step 

SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_JSON) #final result > account info for creds

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(creds)
service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = '1Q4oOByDmCIgPzjhmzpPvotRXY_Ka3fLVFnNeSbrHUKo' #sheet id

#the selection of the sheet's page, depending on the current month
current_month = datetime.now().month
sheet_page = f'Sheet{current_month}'

sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_page) #sheet var for easy calling 

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
    sheeto = data.get('Sheet','')
    rango = data.get('range','')
    column_a_value = data.get('column_a', '')
    column_b_value = data.get('column_b', '')
    column_c_value = data.get('column_c', '')
    column_d_value = data.get('column_d', '')
    column_e_value = data.get('column_e', '')
    if not rango or not sheeto :
        return jsonify({'error': 'sheet and range are required'}), 400

    # Define the range to insert into (e.g., next available row in columns A and B)
    # You can modify the range to match where you want to insert the data
    range_ = f'{sheeto}!{rango}'

    # Prepare the values to be added
    values = [[column_a_value, column_b_value,column_c_value,column_d_value,column_e_value]]
    
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


#change password
@app.route('/api/sheets/change_pass', methods=['POST'])
def change_pass():
    data = request.get_json()
    scode = data.get('scode')
    new_pass = data.get('pass')
    try:
        # Find the cell you know
        cell = sheet.find(scode)

        # Update the cell in the same row but different column
        sheet.update_cell(cell.row, cell.col + 1, f'{new_pass}')

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500






#admin
@app.route('/api/sheets/update-status', methods=['POST'])
def update_status():
    data = request.get_json()
    print("Received data:", data)  # Log incoming data

    row_index = data.get('row_index')
    scode = data.get('scode')
    status = data.get('status')
    dates_str = data.get('dates')
    type_v = data.get('type')

    if not row_index or not scode or not status or not dates_str:
        return jsonify({'error': 'Row index, scode, status, and dates are required'}), 400

    try:
        # Open the spreadsheet
        spreadsheet = client.open_by_key(SPREADSHEET_ID)

        # Update the status in the "Requests-{type_v}" sheet
        status_range = f'Requests-{type_v}!D{row_index}'  # Column D
        spreadsheet.values_update(
            status_range,
            params={'valueInputOption': 'USER_ENTERED'},
            body={'values': [[status]]}
        )

        if status != 'Approved':
            # If the status is not "Approved", skip vacation days update
            return jsonify({'status': 'success'})

        # Parse the month from dates_str
        month = json.loads(dates_str).get('first', {}).get('month', '1')
        sheet_page = f'Sheet{int(month)}'  # Format month as Sheet{month}

        # Get the vacation sheet by month
        vacation_sheet = spreadsheet.worksheet(sheet_page)

        # Find the row in column A where scode matches
        vacation_codes = vacation_sheet.col_values(1)  # Column A
        try:
            vacation_row_index = vacation_codes.index(scode) + 1  # Adding 1 because gspread is 1-indexed
        except ValueError:
            return jsonify({'error': 'Student code not found in vacation sheet'}), 404

        # Map days to columns
        day_to_column = {
            1: 'D', 2: 'E', 3: 'F', 4: 'G', 5: 'H', 6: 'I', 7: 'J', 8: 'K',
            9: 'L', 10: 'M', 11: 'N', 12: 'O', 13: 'P', 14: 'Q', 15: 'R',
            16: 'S', 17: 'T', 18: 'U', 19: 'V', 20: 'W', 21: 'X', 22: 'Y',
            23: 'Z', 24: 'AA', 25: 'AB', 26: 'AC', 27: 'AD', 28: 'AE',
            29: 'AF', 30: 'AG', 31: 'AH'
        }

        # Parse dates and update vacation days individually
        date_values = json.loads(dates_str)
        for key in date_values.keys():
            day = int(date_values[key]['day'])
            column_letter = day_to_column.get(day)  # Map day to column letter
            if not column_letter:
                continue  # Skip if day is out of range

            # Update the vacation day cell
            vacation_range = f'{sheet_page}!{column_letter}{vacation_row_index}'
            vacation_values = [[type_v]]
            vacation_body = {'values': vacation_values}

            spreadsheet.values_update(
                vacation_range,
                params={'valueInputOption': 'USER_ENTERED'},
                body=vacation_body
            )

        return jsonify({'status': 'success'})

    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Print the error for debugging
        return jsonify({'error': str(e)}), 500


#sign_in
@app.route('/api/sheets/sign_in', methods=['POST'])
def sign_in():
    data = request.get_json()
    search_value = data.get('scode')
    
    try:
        # Find the cell in column A
        cell = sheet.find(search_value, in_column=1)
        
        if cell is None:
            return jsonify({'error': f'Value "{search_value}" not found in column A'}), 404
        
        # Get all values in the same row
        row_values = sheet.row_values(cell.row)
        matches = {'index':cell.row,"student":row_values}
        return jsonify({'status': 'success', 'matches': matches})
    except Exception as e:
        return jsonify({'error': str(e)}), 500






@app.route('/api/sheets', methods=['GET'])
def handle_get():
    params = request.args

    if 'count_in_row' in params:
        return handle_count_in_row(params)
    elif 'search' in params:
        return handle_search(params)
    elif 'sign_in' in params:
        return sign_in(params)
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

    if not search_query:
        return jsonify({'error': 'No search query provided'}), 400

    sheet = service.spreadsheets()
    range_ = f'{sheet_page}!A1:BZ1000'  # Adjust range as needed
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

@app.route('/api/sheets/student-requests_c', methods=['GET'])
def get_student_requests_c():
    scode = request.args.get('scode')
    if not scode:
        return jsonify({'error': 'Student code is required'}), 400

    # Define the range to fetch (e.g., columns A to D)
    range_ = 'Requests-C!A:D'

    try:
        # Use Google Sheets API to get the data
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_
        ).execute()

        rows = result.get('values', [])
        if not rows:
            return jsonify({'message': 'No data found'}), 404

        # Initialize an empty list to store filtered requests
        student_requests_c = []

        # Loop through each row, checking if it has the required number of columns
        for row in rows:
            # Only process rows with enough columns
            if len(row) >= 4 and row[0] == scode:  # Check if row has at least 4 columns
                student_requests_c.append({
                    'scode': row[0],     # Student code
                    'sname': row[1],     # Student name
                    'dates': row[2],     # Vacation dates (can be stored as JSON or a combined string)
                    'status': row[3]     # Status (Pending, Approved, Rejected)
                })

        if not student_requests_c:
            return jsonify({'message': 'No vacation requests found for this student'}), 404

        return jsonify({'requests': student_requests_c})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheets/student-requests_e', methods=['GET'])
def get_student_requests_e():
    scode = request.args.get('scode')
    if not scode:
        return jsonify({'error': 'Student code is required'}), 400

    # Define the range to fetch (e.g., columns A to D)
    range_ = 'Requests-E!A:D'

    try:
        # Use Google Sheets API to get the data
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_
        ).execute()

        rows = result.get('values', [])
        if not rows:
            return jsonify({'message': 'No data found'}), 404

        # Initialize an empty list to store filtered requests
        student_requests_e = []

        # Loop through each row, checking if it has the required number of columns
        for row in rows:
            # Only process rows with enough columns
            if len(row) >= 4 and row[0] == scode:  # Check if row has at least 4 columns
                student_requests_e.append({
                    'scode': row[0],     # Student code
                    'sname': row[1],     # Student name
                    'dates': row[2],     # Vacation dates (can be stored as JSON or a combined string)
                    'status': row[3]     # Status (Pending, Approved, Rejected)
                })

        if not student_requests_e:
            return jsonify({'message': 'No vacation requests found for this student'}), 404

        return jsonify({'requests': student_requests_e})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


#admin
@app.route('/api/sheets/requests', methods=['GET'])
def get_requests():
    #type_v = request.args.get("type")
    try:
        # Fetch data from Google Sheets
        sheet = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Requests!A:E'  # Updated to reflect the correct sheet name
        ).execute()

        # Debugging: print the entire API response to see what is returned
        print("API Response:", sheet)

        rows = sheet.get('values', [])

        # Skip the header row and process the rest
        requests = []
        for index, row in enumerate(rows[1:], start=2):  # Start index at 2 to reflect the actual row number in the sheet
            if len(row) >= 5:  # Ensure there are at least 4 columns (A, B, C, D)
                requests.append({
                    'rowIndex': index,       # Capture row number for updates
                    'scode': row[0],
                    'sname': row[1],
                    'dates': row[2],         # Dates stored in JSON format
                    'status': row[3],         # Status in column D
                    'type' : row[4]
                })

        # Debugging: print out the processed requests
        print("Processed requests:", requests)

        return jsonify({'requests': requests})

    except Exception as e:
        return jsonify({'error': str(e)}), 500







#
if __name__ == '__main__':
    app.run(debug=True)
