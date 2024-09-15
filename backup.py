#!/usr/bin/python3 
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

# This code needs major refactoring.
class Backup:

    # Select all the directories that need to be backed up
    FOLDERS = [
        [os.path.expanduser('~/Desktop/'), 'Desktop'],
        [os.path.expanduser('~/Documents/'), 'Documents'],
        [os.path.expanduser('~/Music/'), 'Music'],
        [os.path.expanduser('~/Pictures/'), 'Pictures'],
        [os.path.expanduser('~/Videos/'), 'Videos'],
        [os.path.expanduser('~/Sites/'), 'Sites'],
        [os.path.expanduser('~/Backup/'), 'Backup'],
    ]

    #File Paths to pickle files
    PICKLE_FTP_FILEPATH = os.environ.get('PICKLE_FTP_FILEPATH', '')
    PICKLE_ACTIVE_FILEPATH = os.environ.get('PICKLE_ACTIVE_FILEPATH', '')

    FTP_BACKUP = os.environ.get('FTP_BACKUP', 'true').lower() == 'true'
    FTP_HOST = os.environ.get('FTP_HOST', '')
    FTP_USER = os.environ.get('FTP_USER', '')
    FTP_PASSWORD = os.environ.get('FTP_PASSWORD', '')

    SFTP_BACKUP = os.environ.get('SFTP_BACKUP', 'true').lower() == 'true'
    SFTP_HOST = os.environ.get('SFTP_HOST', '')
    SFTP_USER = os.environ.get('SFTP_USER', '')
    SFTP_PASSWORD = os.environ.get('SFTP_PASSWORD', '')

    USB_BACKUP = os.environ.get('USB_BACKUP', 'false').lower() == 'true'
    USB_DIR = os.environ.get('USB_DIR', '')

    FOLDER_BACKUP = os.environ.get('FOLDER_BACKUP', 'true').lower() == 'true'
    FOLDER_DIR = os.environ.get('FOLDER_DIR', '')

    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '')

    TMP_FOLDER = os.environ.get('TMP_FOLDER', '')

    USE_VPN = os.environ.get('USE_VPN', 'false').lower() == 'true'
    VPN_OVPN_FILE = os.environ.get('VPN_OVPN_FILE', '')
    VPN_USERNAME = os.environ.get('VPN_USERNAME', '')
    VPN_PASSWORD = os.environ.get('VPN_PASSWORD', '')

    S3_BACKUP = os.environ.get('S3_BACKUP', 'false').lower() == 'true'
    S3_BUCKET = os.environ.get('S3_BUCKET', '')
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY', '')
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY', '')
    S3_REGION = os.environ.get('S3_REGION', 'us-east-1')  # Default region
    S3_KEY_PREFIX = os.environ.get('S3_KEY_PREFIX', '') 

    def __init__(self):
        # Small arguement resets active pickle. (In case uploads were aborted somehow)
        vpn_connected = False

        if len(sys.argv) > 1 and sys.argv[1] == 'reset':
            print('Reset pickle...')
            self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 0)

        active_script = self.pickle_load(self.PICKLE_ACTIVE_FILEPATH)

        if active_script == 0:
            try:
                print(self.check_conditions('folder'))
                print(self.check_conditions('usb'))
                self.clean_up()
                # Backup is now active. Prevent it from running again
                self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 1)

                backup_info = self.check_filesizes(self.PICKLE_FTP_FILEPATH)
                
                if backup_info[0] != 0:
                    self.compress_files(backup_info[0])

                    # Connect to the VPN if required
                    if self.USE_VPN:
                        self.connect_vpn()
                        vpn_connected = True

                    #USB backup
                    if self.check_conditions('usb'):
                        self.copy_to_usb()
                    #Folder backup
                    if self.check_conditions('folder'):
                        self.copy_to_folder()
                    #FTP backup
                    if self.check_conditions('sftp'):
                        self.upload_files()

                    folders_with_stat = self.get_folder_stats()
                    self.pickle_dump(self.PICKLE_FTP_FILEPATH, folders_with_stat)
                    self.clean_up()

                self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 0)
                print('All done!')
            except Exception as e:
                print(f"An error occured: {e}")
            finally:
                if self.USE_VPN and vpn_connected:
                    self.disconnect_vpn()
                self.clean_up();

    def check_filesizes(self, filepath):
        # Check if pickle file is empty
        if os.path.getsize(filepath) == 0:
            return [self.FOLDERS]
        
        filesizes_list = self.pickle_load(filepath)
        updated = []
        success = 0
        for folder in self.FOLDERS:
            size = self.folder_size(folder[0])
            for filesizes in filesizes_list:
                # if name matches and filesize isn't the same as the pickle file then send to backup
                if filesizes[0] == folder[0] and filesizes[2] != size:
                    success = 1
                    updated.append([folder[0], folder[1]])
        
        # Clean up old files, compress files, upload files, clean up again, and update the filesize pickle fileade
        if not success:
            return [0]

        return [updated]

    def check_conditions(self, ctype):
        if self.SFTP_BACKUP and ctype == 'sftp':
            return True

        if self.S3_BACKUP and ctype == 's3':
            return True

        if self.USB_BACKUP and os.path.ismount(self.USB_DIR) and ctype == 'usb':
            return True

        if self.FOLDER_BACKUP and os.path.exists(self.FOLDER_DIR) and ctype == 'folder':
            return True

        return False

    def compress_files(self,lists):
        """
        Compresses the files using 7z. Needs to figure out what OS it's using first before it does.
        """
        # Compress & encrypt files and save them inside tmp
        if sys.platform == "linux" or sys.platform == "linux2" or sys.platform == "darwin":
            # linux & mac (mac hasnt been tested)
            for item in lists:
                name = hashlib.md5(item[1].encode())
                rc = subprocess.call(['7z', 'a', '-p' + self.ENCRYPTION_KEY, '-y', self.TMP_FOLDER + name.hexdigest() + '.7z', '-xr!node_modules', '-xr!vendor', '-xr!_ignore_backup', '-mhe'] + [item[0]])
        elif sys.platform == "win32":
            #windows (windows hasnt been properely tested)
            for item in lists:
                name = hashlib.md5(item[1].encode())
                rc = subprocess.call(r'"C:\Program Files\7-zip\7z.exe" a -p' + self.ENCRYPTION_KEY + ' "' + self.TMP_FOLDER + name.hexdigest() + '.7z' + '" "' + item[0] + '" -mhe')
    
    def clean_up(self):
        """
        Cleans up the temp folder
        """
        print('Clean up files..')
        listdir = os.listdir(self.TMP_FOLDER)
        for item in listdir:
            os.remove(os.path.join(self.TMP_FOLDER, item))


    def copy_to_usb(self):
        """
        Copies the compressed files to to the defined USB drive
        """
        print("-- Backup to USB... --")
        listdir = os.listdir(self.TMP_FOLDER)
        for item in listdir:
            print('Copy: ' + item)
            shutil.copyfile(self.TMP_FOLDER + item, self.USB_DIR + item)

    def copy_to_folder(self):
        # Check first to make sure USB Backup is True and USB stick is plugged in
        print("-- Backup to Folder... --")
        if self.FOLDER_BACKUP and os.path.exists(self.FOLDER_DIR):
            print("-- Backup to folder... --")
            listdir = os.listdir(self.TMP_FOLDER)
            for item in listdir:
                print('Copy: ' + item)
                shutil.copyfile(self.TMP_FOLDER + item, self.FOLDER_DIR + item)

    def upload_files(self):
        """
        Uploads the file to S3 or SFTP
        """
        if self.SFTP_BACKUP:
            self.upload_via_sftp()
        if self.S3_BACKUP:
            self.upload_via_s3()

    def upload_via_sftp(self):
        """
        Uploads compressed files via SFTP
        """
        print("-- Backup to SFTP server... --")
        sftp_remote_upload_dir = os.environ.get('SFTP_REMOTE_UPLOAD_DIR', '')
        try:
            listdir = os.listdir(self.TMP_FOLDER)
            with pysftp.Connection(self.SFTP_HOST, username=self.SFTP_USER, password=self.SFTP_PASSWORD) as sftp:
                sftp.cwd(sftp_remote_upload_dir)  # Change to the remote upload directory
                for item in listdir:
                    print('Upload: ' + item)
                    sftp.put(self.TMP_FOLDER + item)
        except socket.error as e:
            print('Error on connect')

    def upload_via_s3(self): 
        """
        Uploads the compressed files to S3
        """
        # Amazon S3 backup
        print('-- Uploading files to Amazon S3... --')
        # Initialize the S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=self.S3_ACCESS_KEY,
            aws_secret_access_key=self.S3_SECRET_KEY,
            region_name=self.S3_REGION
        )

        listdir = os.listdir(self.TMP_FOLDER)
        for item in listdir:
            s3_key = os.path.join(self.S3_KEY_PREFIX, item) if self.S3_KEY_PREFIX else item
            file_path = os.path.join(self.TMP_FOLDER, item)
            try:
                print(f'Uploading {item} to s3://{self.S3_BUCKET}/{s3_key}')
                s3_client.upload_file(file_path, self.S3_BUCKET, s3_key)
            except Exception as e:
                print(f'Error uploading {item} to S3: {e}')


    def folder_size(self, path='.'):
        """
        Gets the folder size of a specific path
        @todo move this to a dedicated class
        """
        total = 0
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += self.folder_size(entry.path)
        return total

    def get_folder_stats(self):
        """
        Gets the folder size 
        @todo move this to a dedicated class
        """
        folders_with_stat = []
        for folder in self.FOLDERS:
            size = self.folder_size(folder[0])
            folders_with_stat.append([folder[0], folder[1], size])

        return folders_with_stat

    def pickle_load(self, filepath):
        with open(filepath, 'rb') as filesizes_pickle:
            filesizes_list = pickle.load(filesizes_pickle)
        return filesizes_list

    def pickle_dump(self, filepath, arr):
        with open(filepath, 'wb') as file:
            pickle.dump(arr, file)

    def connect_vpn(self):
        print("Connecting to VPN...")
        with open("vpn_auth.txt", "w") as auth_file:
            auth_file.write(self.VPN_USERNAME + "\n")
            auth_file.write(self.VPN_PASSWORD)

        cmd = ["sudo", "openvpn", "--config", self.VPN_OVPN_FILE, "--auth-user-pass", "vpn_auth.txt", "--daemon"]
        subprocess.run(cmd, check=True)
        os.remove("vpn_auth.txt")

        time.sleep(10)  # Wait for the VPN connection to establish
        print("Connected to VPN.")

    def disconnect_vpn(self):
        print("Disconnecting from VPN...")
        cmd = ["sudo", "killall", "openvpn"]
        subprocess.run(cmd, check=True)
        print("Disconnected from VPN.")


backup = Backup()
