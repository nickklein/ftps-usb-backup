#!/usr/bin/python3 
from sftp_uploader import SFTPUploader 
from s3_uploader import S3Uploader 
from local_uploader import LocalUploader 
from config_manager import ConfigManager
from state_manager import StateManager
from folder_manager import FolderManager
from compressor import Compressor
from ftplib import FTP_TLS
import zipfile
import os
import time
import sys
import pickle
import subprocess
import hashlib
import socket
import pysftp
import shutil
import boto3
from dotenv import load_dotenv
load_dotenv()

class Backup:

    def __init__(self):
        self.config = ConfigManager()
        self.state_manager = StateManager(
            self.config.PICKLE_ACTIVE_FILEPATH,
            self.config.PICKLE_FTP_FILEPATH
        )
        self.folder_manager = FolderManager(
            self.config.FOLDERS,
            self.config.TMP_FOLDER
        )
        self.compressor = Compressor(self.config.ENCRYPTION_KEY,self.config.TMP_FOLDER)
        self.uploaders = self.initialize_backup()
        self.run_backup()

    def run_backup(self):
        if len(sys.argv) > 1 and sys.argv[1] == 'reset':
            print('Resetting backup state...')
            self.state_manager.set_backup_active(False)
            return
        if self.state_manager.is_backup_active():
            print("Backup is already active..")
            return


        self.state_manager.set_backup_active(True)
        try:
            # Get current folder stats
            current_stats = self.folder_manager.get_folder_stats()
            previous_stats = self.state_manager.load_folder_sizes()
            # Determine folders that have changed
            folders_to_backup = self.folder_manager.get_folders_to_backup(current_stats, previous_stats)

            if not folders_to_backup:
                print('No changes detected. Backup not required.')
                return

            compressed_files = []
            for folder in folders_to_backup:
                compressed_file = self.compressor.compress(folder)
                if compressed_file:
                    compressed_files.append(compressed_file)

             # Upload compressed files
            for uploader in self.uploaders:
                for file_path in compressed_files:
                    uploader.upload(file_path)           

            self.state_manager.save_folder_sizes(current_stats)

        except Exception as e:
            print(f"An error occured: {e}")
        finally:
            print('All done!')
            self.folder_manager.clean_up();
            self.state_manager.set_backup_active(False)

    def initialize_backup(self):
        uploaders = []
        if 'sftp' in self.config.backup_destinations:
            sftp_uploader = SFTPUploader(
                self.config.SFTP_HOST,
                self.config.SFTP_USER,
                self.config.SFTP_PASSWORD,
                self.config.REMOTE_UPLOAD_DIR
            )
            uploaders.append(sftp_uploader)
        if 's3' in self.config.backup_destinations:
            s3_uploader = S3Uploader(
                self.config.S3_ACCESS_KEY,
                self.config.S3_SECRET_KEY,
                self.config.S3_BUCKET,
                self.config.S3_KEY_PREFIX,
                self.config.S3_REGION
            )
            uploaders.append(s3_uploader)
        if 'usb' in self.config.backup_destinations:
            usb_uploader = LocalUploader(self.config.USB_DIR)
            uploaders.append(usb_uploader)
        if 'folder' in self.config.backup_destinations:
            folder_uploader = LocalUploader(self.config.FOLDER_DIR)
            uploaders.append(folder_uploader)

        return uploaders

backup = Backup()
