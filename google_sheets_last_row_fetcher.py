import requests
API_KEY="AIzaSyCrHqwbt8hAxuTXFcPlb6mt0nGljXA7NDs"

def get_spreadsheet_values(column_name):
    spreadsheet_id = '1z4TW2HLZrD3obstC3ICqzxOPAZXwZzeoo7jsix9PWEo'
    range_name = column_name
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}?alt=json&key={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        values = response.json().get('values', [])

        if not values:
            print('No data found.')
            return 'No data found.'
        else:
            last_row = len(values)
            print(f"{last_row}, {values[-1]}")
            return values[-1]
    except requests.exceptions.HTTPError as err:
        print(err)
        return str(err)

# Example usage:
if __name__ == '__main__':
  last_value = get_spreadsheet_values('Bill history!I2:I')
  print(last_value)
