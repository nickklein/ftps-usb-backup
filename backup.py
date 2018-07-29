#!/usr/bin/python3 
from ftplib import FTP_TLS
import zipfile
import os
import sys
import pickle
import subprocess
import hashlib
import socket



# Put this in a class with picklein and out
class Backup:

	# Select all the directories that need to be backed up
	FOLDERS = [
        ['/home/NAME/Desktop/', 'Desktop'],
        ['/home/NAME/Documents/', 'Documents'],
        ['/home/NAME/Music/', 'Music'],
	]
	PICKLE_FILEPATH = '/home/NAME/Sites/ftps-backup/filesizes.pickle'
	PICKLE_ACTIVE_FILEPATH = '/home/NAME/Sites/ftps-backup/active.pickle'



	FTP_HOST = '192.168.1.xxx'
	FTP_USER = 'NAME'
	FTP_PASSWORD = ''

	ENCRYPTION_KEY = ''

	TMP_FOLDER = '/home/NAME/temp/'

	def __init__(self):
		active_script = self.pickle_load(self.PICKLE_ACTIVE_FILEPATH)

		if active_script is 0:
			# Backup is now active. Prevent it from running again
			self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 1)

			# Check if pickle file is empty
			if os.path.getsize(self.PICKLE_FILEPATH) > 0:
				filesizes_list = self.pickle_load(self.PICKLE_FILEPATH)


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
				if success:
					self.start_backup(updated)
			else:
				# Clean up old files, compress files, upload files, clean up again, and update the filesize pickle fileade
				self.start_backup(self.FOLDERS)

			self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 0)
			print('All done!')

	def start_backup(self,folders):
		self.clean_up()
		self.compress_files(folders)
		self.upload_files()
		self.clean_up()

		# Save updated folder sizes to pickle file for next run
		folders_with_stat = self.get_folder_stats()
		self.pickle_dump(self.PICKLE_FILEPATH, folders_with_stat)


	def compress_files(self,lists):
		# Compress & encrypt files and save them inside tmp

		if sys.platform == "linux" or sys.platform == "linux2" or sys.platform == "darwin":
		    # linux & mac (mac hasnt been tested)
			for item in lists:
					name = hashlib.md5(item[1].encode())
					rc = subprocess.call(['7z', 'a', '-p' + self.ENCRYPTION_KEY, '-y', self.TMP_FOLDER + name.hexdigest() + '.7z', '-mhe'] + [item[0]])
		elif sys.platform == "win32":
			#windows (windows hasnt been properely tested)
			for item in lists:
					name = hashlib.md5(item[1].encode())
					rc = subprocess.call(r'"C:\Program Files\7-zip\7z.exe" a -p' + self.ENCRYPTION_KEY + ' "' + self.TMP_FOLDER + name.hexdigest() + '.7z' + '" "' + item[0] + '" -mhe')
	
	def clean_up(self):
		listdir = os.listdir(self.TMP_FOLDER)
		for item in listdir:
			os.remove(self.TMP_FOLDER + item)


	def upload_files(self):
		listdir = os.listdir(self.TMP_FOLDER)

		ftps = FTP_TLS(self.FTP_HOST)
		ftps.login(self.FTP_USER, self.FTP_PASSWORD)
		ftps.set_pasv(True)

		for item in listdir:
			ftps.storbinary('STOR ' + item, open(self.TMP_FOLDER + item,'rb'), 1024)

		ftps.quit()


	def folder_size(self, path='.'):
	    total = 0
	    for entry in os.scandir(path):
	        if entry.is_file():
	            total += entry.stat().st_size
	        elif entry.is_dir():
	            total += self.folder_size(entry.path)
	    return total

	def get_folder_stats(self):
		folders_with_stat = []
		for folder in self.FOLDERS:
			size = self.folder_size(folder[0])
			folders_with_stat.append([folder[0], folder[1], size])

		return folders_with_stat

	def pickle_load(self, filepath):
		filesizes_pickle = open(filepath,'rb')
		filesizes_list = pickle.load(filesizes_pickle)
		return filesizes_list

	def pickle_dump(self, filepath, arr):
		file = open(filepath,'wb')
		pickle.dump(arr, file)




# Check to make server is up, if yes back up files! Test
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
try:
    s.connect(('192.168.1.xxx', 21))
    backup = Backup()
except socket.error as e:
    print("Error on connect")
s.close()