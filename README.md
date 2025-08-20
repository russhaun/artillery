# Project Artillery

Artillery is a combination of a honeypot, monitoring tool, and alerting system. Eventually this will evolve into a hardening monitoring platform as well to detect insecure configurations on windows systems. It's relatively simple, run ```Artillery.msi``` and follow the prompts, it will be installed to ```\Program Files (x86)\Artillery```.

## Features

1. It sets up multiple common ports that are attacked. If someone connects to these ports, it blacklists them forever (On Windows use ```Unban.exe <ip>``` to remove them from```\Program Files (x86)\Artillery\banlist.txt```)

2. It monitors what folders you specify for modifications.:
    - On windows by default it checks ```%temp%``` and ```%homepath%```

3. It will email you when attacks occur and let you know what the attack was.

4. Will alert with Toast Notifications and also event log

Be sure to edit ```\Program Files (x86)\Artillery\config``` on Windows to turn on mail delivery, and what folders to monitor.

### Bugs and enhancements

For bug reports or enhancements, please open an issue here https://github.com/Russhaun/artillery/issues

#### Project structure

This is a port of (original repo) to run without python needing to be installed on host system. There are some new features here that are not availible in upstream repo with more planned.For those technical folks you can find all of the code in the following structure:

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

##### Supported platforms

- Windows
- Linux (in progress)

###### Windows installs

Manual method:
  Download files to location of your choice. extract contents of archive. copy contents to```"Program Files (x86)\Artillery```. once copied run "dll_reg.bat" (as admin) located in windows dir of artillery to register event dll. create shortcuts as needed.

MSI method:(preferred)
  Installer will put all files in there proper location and also setup all shortcuts for app. ex: desktop/userfolder/startup. dll is automatically registered

note:

a setup.exe is in progress to address manual install including creating shortcuts and related settings

###### Tested on/with

- win10 22h2 19045
- server 2016/19
- python 3.10

###### Alpha testing

- python 3.12 (see below)
- pywin32 v30x (higher then current ver. some breaking changes need to be addressed)
- windows 11 and ^
- pop_os
- parrot_os
- kali

###### Built with

- pyinstaller 6.15
- python 3.10.0
- windows sdk 19041
- visualstudio 2019 (event dll\msi)

###### Building project

###### requirements:

    - pywin32 v302
    - pyinstaller 5.7 or higher
    - python 3.10.0 (python.org install. not microsoft store)
    - win10 19041 sdk

  Note:

  The version of pywin32 is capped(for now @ 302) use binary installer from here. https://github.com/mhammond/pywin32/releases/tag/b302 . python 2 support has been removed in this release. install appropriate version for your platform ex: 32/64 bit

  navigate to windows folder of extacted repo. you will see a folder called "source" copy this folder to a place of your choosing rename if you wish.open a cmd prompt in this new location  and execute "pyinstaller artillery.spec" (without quotes)  when complete files will be located in "finalbuild" folder, this folder is created during build.this includes any src code as well. this project self replicates src\compiled binaries to finalbuild folder will improve as time goes on. full instructions are in "build_instructions.txt"


  
  msi is not in this package so u will have to manually copy files and register dll (working on setup.exe) for now it's a 2 step process
