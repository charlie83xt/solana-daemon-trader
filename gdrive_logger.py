from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import csv
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

FOLDER_NAME = "SolanaTraderLogs"


class DriveLogger:
    def __init__(self):
        self.path_to_auth_file = "gdrive_service_account.json"
        scope = ["https://www.googleapis.com/auth/drive"]

        self.gauth = GoogleAuth()
        self.gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self.path_to_auth_file,
            scope
        )

        self.gauth.auth_method = 'service'
        
        self.drive = GoogleDrive(self.gauth)
        self.folder_id = self._ensure_folder()


    def _ensure_folder(self):
        query = f"title='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        file_list = self.drive.ListFile({'q': query}).GetList()

        if file_list:
            folder = file_list[0]
        else:
            folder = self.drive.CreateFile({'title': FOLDER_NAME, 'mimeType': 'application/vnd.google-apps.folder'})
            folder.Upload()
        # Sharing the FOLDER NAME (SolanaTraderLogs) To find on personal account
        permission = {
            "type": "user",
            "value": os.getenv("PERSONAL_GMAIL"),
            "role": "writer"
        }
        folder.InsertPermission(permission)
        return folder['id']

        

        
    def upload_or_append(self, local_csv_path, remote_filename="trade_log.csv"):
        file_list = self.drive.ListFile({
            'q': f"title='{remote_filename}' and '{self.folder_id}' in parents and trashed= false"
        }).GetList()

        if not file_list:
            print("[DriveLogger] Uploading new log file...")
            new_file = self.drive.CreateFile({'title': remote_filename, 'parents': [{'id': self.folder_id}]})
            new_file.SetContentFile(local_csv_path)
            new_file.Upload()

        else:
            print("[DriveLogger] Appending to existing log...")
            existing = file_list[0]
            existing.GetContentFile("temp_existing.csv")
            with open("temp_existing.csv", "a", newline="") as f1, open(local_csv_path, "r") as f2:
                reader = csv.reader(f2)
                next(reader) # Skip header
                writer = csv.writer(f1)
                for row in reader:
                    writer.writerow(row)
            existing.SetContentFile("temp_existing.csv")
            existing.Upload()
            os.remove("temp_existing.csv")