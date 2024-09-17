import pickle
import os

class StateManager:
    def __init__(self, active_filepath, ftp_filepath):
        self.active_filepath = active_filepath
        self.ftp_filepath = ftp_filepath

    def is_backup_active(self):
        if os.path.exists(self.active_filepath):
            with open(self.active_filepath, 'rb') as f:
                return pickle.load(f)
        else:
            return False

    def set_backup_active(self, active):
        with open(self.active_filepath, 'wb') as f:
            pickle.dump(active, f)

    def load_folder_sizes(self):
        if os.path.exists(self.ftp_filepath) and os.path.getsize(self.ftp_filepath) > 0:
            with open(self.ftp_filepath, 'rb') as f:
                try:
                    return pickle.load(f)
                except EOFError:
                    # The file is empty or corrupted
                    return []
        else:
            # File doesn't exist or is empty
            return []

    def save_folder_sizes(self, folder_sizes):
        with open(self.ftp_filepath, 'wb') as f:
            pickle.dump(folder_sizes, f)
