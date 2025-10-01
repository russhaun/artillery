Project Artillery
=======
Artillery is a combination of a honeypot, monitoring tool, and alerting system. Eventually this will evolve into a hardening monitoring platform as well to detect insecure configurations from nix and windows systems. 

Download zip archive to location of your choice unzip the file. Open a cmd prompt browse to directory that files are located and run  ```python ./setup.py``` and hit yes, or ```python ./setup.py -y```(silent install). 

On Linux this will install Artillery in ```/var/artillery``` and edit your ```/etc/init.d/rc.local``` to start artillery on boot up. 

On Windows this will install Artillery in ```\Program Files (x86)\Artillery``` a desktop shorcut is created to launch. Also creates a shortcut in users startup folder to launch when they log in. 


### Features

1. It sets up multiple common ports that are attacked. If someone connects to these ports, it blacklists them forever.To add/remove blacklisted ip's use:
 
   - ```python remove_ban.py ban\unban ipaddress``` .
   
   Works on routing table(default) or firewall/Iptables(if enabled) from the config

2. It monitors what folders you specify.
   - On linux by default it checks ```/var/www``` and ```/etc``` .       
   - On windows by default it checks ```%temp%``` which points to```\Users\<username>\AppData\Local\Temp```.

3. It monitors the SSH/FTP logs and looks for brute force attempts.(linux only)

4. It monitors apache web servers ERROR and ACCESS logs.

5. Can log to local/remote Syslog, File or Windows event logs.

6. Blocks offenders using mutiple methods on Linux uses routing table and IpTables. On Windows  uses routing table and windows firewall(experimental)

7. Updates banlist from multiple sources can add more sources to config

8. Can act as a threatserver. Meaning you can host your banlist for others to use

9. Monitors for denial-of-service attempts and then throttles offenders(linux only)

10. Runs checks for insecure service settings SSH/FTP(linux),SMB/LLMNR/WPAD(windows)

11. Set customizable alert messages in config file.

12. Supports Ipv4 tcp/udp connections.(Ipv6 servers are present but experimental at this time)


Be sure to edit the ```/var/artillery/config```on Linux or ```\Program Files (x86)\Artillery\config``` on Windows to turn on mail delivery, brute force attempt customizations, and what folders to monitor.


### Project structure

For those technical folks you can find all of the code in the following structure:

- ```Artillery.py``` - main program file
- ```restart_server.py``` - handles stop/start/restart of software
- ```remove_ban.py``` - adds/removes ips from/to banlist also winfirewall/Iptables 
- ```src/anti_dos.py``` - main monitoring module for Dos attacks
- ```src/apache_monitor.py``` - main monitoring module for Apache web service
- ```src/config.py``` - main module for handling configuration settings
- ```src/email_handler.py``` - main module for handling email
- ```src/ftp_monitor.py``` - main monitoring module for FTP bruteforcing
- ```src/core.py``` - main central code reuse for things shared between each module
- ```src/monitor.py``` - main monitoring module for changes to the filesystem
- ```src/ssh_monitor.py``` - main monitoring module for SSH brute forcing
- ```src/honeypot.py``` - main module for honeypot detection
- ```src/harden.py``` - check for basic hardening to the OS
- ```database/integrity.data``` - main database for maintaining sha512 hashes of filesystem
- ```setup.py``` - handles installing software

### Screenshots

### Requirements

- python 3.10.0 (minimum version supported)
- pwin32(windows) 
- requests

note:
    On windows setup.py will attempt to install missing dependencies if they are not there.
    This assumes a default install of python 3.10.0.


### Supported platforms

- Linux
- Windows

### Bugs and enhancements

Binary Defense Systems (BDS) (https://www.binarydefense.com) is a sister company of TrustedSec, LLC


For bug reports or enhancements, please open an issue here https://github.com/BinaryDefense/artillery/issues


