from decouple import config
from apiclient import discovery
from google.oauth2 import service_account
import pandas as pd


class GoogleSheetsAPI:
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file",
                       "https://www.googleapis.com/auth/spreadsheets"]
        self.env = {"type": config('GOOGLE_AUTH_TYPE'),
                    "project_id": config('GOOGLE_AUTH_PROJECT_ID'),
                    "private_key_id": config('GOOGLE_AUTH_PRIVATE_KEY_ID'),
                    "private_key": config('GOOGLE_AUTH_PRIVATE_KEY').replace('\\n', '\n'),
                    "client_email": config('GOOGLE_AUTH_CLIENT_EMAIL'),
                    "client_id": config('GOOGLE_AUTH_CLIENT_ID'),
                    "auth_uri": config('GOOGLE_AUTH_AUTH_URI'),
                    "token_uri": config('GOOGLE_AUTH_TOKEN_URI'),
                    "auth_provider_x509_cert_url": config('GOOGLE_AUTH_AUTH_PROVIDER_X509_CERT_URL'),
                    "client_x509_cert_url": config('GOOGLE_AUTH_CLIENT_X509_CENT_URL')}

        self.pull_spreadsheet_id = config('PULL_SPREADSHEET_ID')
        self.export_spreadsheet_id = config('EXPORT_SPREADSHEET_ID')
        self.range_name_outliers = 'Outliers!A1'
        self.range_name_duplicates = 'Duplicates!A1'
        self.range_name_participants = 'participants'
        self.participants = []

    def export_to_google_sheet(self, change_weightings, duplicates):
        print("Exporting to Google Sheet...")
        credentials = service_account.Credentials.from_service_account_info(self.env, scopes=self.scopes)
        service = discovery.build('sheets', 'v4', credentials=credentials)

        df_outliers = pd.DataFrame(change_weightings)

        service.spreadsheets().values().append(
            spreadsheetId=self.export_spreadsheet_id,
            range=self.range_name_outliers,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={
                "values": df_outliers.values.tolist()
            },
        ).execute()

        df_duplicates = pd.DataFrame(duplicates)

        service.spreadsheets().values().append(
            spreadsheetId=self.export_spreadsheet_id,
            range=self.range_name_duplicates,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={
                "values": df_duplicates.values.tolist()
            },
        ).execute()

    def pull_participants_data(self):
        print("Pulling participants data...")
        credentials = service_account.Credentials.from_service_account_info(self.env, scopes=self.scopes)
        service = discovery.build('sheets', 'v4', credentials=credentials)

        rows = service.spreadsheets().values().get(
            spreadsheetId=self.pull_spreadsheet_id,
            range=self.range_name_participants
        ).execute()
        data = rows.get('values')
        print("Data Copied")
        return data
