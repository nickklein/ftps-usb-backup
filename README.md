# ftps-usb-backup
Compress &amp; Encrypt, then upload it to your local FTPS or USB drive. I use this script to backup my files to USB stick and a computer on my local network.

Requirements:
1. Python3
2. 7-zip (Linux, Mac, Windows)
3. Computer with FTPS set up OR USB drive

## How to install 7-zip:
### Linux:
Go to terminal and install the following package
```sudo apt-get install p7zip-full```
### Windows:
Navigate to the [7-zip website](https://www.7-zip.org/download.html), download the .exe file and install it to your computer

## How to configure it
1. Fill out the folders that you would like to backup
2. The path to the pickle file
3. FTPS information
4. Encryption Key
5. A temp folder where 7z files temporarily get stored while they are being uploaded

## How to run it
Go to your terminal and type in the following
```python3 path/to/backup.py```

You can also set up a cron job for it
```/usr/bin/python3 /path/to/backup/backup.py```
