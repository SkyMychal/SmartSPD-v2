"""
Cloud storage service for handling file uploads, downloads, and deletions.
This is a local simulation of a cloud storage service.
"""
import os
import shutil
from pathlib import Path
from fastapi import HTTPException

from app.core.config import settings

class CloudStorageService:
    def __init__(self):
        self.bucket_path = Path(settings.CLOUD_STORAGE_BUCKET_PATH)
        self.bucket_path.mkdir(parents=True, exist_ok=True)

    def upload_file(self, source_path: str, destination_path: str) -> str:
        """
        Moves a file from a source path to the cloud storage bucket.
        In this local simulation, it moves the file to the configured bucket path.
        """
        try:
            destination_full_path = self.bucket_path / destination_path
            destination_full_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(source_path, destination_full_path)
            return str(destination_full_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload file to cloud storage: {e}")

    def get_file_path(self, file_key: str) -> str:
        """
        Gets the full path to a file in the cloud storage bucket.
        """
        return str(self.bucket_path / file_key)

    def delete_file(self, file_key: str):
        """
        Deletes a file from the cloud storage bucket.
        """
        try:
            file_path = self.bucket_path / file_key
            if file_path.exists():
                os.remove(file_path)
        except Exception as e:
            # Log the error, but don't raise an exception to the user
            print(f"Error deleting file from cloud storage: {e}")

cloud_storage_service = CloudStorageService()
