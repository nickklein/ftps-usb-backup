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
        base_dir = folder[2] if len(folder) > 2 else '/'

        name_hash = hashlib.md5(folder_name.encode()).hexdigest()
        output_file = os.path.join(self.tmp_folder, f"{name_hash}.7z")
        # Calculate the relative path from the base directory
        relative_path = os.path.relpath(folder_path, base_dir)

        # Change working directory to the base directory
        current_dir = os.getcwd()
        os.chdir(base_dir)

        cmd = [
            '7z', 'a',
            f'-p{self.encryption_key}',
            '-y',
            output_file,
            '-xr!node_modules', '-xr!vendor', '-xr!_ignore_backup',
            '-mhe',
            relative_path
        ]
        try:
            subprocess.check_call(cmd)
            print(f"Compressed {folder_name} to {output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            print(f"Error compressing {folder_name}: {e}")
            return None
        finally:
            os.chdir(current_dir)

