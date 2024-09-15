from dotenv import load_dotenv
import os
load_dotenv()

class ConfigManager:
    def __init__(self):
        load_dotenv()
        self.load_config()

    def load_config(self):
        # General settings
        self.ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')
        self.TMP_FOLDER = os.getenv('TMP_FOLDER', '')
        self.PICKLE_ACTIVE_FILEPATH = os.getenv('PICKLE_ACTIVE_FILEPATH', '')
        self.PICKLE_FTP_FILEPATH = os.getenv('PICKLE_FTP_FILEPATH', '')
        self.FOLDERS = [
            [os.path.expanduser('~/Backup/'), 'Backup'],
            # [os.path.expanduser('~/Desktop/'), 'Desktop'],
            # [os.path.expanduser('~/Documents/'), 'Documents'],
            # [os.path.expanduser('~/Music/'), 'Music'],
            # [os.path.expanduser('~/Pictures/'), 'Pictures'],
            # [os.path.expanduser('~/Videos/'), 'Videos'],
            # [os.path.expanduser('~/Sites/'), 'Sites'],
        ]

        # Backup destinations
        self.load_backup_destinations()

    def load_backup_destinations(self):
        self.backup_destinations = []

        # SFTP settings
        if os.getenv('SFTP_BACKUP', 'false').lower() == 'true':
            self.backup_destinations.append('sftp')
            self.SFTP_HOST = os.getenv('SFTP_HOST', '')
            self.SFTP_USER = os.getenv('SFTP_USER', '')
            self.SFTP_PASSWORD = os.getenv('SFTP_PASSWORD', '')
            self.REMOTE_UPLOAD_DIR = os.getenv('REMOTE_UPLOAD_DIR', '')

        # S3 settings
        if os.getenv('S3_BACKUP', 'false').lower() == 'true':
            self.backup_destinations.append('s3')
            self.S3_BUCKET = os.getenv('S3_BUCKET', '')
            self.S3_KEY_PREFIX = os.getenv('S3_KEY_PREFIX', '')
            self.S3_REGION = os.getenv('S3_REGION', 'us-east-1')
            self.S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY', '')
            self.S3_SECRET_KEY = os.getenv('S3_SECRET_KEY', '')

        # USB backup
        if os.getenv('USB_BACKUP', 'false').lower() == 'true':
            self.backup_destinations.append('usb')
            self.USB_DIR = os.getenv('USB_DIR', '')

        # Folder backup
        if os.getenv('FOLDER_BACKUP', 'false').lower() == 'true':
            self.backup_destinations.append('folder')
            self.FOLDER_DIR = os.getenv('FOLDER_DIR', '')


