import os

class FolderManager:
    def __init__(self, folders, tmp_folders):
        self.folders = folders
        self.tmp_folders = tmp_folders

    def get_folder_size(self, path):
        total = 0
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += self.get_folder_size(entry.path)
        return total

    def get_folder_stats(self):
        folders_with_stat = []
        for folder in self.folders:
            size = self.get_folder_size(folder[0])
            folders_with_stat.append([folder[0], folder[1], size])
        return folders_with_stat

    def get_folders_to_backup(self, current_stats, previous_stats):
        folders_to_backup = []
        previous_sizes = {folder[0]: folder[2] for folder in previous_stats}
        for folder in current_stats:
            path, name, size = folder
            previous_size = previous_sizes.get(path)
            if previous_size != size:
                folders_to_backup.append([path, name])
        print(folders_to_backup)
        return folders_to_backup

    def clean_up(self):
        listdir = os.listdir(self.tmp_folders)
        for item in listdir:
            os.remove(os.path.join(self.tmp_folders, item))
