##!/usr/bin/python
#
# quick script for installing artillery. This version has been modified to not depend on any src files for use.
# I predifine some things to allow not needing the files to operate process is exactly the same as before in the end
# 
#

import time
import subprocess
import re
import os
import shutil
import sys
import errno
import argparse
#
#
if 'win32' in sys.platform:
    #pyuac wil be moved into setup to remove need on src files maybe
    from src.pyuac import isUserAdmin, runAsAdmin # UAC Check Script found it here.https://gist.github.com/Preston-Landers/267391562bc96959eb41 all credit goes to him.
    import win32evtlog
    from win32evtlogutil import ReportEvent
    from win32api import GetCurrentProcess
    from win32security import GetTokenInformation, TokenUser, OpenProcessToken
    from win32con import TOKEN_READ
    
# Argument parse. Aimed to provide automatic deployment options
interactive = True # Flag to select interactive install, typically prompting user to answer [y/n]
parser = argparse.ArgumentParser(description='-y, optional non interactive install/uninstall with automatic \'yes\' selection. It must roon with root/admin privileges')
parser.add_argument("-y", action='store_true')
args = parser.parse_args()
if args.y: # Check if non-interactive install argument is provided using an apt parameter style, -y
    print("Running in non interactive mode with automatic \'yes\' selection")
    interactive = False;

# Check to see if we are admin
if 'win32' in sys.platform:
    if not isUserAdmin():
        runAsAdmin()
        sys.exit(1)
    if isUserAdmin():
        AppName = "Artillery"
        category = int(1)
        data = "Application\0Data".encode("ascii")
        process = GetCurrentProcess()
        info = win32evtlog.EVENTLOG_INFORMATION_TYPE
        token = OpenProcessToken(process, TOKEN_READ)
        my_sid = GetTokenInformation(token, TokenUser)[0]
        src_path = os.getcwd()
        program_files = os.environ["PROGRAMFILES(X86)"]
        install_path = program_files + "\\Artillery"
        #new path used for holding event dll 
        # and other related files for artillery on windows
        program_data = os.environ["PROGRAMDATA"]
        event_dll = src_path+"\\src\\windows\\ArtilleryEvents.dll"
       
        #define some events for use in setup
        def artillery_installed():
            '''writes event that Artillery has been installed'''
            eventID=502
            ReportEvent(AppName, eventID, eventCategory=int(category), eventType=info, data=data, sid=my_sid)

        def artillery_uninstalled():
            '''writes event that Artillery has been uninstalled'''
            eventID=503
            ReportEvent(AppName, eventID, eventCategory=int(category), eventType=info, data=data, sid=my_sid)

        def add_dll_registry_keys():
            '''imports .reg file containing eventdll settings. For now dll lives next to artillery files
             Will be moved to system32 folder in future release.
            '''
            file_name = "src\\windows\\ArtilleryEvents.reg"
            print("[*] Adding registry entries for event dll")
            subprocess.run(['cmd', '/C', 'reg', 'import', src_path+"\\"+file_name], check=False)
        
        print('''
Welcome to the Artillery installer. Artillery is a honeypot, file monitoring, and overall security tool used to protect your nix and windows systems.

Written by: Dave Kennedy (ReL1K)
''')
#create loop for install/uninstall not perfect but works saves answer for next step
    if not os.path.isfile(install_path+"\\artillery.py"):
        if interactive:
            answer = input("[*] Do you want to install Artillery [y/n]: ")
        else:
            answer = 'y'
    #if above is false it must be installed so ask to uninstall
    else:
        if os.path.isfile( install_path +"\\artillery.py") and interactive:
            #print("[*] [*] If you would like to uninstall hit y then enter")
            answer = input("[*] Artillery detected. Do you want to uninstall [y/n:] ")
        else:
            answer = 'y'
        #put this here to create loop
        if (answer.lower() in ["yes", "y"]) or not interactive:
            answer = "uninstall"


# Check to see if we are root
if ('linux' or 'linux2' or 'darwin') in sys.platform:
    try:   # and delete folder
        if os.path.isdir("/var/artillery_check_root"):
            os.rmdir('/var/artillery_check_root')
            #if not thow error and quit
    except OSError as e:
        if (e.errno == errno.EACCES or e.errno == errno.EPERM):
            print ("You must be root to run this script!\r\n")
        sys.exit(1)
    print('''
Welcome to the Artillery installer. Artillery is a honeypot, file monitoring, and overall security tool used to protect your nix systems.

Written by: Dave Kennedy (ReL1K)
''')
#if we are root create loop for install/uninstall not perfect but works saves answer for next step
    if not os.path.isfile("/etc/init.d/artillery"):
        if interactive:
            answer = input("Do you want to install Artillery and have it automatically run when you restart [y/n]: ")
        else:
            answer = 'y'
    #if above is true it must be installed so ask to uninstall
    else:
        if os.path.isfile("/etc/init.d/artillery") and interactive:
            answer = input("[*] Artillery detected. Do you want to uninstall [y/n:] ")
        else:
            answer = 'y'
        #put this here to create loop
        if (answer.lower() in ["yes", "y"]) or not interactive:
            answer = "uninstall"

if answer.lower() in ["yes", "y"]:
    if ('linux' or 'linux2' or 'darwin') in sys.platform:
        #kill_artillery()

        print("[*] Beginning installation. This should only take a moment.")

        # if directories aren't there then create them
        #make root check folder here. Only root should
        #be able to create or delete this folder right?
        # leave folder for future installs/uninstall?
        if not os.path.isdir("/var/artillery_check_root"):
            os.makedirs("/var/artillery_check_root")
        if not os.path.isdir("/var/artillery/database"):
            os.makedirs("/var/artillery/database")
        if not os.path.isdir("/var/artillery/src/program_junk"):
            os.makedirs("/var/artillery/src/program_junk")

        # install to rc.local
        print("[*] Adding artillery into startup through init scripts..")
        if os.path.isdir("/etc/init.d"):
            if not os.path.isfile("/etc/init.d/artillery"):
                fileopen = open("src/startup_artillery", "r")
                config = fileopen.read()
                filewrite = open("/etc/init.d/artillery", "w")
                filewrite.write(config)
                filewrite.close()
                print("[*] Triggering update-rc.d on artillery to automatic start...")
                subprocess.Popen(
                    "chmod +x /etc/init.d/artillery", shell=True).wait()
                subprocess.Popen(
                    "update-rc.d artillery defaults", shell=True).wait()

            # remove old method if installed previously
            if os.path.isfile("/etc/init.d/rc.local"):
                fileopen = open("/etc/init.d/rc.local", "r")
                data = fileopen.read()
                data = data.replace(
                    "sudo python /var/artillery/artillery.py &", "")
                filewrite = open("/etc/init.d/rc.local", "w")
                filewrite.write(data)
                filewrite.close()
        #move code up from below to copy src files from archive over here and
        #remove the update from git use that in main artillery code
        #pretty sure something exists already for that in core.py?
    
    if 'win32' in sys.platform:
        print(f"[*] copying src files to.....{install_path}")
        shutil.copytree(src_path, install_path)
        os.makedirs(install_path + "\\logs")
        os.makedirs(install_path + "\\database")
        os.makedirs(install_path + "\\src\\program_junk")
        if os.path.isdir(program_data + "\\Artillery"):
            #must be previous install just copy over files
            pass
        else:
            #must be new install create path and copy over files
            print("[*] Creating ProgramData folder")
            os.makedirs(program_data + "\\Artillery")
        #register dll with windows
        add_dll_registry_keys()
        #copy over banlist
        #this will change to a function @ some point
        print("[*] Copying over banlist")
        #change to windows dir for rest of setup
        os.chdir("src\\windows")
        os.system("start cmd /K banlist.bat")
        #write event that artillery is installed
        artillery_installed()
        print("[*] Finished")


    if ('linux' or 'linux2' or 'darwin') in sys.platform:
        #do we really want to do it like this it pulls from github. looks to be more
        #suitible as a config flag? we should just copy over the archive here as we do with windows
        if interactive:
            choice = input("[*] Do you want to keep Artillery updated? (requires internet) [y/n]: ")
        else:
            choice = 'y'
        if choice in ["y", "yes"]:
            print("[*] Checking out Artillery through github to /var/artillery")
            # if old files are there
            if os.path.isdir("/var/artillery/"):
                shutil.rmtree('/var/artillery')
            subprocess.Popen(
                "git clone https://github.com/binarydefense/artillery /var/artillery/", shell=True).wait()
            print("[*] Finished. If you want to update Artillery go to /var/artillery and type 'git pull'")
        else:
            print("[*] Copying setup files over...")
            subprocess.Popen("cp -rf * /var/artillery/", shell=True).wait()

        # if os is Mac Os X than create a .plist daemon - changes added by
        # contributor - Giulio Bortot
        if os.path.isdir("/Library/LaunchDaemons"):
            # check if file is already in place
            if not os.path.isfile("/Library/LaunchDaemons/com.artillery.plist"):
                print("[*] Creating com.artillery.plist in your Daemons directory")
                filewrite = open(
                    "/Library/LaunchDaemons/com.artillery.plist", "w")
                filewrite.write('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0">\n<dict>\n<key>Disabled</key>\n<false/>\n<key>ProgramArguments</key>\n<array>\n<string>/usr/bin/python</string>\n<string>/var/artillery/artillery.py</string>\n</array>\n<key>KeepAlive</key>\n<true/>\n<key>RunAtLoad</key>\n<true/>\n<key>Label</key>\n<string>com.artillery</string>\n<key>Debug</key>\n<true/>\n</dict>\n</plist>')
                print("[*] Adding right permissions")
                subprocess.Popen(
                    "chown root:wheel /Library/LaunchDaemons/com.artillery.plist", shell=True).wait()

    if interactive:
        choice = input("[*] Would you like to start Artillery now? [y/n]: ")
    else:
        choice = 'y'
    if choice in ["yes", "y"]:
        if ('linux' or 'linux2' or 'darwin') in sys.platform:
            subprocess.Popen("/etc/init.d/artillery start", shell=True).wait()
            print("[*] Installation complete. Edit /var/artillery/config in order to config artillery to your liking")
            #
        if 'win32' in sys.platform:
            time.sleep(2)
            #launch from install dir
            print("[*} attempting to launch artillery")
            os.system("start cmd /K launch.bat")
            #cleanup cache folder
            time.sleep(2)
            os.system("start cmd /K del_cache.bat")


#added root check to uninstall for linux
if answer == "uninstall":
    if ('linux' or 'linux2' or 'darwin') in sys.platform:
        try:   #check if the user is root
            if os.path.isdir("/var/artillery_check_root"):
                os.rmdir('/var/artillery_check_root')
               #if not throw an error and quit
        except OSError as e:
            if (e.errno == errno.EACCES or e.errno == errno.EPERM):
                print ("[*] You must be root to run this script!\r\n")
            sys.exit(1)
        else:# remove all of artillery
            os.remove("/etc/init.d/artillery")
            subprocess.Popen("rm -rf /var/artillery", shell=True)
            subprocess.Popen("rm -rf /etc/init.d/artillery", shell=True)
            #kill_artillery()
            print("[*] Artillery has been uninstalled. Manually kill the process if it is still running.")
    #Delete routine to remove artillery on windows.added uac check
    if 'win32' in sys.platform:
        if not isUserAdmin():
            runAsAdmin()
        if isUserAdmin():
            #write event that artillery has been removed
            artillery_uninstalled()
            time.sleep(2)
            #remove program files
            print("[*] Deleting artillery files.....")
            subprocess.call(['cmd', '/C', 'rmdir', '/S', '/Q', install_path])
            #del uninstall cache
            os.chdir("src\\windows")
            print("[*] deleting cache")
            os.system("start cmd /K del_cache.bat")
            #just so they can see this message sleep a sec
            print("[*] Artillery has been uninstalled.\n[*] Manually kill the process if it is still running.")
            time.sleep(2)
