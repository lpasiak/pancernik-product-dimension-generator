import gspread
import pandas as pd
import os
from config import SHEETS_DIR
import time
from gspread.exceptions import APIError

class GSheetsClient:

    def __init__(self, credentials, sheet_id, sheet_name):
        """
        Initialize the GSheetsClient with credentials and sheet ID.
        Args:
            credentials (str): Path to the service account JSON credentials file.
            sheet_id (str): Name of the environment variable storing the sheet ID.
            sheet_name (str): Name of the specific sheet.
        """

        self.credentials_path = credentials
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self.gc = None
        self.sheet = None
        self.worksheet = None

    def connect(self):
        """Authenticate with Google Sheets."""
        try:
            self.gc = gspread.service_account(filename=self.credentials_path)
            self.sheet = self.gc.open_by_key(self.sheet_id)
            self.worksheet = self.sheet.worksheet(self.sheet_name)
            print("Google Authentication successful.")
        except Exception as e:
            print(f"Failed to connect to Google Sheets: {str(e)}")
            raise

    def get_data(self, include_row_numbers=False):
        """Get data from a Google Sheets worksheet as a pandas DataFrame."""
        if not self.sheet:
            raise Exception("Not connected to Google Sheets. Call connect() first.")

        worksheet = self.sheet.worksheet(self.sheet_name)
        data = worksheet.get_all_values()
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data[1:], columns=data[0])  # First row as header
        df.to_excel(os.path.join(SHEETS_DIR, 'google_sheets_all.xlsx'), index=False)
        df = df[df.iloc[:, 0].notna() & (df.iloc[:, 0] != '')]
        df = df[df['komunikat'] != 'Promocja dodana']
        
        if include_row_numbers:
            df.insert(0, 'Row Number', range(2, len(df) + 2)) # GSheets rows start at 2

        return df
    
    def save_data(self, df, max_retries=3, delay=5):
        """
        Save DataFrame to Google Sheets.
        """
        attempt = 0
        while attempt < max_retries:
            try:
                print('Transforming data...')
                all_values = self.transform_data(df)
                print('Cleaning the worksheet...')
                self.worksheet.clear()
                print('Saving to Google Sheets...')
                self.worksheet.update(all_values)
                print("Successfully saved to Google Sheets!")
                return True
                
            except APIError as e:
                attempt += 1
                if attempt == max_retries:
                    print(f"Failed to save after {max_retries} attempts. Error: {str(e)}")
                    return False
                else:
                    print(f"Attempt {attempt} failed. Retrying in {delay} seconds...")
                    time.sleep(delay)
            except Exception as e:
                print(f"Unexpected error occurred: {str(e)}")
                return False

    def transform_data(self, df):
        """
        Transform DataFrame to match Google Sheets format.
        """
        df_string = df.astype(str)
        header = df_string.columns.values.tolist()
        data = df_string.values.tolist()
        
        return [header] + data
