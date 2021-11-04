# Project Artillery - A project by Binary Defense Systems (https://www.binarydefense.com).

=======
Artillery is a combination of a honeypot, monitoring tool, and alerting system. Eventually this will evolve into a hardening monitoring platform as well to detect insecure configurations from nix and windows systems. It's relatively simple, run ```./setup.py``` and hit yes, this will install Artillery in ```/var/artillery``` and edit your ```/etc/init.d/rc.local``` on linux to start artillery on boot up. On windows it will be installed to ```\Program Files (x86)\Artillery``` and a batch file is included for startup

## Features

1. It sets up multiple common ports that are attacked. If someone connects to these ports, it blacklists them forever (to remove blacklisted ip's, On Linux remove them from ```/var/artillery/banlist.txt```. On Windows remove them from```\Program Files (x86)\Artillery\banlist.txt```)

2. It monitors what folders you specify for modifications.:
    - On linux by default it checks ```/var/www``` and ```/etc``` .
    - On windows by default it checks ```%temp%``` and ```%homepath%```

3. It monitors the SSH logs and looks for brute force attempts.(linux only)

4. It will email you when attacks occur and let you know what the attack was.

Be sure to edit the ```/var/artillery/config```on Linux or ```\Program Files (x86)\Artillery\config``` on Windows to turn on mail delivery, brute force attempt customizations, and what folders to monitor.

### Bugs and enhancements

For bug reports or enhancements, please open an issue here https://github.com/Russhaun/artillery/issues

#### Project structure
This is a port of (original repo) to run without python needing to be installed on host system. For those technical folks you can find all of the code in the following structure:

- ```Artillery.exe``` - main program file
- ```Restart.exe``` - handles restarting software
- ```Unban.exe``` - removes ips from banlist
- ```config```    - holds config settings
- ```/logs```     - holds log files
- ```/readme```   - changelog and license files
- ```/database``` - holds database for file monitoring
- ```src/windows``` - holds main windows files
- ```src/windows/source``` - current release sourcecode
- ```src/icons``` - holds icons for project
- ```artillery.msi``` - msi installer of current repo for windows systems

##### Supported platforms

- Windows
- Linux (in progress)

###### Windows installs

Manual method:
  Download files to location of your choice. extract contents of archive. copy contents to```"Program Files (x86)\Artillery```. once copied run "dll_reg.bat" (as admin) located in windows dir to register event dll. create shortcuts as needed.

MSI method:(preferred)
  Installer will put all files in thier proper location and also setup all shortcuts for app. ex: desktop/userfolder/startup. dll is automatically registered

###### Tested on/with

- win10 21h1 19043
- server 2012/16

###### Alpha testing
- Python 3.8.x
- pop_os
- parrot_os

###### Built with

- pyinstaller 4.5.1
- python 3.6
- visualstudio 2017 (event dll\msi)

###### Building project

###### requirements:

    - PyQT5
    - win10toast
    - pywin32 v228
    - pyinstaller 4.5.1
    - python 3.6
    - win10 sdk

  Note:
    the library win10toast is a custom one and different from the one on pip.please use this repo to install. https://github.com/russhaun/Windows-10-Toast-Notifications .This repo adds callbacks to class.

  Also:
    version of pywin32 is capped(for now @ 228) use binary installer from here. https://github.com/mhammond/pywin32/releases/tag/b228 . due to issues with parts of project breaking if upgraded. has to do with py 2.7 code still present. working on new branch now. install appropriate version for your platform ex: 32/64 bit

  navigate to windows folder of extacted repo. you will see a folder called "source" copy this folder to a place of your choosing rename if you wish.open a cmd prompt in this new location  and execute "pyinstaller artillery.spec" (without quotes)  when complete files will be located in "finalbuild" folder, this folder is created during build.this includes any src code as well. this project self replicates src\compiled binaries to finalbuild folder will improve as time goes on.
  
  msi is not in this package so u will have to manually copy files and register dll (working on setup.exe) for now it's a 2 step process

Binary Defense Systems (BDS) is a sister company of TrustedSec, LLC
