#!/usr/bin/python3 
from ftplib import FTP_TLS
import zipfile
import os
import sys
import pickle
import subprocess
import hashlib
import socket
import shutil



# Put this in a class with picklein and out
class Backup:

	# Select all the directories that need to be backed up
	FOLDERS = [
        ['/home/NAME/Desktop/', 'Desktop'],
        ['/home/NAME/Documents/', 'Documents'],
        ['/home/NAME/Music/', 'Music'],
        ['/home/NAME/Pictures/', 'Pictures'],
        ['/home/NAME/Videos/', 'Videos']
	]

	#File Paths to pickle files
	PICKLE_FTP_FILEPATH = 'pickles/ftp_filesizes.pickle'
	PICKLE_USB_FILEPATH = 'pickles/usb_filesizes.pickle'	
	PICKLE_ACTIVE_FILEPATH = 'pickles/active.pickle'

	FTP_BACKUP = True
	FTP_HOST = '192.168.1.xxx'
	FTP_USER = 'NAME'
	FTP_PASSWORD = ''

	SFTP_BACKUP = True
	SFTP_HOST = '192.168.1.xxx'
	SFTP_USER = 'NAME'
	SFTP_PASSWORD = ''

	USB_BACKUP = True
	USB_DIR = '/media/NAME/usb-backup/'

	ENCRYPTION_KEY = ''

	TMP_FOLDER = '/home/NAME/temp/'


	def __init__(self):
		# Small arguement resets active pickle. (In case uploads were aborted somehow)
		if len(sys.argv) > 1 and sys.argv[1] == 'reset':
			print('Reset pickle...')
			self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 0)

		active_script = self.pickle_load(self.PICKLE_ACTIVE_FILEPATH)

		if active_script is 0:
			# Backup is now active. Prevent it from running again
			self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 1)

			#FTP backup
			if self.check_conditions('ftp'):
				backup_info = self.check_filesizes(self.PICKLE_FTP_FILEPATH, 'ftp')
				self.start_backup(backup_info)

			#USB backup
			if self.check_conditions('usb'):
				backup_info = self.check_filesizes(self.PICKLE_USB_FILEPATH, 'usb')
				self.start_backup(backup_info)

			self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 0)
			print('All done!')

	def check_filesizes(self, filepath, bktype):
			# Check if pickle file is empty
			if os.path.getsize(filepath) > 0:
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
				if success:
					return [updated, filepath, bktype]
				else:
					return [0, filepath, bktype]
			else:
				# Clean up old files, compress files, upload files, clean up again, and update the filesize pickle fileade
				return [self.FOLDERS, filepath, bktype]

	def start_backup(self, info):
		self.clean_up()
		# Only execute if there has been changes in one fo the folders
		if info[0] is not 0:
			self.compress_files(info[0])
			if info[2] is 'usb':
				self.copy_to_usb()
			if info[2] is 'ftp':
				self.upload_files()
			self.clean_up()

			# Save updated folder sizes to pickle file for next run
			folders_with_stat = self.get_folder_stats()
			self.pickle_dump(info[1], folders_with_stat)


	def check_conditions(self, ctype):
		success = False
		if self.FTP_BACKUP and ctype is 'ftp':
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(5)
			#check network backup
			try:
			    s.connect((self.FTP_HOST, 21))
			    success = True
			except socket.error as e:
				pass
			s.close()

		if self.USB_BACKUP and ctype is 'usb':
			if os.path.ismount(self.USB_DIR):
				success = True

		return success

	def compress_files(self,lists):
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
		listdir = os.listdir(self.TMP_FOLDER)
		for item in listdir:
			os.remove(self.TMP_FOLDER + item)


	def copy_to_usb(self):
		# Check first to make sure USB Backup is True and USB stick is plugged in
		if self.USB_BACKUP and os.path.ismount(self.USB_DIR):
			listdir = os.listdir(self.TMP_FOLDER)
			for item in listdir:
				print('Copy: ' + item)
				shutil.copyfile(self.TMP_FOLDER + item, self.USB_DIR + item)

	def upload_files(self):
		if self.FTP_BACKUP:
			# Check to make server is up, if yes back up files! Test
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(5)
			try:
			    s.connect((self.FTP_HOST, 21))

			    listdir = os.listdir(self.TMP_FOLDER)

			    ftps = FTP_TLS(self.FTP_HOST)
			    ftps.login(self.FTP_USER, self.FTP_PASSWORD)
			    ftps.set_pasv(True)

			    for item in listdir:
			    	print('Upload: ' + item)
			    	ftps.storbinary('STOR ' + item, open(self.TMP_FOLDER + item,'rb'), 1024)

			    ftps.quit()
			except socket.error as e:
				print("Error on connect")
			s.close()

		if self.SFTP_BACKUP:
			try:
				listdir = os.listdir(self.TMP_FOLDER)
				with pysftp.Connection(self.SFTP_HOST, username=self.SFTP_USER, password=self.SFTP_PASSWORD) as sftp:
					for item in listdir:
						print('Upload: ' + item)
						sftp.put(self.TMP_FOLDER + item)
			except socket.error as e:
				print('Error on connect')



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


backup = Backup()