import subprocess
import hashlib
import os

class Compressor:
    def __init__(self, encryption_key, tmp_folder):
        self.encryption_key = encryption_key
        self.tmp_folder = tmp_folder

    def compress(self, folder):
        folder_path = folder[0]
        folder_name = folder[1]
        name_hash = hashlib.md5(folder_name.encode()).hexdigest()
        output_file = os.path.join(self.tmp_folder, f"{name_hash}.7z")
        cmd = [
            '7z', 'a',
            f'-p{self.encryption_key}',
            '-y',
            output_file,
            '-xr!node_modules', '-xr!vendor', '-xr!_ignore_backup',
            '-mhe',
            folder_path
        ]
        try:
            subprocess.check_call(cmd)
            print(f"Compressed {folder_name} to {output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            print(f"Error compressing {folder_name}: {e}")
            return None

