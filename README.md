# usbipdhelper
Connect and Disconnect USB Devices from your Hyper-V Virtual Machine without typing a million commands.

## Requirements on Host Machine
- Windows 10/11+ with Powershell Admin Privileges
- Python 3.13+ (Or Latest)
- pyuac
- pypiwin32
- paramiko
- [usbipd-win](https://github.com/dorssel/usbipd-win)
- Hyper-V
- Username and Password to the Virtual Machine SSH Server

## Requirements on Guest/Virtual Machine
- usbip
- SSH Server Daemon Running

## Installation

- Clone the repo & install dependencies w/ pip 
```
git clone https://github.com/dantefernando/usbipdhelper
cd usbipdhelper
pip install -r requirements.txt
```

## Setup (REQUIRED)

- Edit `ssh_credentials.py` to include your SSH `USERNAME` and `PASSWORD` for the Virtual Machine
- For Example:
```
USERNAME = "Dante"
PASSWORD = "myPassword123"
```

## Usage

- Change Directories to the cloned repo and Run `main.py`
```
python main.py
```


### Author

Written by Dante Fernando 2025
