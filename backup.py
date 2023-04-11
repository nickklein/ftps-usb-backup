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
from dotenv import load_dotenv
load_dotenv()

# Put this in a class with picklein and out
class Backup:

	# Select all the directories that need to be backed up
	FOLDERS = [
		[os.path.expanduser('~/Desktop/'), 'Desktop'],
		[os.path.expanduser('~/Documents/'), 'Documents'],
		[os.path.expanduser('~/Music/'), 'Music'],
		[os.path.expanduser('~/Pictures/'), 'Pictures'],
		[os.path.expanduser('~/Videos/'), 'Videos'],
		[os.path.expanduser('~/Sites/'), 'Sites'],
		[os.path.expanduser('~/Backup/'), 'Backup'],
	]

	#File Paths to pickle files
	PICKLE_FTP_FILEPATH = os.environ.get('PICKLE_FTP_FILEPATH', '')
	PICKLE_ACTIVE_FILEPATH = os.environ.get('PICKLE_ACTIVE_FILEPATH', '')

	FTP_BACKUP = os.environ.get('FTP_BACKUP', 'true').lower() == 'true'
	FTP_HOST = os.environ.get('FTP_HOST', '')
	FTP_USER = os.environ.get('FTP_USER', '')
	FTP_PASSWORD = os.environ.get('FTP_PASSWORD', '')

	SFTP_BACKUP = os.environ.get('SFTP_BACKUP', 'true').lower() == 'true'
	SFTP_HOST = os.environ.get('SFTP_HOST', '')
	SFTP_USER = os.environ.get('SFTP_USER', '')
	SFTP_PASSWORD = os.environ.get('SFTP_PASSWORD', '')

	USB_BACKUP = os.environ.get('USB_BACKUP', 'false').lower() == 'true'
	USB_DIR = os.environ.get('USB_DIR', '')

	FOLDER_BACKUP = os.environ.get('FOLDER_BACKUP', 'true').lower() == 'true'
	FOLDER_DIR = os.environ.get('FOLDER_DIR', '')

	ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '')

	TMP_FOLDER = os.environ.get('TMP_FOLDER', '')


	def __init__(self):
		# Small arguement resets active pickle. (In case uploads were aborted somehow)
		if len(sys.argv) > 1 and sys.argv[1] == 'reset':
			print('Reset pickle...')
			self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 0)

		active_script = self.pickle_load(self.PICKLE_ACTIVE_FILEPATH)

		if active_script == 0:
			self.clean_up()
			# Backup is now active. Prevent it from running again
			self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 1)

			backup_info = self.check_filesizes(self.PICKLE_FTP_FILEPATH)
			
			if backup_info[0] != 0:
				self.compress_files(backup_info[0])

				#USB backup
				if self.check_conditions('usb'):
					self.copy_to_usb()
				
				#Folder backup
				if self.check_conditions('folder'):
					self.copy_to_folder()

				#FTP backup
				if self.check_conditions('ftp'):
					self.upload_files()

				folders_with_stat = self.get_folder_stats()
				self.pickle_dump(self.PICKLE_FTP_FILEPATH, folders_with_stat)
				self.clean_up()

			self.pickle_dump(self.PICKLE_ACTIVE_FILEPATH, 0)
			print('All done!')

	def check_filesizes(self, filepath):
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
					return [updated]
				else:
					return [0]
			else:
				# Clean up old files, compress files, upload files, clean up again, and update the filesize pickle fileade
				return [self.FOLDERS]


	def check_conditions(self, ctype):
		success = False
		if self.FTP_BACKUP and ctype == 'ftp':
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(5)
			#check network backup
			try:
			    s.connect((self.FTP_HOST, 21))
			    success = True
			except socket.error as e:
				pass
			s.close()

		if self.USB_BACKUP and ctype == 'usb':
			if os.path.ismount(self.USB_DIR):
				success = True

		if self.FOLDER_BACKUP and ctype == 'folder':
			if os.path.exists(self.FOLDER_DIR):
				success = True

		if self.SFTP_BACKUP:
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
		print('clean up')
		listdir = os.listdir(self.TMP_FOLDER)
		for item in listdir:
			os.remove(os.path.join(self.TMP_FOLDER, item))


	def copy_to_usb(self):
		# Check first to make sure USB Backup is True and USB stick is plugged in
		if self.USB_BACKUP and os.path.ismount(self.USB_DIR):
			print('copy to usb')
			listdir = os.listdir(self.TMP_FOLDER)
			for item in listdir:
				print('Copy: ' + item)
				shutil.copyfile(self.TMP_FOLDER + item, self.USB_DIR + item)

	def copy_to_folder(self):
		# Check first to make sure USB Backup is True and USB stick is plugged in
		if self.FOLDER_BACKUP and os.path.exists(self.FOLDER_DIR):
			print('copy to folder')
			listdir = os.listdir(self.TMP_FOLDER)
			for item in listdir:
				print('Copy: ' + item)
				shutil.copyfile(self.TMP_FOLDER + item, self.FOLDER_DIR + item)

	def upload_files(self):
		print('upload files')
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
		with open(filepath, 'rb') as filesizes_pickle:
			filesizes_list = pickle.load(filesizes_pickle)
		return filesizes_list

	def pickle_dump(self, filepath, arr):
		with open(filepath, 'wb') as file:
			pickle.dump(arr, file)


backup = Backup()
