#!/usr/bin/python3 
from ftplib import FTP_TLS
import zipfile
import os
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

	FTP_HOST = '192.168.1.xxx'
	FTP_USER = 'NAME'
	FTP_PASSWORD = ''

	ENCRYPTION_KEY = ''

	TMP_FOLDER = '/home/NAME/temp/'

	def __init__(self):
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
			
			# Dump to pickle file if there's a change made
			if success:
				self.compress_files(updated)
				self.upload_files()
				self.clean_up()
				self.pickle_dump()

		else:
			#dump to pickle file if the pickle file doesnt exist or is empty
			self.compress_files(self.FOLDERS)
			self.upload_files()
			self.clean_up()
			self.pickle_dump()

		print('All done!')

	def compress_files(self,lists):
		# Compress & encrypt files and save them inside tmp
		for item in lists:
				name = hashlib.md5(item[1].encode())
				#rc = subprocess.call(['7z', 'a', '-p' + self.ENCRYPTION_KEY, '-y', self.TMP_FOLDER + name.hexdigest() + '.7z', '-mhe'] + 
		        #             [item[0]])

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

	def pickle_load(self, filepath):
		filesizes_pickle = open(filepath,'rb')
		filesizes_list = pickle.load(filesizes_pickle)
		return filesizes_list

	def pickle_dump(self):
		folders_with_stat = []
		for folder in self.FOLDERS:
			size = self.folder_size(folder[0])
			folders_with_stat.append([folder[0], folder[1], size])

		file = open(self.PICKLE_FILEPATH,'wb')
		pickle.dump(folders_with_stat, file)



# Check to make server is up, if yes back up files! Test
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
try:
    s.connect(('192.168.1.131', 21))
    backup = Backup()
except socket.error as e:
    print("Error on connect")
s.close()