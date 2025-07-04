from gdrive_logger import DriveLogger
import os

class LogRouter:
    def __init__(self, use_drive=False):
        self.use_drive = use_drive
        self.drive_logger = DriveLogger() if use_drive else None

    def log_local_and_remote(self, local_file_path):
        if self.use_drive:
            try:
                remote_filename = os.path.basename(local_file_path)
                self.drive_logger.upload_or_append(local_csv_path=local_file_path, remote_filename=remote_filename)
            except Exception as e:
                print(f"[LogRouter] Failed to sync to Google Drive: {e}")