import pysftp
import os

class SFTPUploader:
    def __init__(self, host, user, password, remote_dir):
        self.host = host
        self.user = user
        self.password = password
        self.remote_dir = remote_dir

    def upload(self, file_path):
        try:
            with pysftp.Connection(self.host, username=self.user, password=self.password) as sftp:
                sftp.cwd(self.remote_dir)
                filename = os.path.basename(file_path)
                sftp.put(file_path)
                print(f"Uploaded {filename} to SFTP server")
        except Exception as e:
            print(f"SFTP upload failed: {e}")
