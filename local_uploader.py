import shutil

class LocalUploader:
    def __init__(self, destination_path):
        self.destination_path = destination_path

    def upload(self, file_path):
        try:
            filename = os.path.basename(file_path)
            dest_file = os.path.join(self.destination_path, filename)
            shutil.copyfile(file_path, dest_file)
            print(f"Copied {filename} to {self.destination_path}")
        except Exception as e:
            print(f"Local copy failed: {e}")
