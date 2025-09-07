#!/usr/bin/python
#
# quick script for installing artillery. This file intentionally does not use any files from src directory
# while that might increase the file size and produce some code duplication in the end, 
# it makes setup much cleaner and seperate from artillery. no dependency issues or import problems
# also most functions that were added are mostly used in this file. this allows for setup to do "setup things"
# and artillery to do "artillery things".I lock the minimun version to 3.10.0(windows only) you can install anything later but,
# i cannot say it will work. I try to make sure you have the needed libraries when setup is done(windows). They get installed
# @ runtime if not present.
#
#
# As of this writing the highest version of python tested is 3.13.0
# and working on windows 10 and 11. This is also true for *nix systems
## Future versions will include a more robust install with options for custom install paths, firewall rules, and more
# #using argparse
#
## Modified by: Russ Haun (R0ach)
#import std libs needed
import time
import subprocess
import os
import shutil
import sys
import errno
import argparse
import traceback
import types
import platform

# Argument parse. Aimed to provide automatic deployment options
#do nothing with firewall
firewall = False
interactive = True  # Flag to select interactive install, typically prompting user to answer [y/n]
parser = argparse.ArgumentParser()
parser.add_argument("-y", action='store_true', help='silently installs\\uninstalls with automatic \'yes\' selection. must run with root/admin privileges')
parser.add_argument("-fw", action='store_true', help="Adds or removes firewall rules during setup on windows")
args = parser.parse_args()
if args.y:  # Check if non-interactive install argument is provided using an apt parameter style, -y
    interactive = False
if args.fw:
    #this will add/remove firewll rules if any
    firewall = True
install_banner = '''   
            Welcome to the Artillery installer.\n\n Artillery is a honeypot, file monitoring, and overall security tool\n used to protect your nix and windows systems using various methods.
                Written by: Dave Kennedy (ReL1K)
    '''
logfile = "setuplog.txt"
LOG_LOCATION = ""
#define some functions for use
if 'win32' in sys.platform:
    #used to search for installed libraries
    from importlib.metadata import version
    import importlib.util
    #
    def write_setup_log(line:str, console:bool):
        """Creates a log file specifically for setup in %TEMP% dir. 
        file is copied at end of setup to artillery log dir on install, 
        desktop on uninstall. Windows only for now will be updated in next release"""
        tempdir = os.environ["TEMP"]
        setuplog = os.path.join(tempdir,logfile)
        global LOG_LOCATION
        LOG_LOCATION = setuplog
        if not os.path.isfile(setuplog):
            with open(file=setuplog,mode='x',encoding='utf-8') as log:
                if console is True:
                    print(line)
                log.write("************Artillery setup log************"+"\n")
                log.write(line + "\n")
        else:
            with open(file=setuplog,mode='a',encoding='utf-8') as log:
                if console is True:
                    print(line)
                log.write(line + "\n")
    #
    def UninstallDLL():
        """Removes artillery event dll settings from the registry."""
        RemoveSourceFromRegistry(appName ="Artillery", eventLogType = "Application")
        if interactive:
            write_setup_log("[*] Removed event dll entries from registry",True)
        else:
            write_setup_log("[*] Removed event dll entries from registry",False)
    #
    def create_batch_file(path:str):
        """
            Creates batch file given the command to run.
            Used for Artillery in raw python versions
            to create artillery_start.bat
        """
        batch =":: script to start artillery\n"
        batch +="@echo off\n"
        batch +=f"python \"{path}\"\n"
        batch +="exit\n"
        batch +="exit\n"
        batch +="exit\n"
        return batch

    def get_artillery_dependencies():
        """
                This check is for the existence of some needed libraries for the install as well
            as artillery runtime itself. It will get the latest version for the python version running on host.
            specifically pywin32 and requests on Windows.This will breakout for both platforms at a point. 
            This can probably be done better it works with no issue with fresh install of python 3.13.0 
            windows. I am assuming a completly fresh install of python on host
        """
    
        #
        if interactive:
            write_setup_log("[*] Checking for needed libraries",True)
        else:
            write_setup_log("[*] Checking for needed libraries",False)
        #for some reason importlib.util.find_spec("pywin32") fails to find if installed??
        #so i use version and it does what i want? thanks python :((
        pywin32 = version('pywin32')
        if pywin32 is not None:
            #get the version
            pywin32_ver = version('pywin32')
            if interactive:
                write_setup_log(f"[*] pywin32 {pywin32_ver} is installed",True)
            else:
                 write_setup_log(f"[*] pywin32 {pywin32_ver} is installed",False)
        else:
            if interactive:
                write_setup_log("[*] pywin32 is not present installing",True)
            else:
                write_setup_log("[*] pywin32 is not present installing",False)
            subprocess.check_call([sys.executable,'-m','pip','install','pywin32'],shell=True)
        requests = importlib.util.find_spec("requests")
        if requests is not None:
            requests_ver = version("requests")
            if interactive:
                write_setup_log(f"[*] requests {requests_ver} is installed",True)
            else:
                write_setup_log(f"[*] requests {requests_ver} is installed",False)
        else:
            if interactive:
                write_setup_log("requests is not present installing",True)
            else:
                write_setup_log("requests is not present installing",False)
            subprocess.check_call([sys.executable,'-m','pip','install','requests'],shell=True)
        
    def make_shorcut(targetpath:str,shortcutname:str, icon ,description:str, args:str|None, destination:str|None):
        """
        Creates windows shorcuts for artillery given the path to exe, name, icon, description
        this will be used primarily in setup.py as with the msi installer this is done automagically.


            :param targetpath ex: "c:\\windows\\system32\\notepad.exe"
            :param shortcutname ex: "notepad.lnk"
            :param icon ex: "c:\\windows\\system32\\notepad.exe"
            :param description ex: "python created shorcut"
            :param args ex: "none"
            :param destination ex: "'desktop' where to place final shortcut. desktop//systray//artillery//startup"
        """
        if destination == 'desktop':
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")  # Path to the user's desktop
            full_path = os.path.join(desktop_path)
        #added for future inclusion of raw systray app
        elif destination == "systray":
            program_data = os.environ["ProgramData"]
            full_path = os.path.join(program_data, "Artillery","systray")
        elif destination == "artillery":
            program_files = os.environ["PROGRAMFILES(x86)"]
            full_path = os.path.join(program_files,"Artillery")
        elif destination == "startup":
            program_data = os.environ["ProgramData"]
            full_path = os.path.join(program_data, "Microsoft","Windows","Start Menu","Programs","Startup")
        #create final shortcut save path
        shortcut_path = os.path.join(full_path, shortcutname)
        shell = win32com.client.Dispatch("WScript.Shell")
        # Create the shortcut object
        shortcut = shell.CreateShortCut(shortcut_path)
        # Set shortcut properties
        shortcut.TargetPath = targetpath
        shortcut.WorkingDirectory = os.path.dirname(targetpath)#Set the working directory
        shortcut.Description = description
        #check for any arguments
        if args is None:
            pass
        else:
            shortcut.Arguments = args
        if icon == "" or None:
            pass
        else:
            shortcut.IconLocation = icon# Optional: Set a custom icon
        # Save the shortcut
        shortcut.save()

    
    def isUserAdmin():
        """@return: True if the current user is an 'Admin' whatever that
            means (root on Unix), otherwise False.

            Warning: The inner function fails unless you have Windows XP SP2 or
            higher. The failure causes a traceback to be printed and this
            function to return False.
        """

        if os.name == 'nt':

           import ctypes
        # WARNING: requires Windows XP SP2 or higher!
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            traceback.print_exc()
            print("Admin check failed, assuming not an admin.",flush=True)
            return False
        else:
        # Check for root on Posix
            return os.getuid() == 0


    def runAsAdmin(cmdLine=None, wait=False):
        """Attempt to relaunch the current script as an admin using the same
            command line parameters.  Pass cmdLine in to override and set a new
             command.  It must be a list of [command, arg1, arg2...] format.

            Set wait to False to avoid waiting for the sub-process to finish. You
            will not be able to fetch the exit code of the process if wait is
            False.

             Returns the sub-process return code, unless wait is False in which
             case it returns None.

             @WARNING: this function only works on Windows.
        """

        if os.name != 'nt':
                
                #raise RuntimeError, ("This function is only implemented on Windows.")
                #print("This function is only implemented on Windows.")
            raise RuntimeError("This function is only implemented on Windows.")
        import win32api
        import win32con
        import win32event
        import win32process
        from win32com.shell.shell import ShellExecuteEx
        from win32com.shell import shellcon

        python_exe = sys.executable

        if cmdLine is None:
            cmdLine = [python_exe] + sys.argv
        elif type(cmdLine) not in (types.TupleType, types.ListType):
            raise ValueError("cmdLine is not a sequence.")
        cmd = '"%s"' % (cmdLine[0],)
            # XXX TODO: isn't there a function or something we can call to massage command line params?
        params = " ".join(['"%s"' % (x,) for x in cmdLine[1:]])
        cmdDir = ''
        showCmd = win32con.SW_SHOWNORMAL
        lpVerb = 'runas'  # causes UAC elevation prompt.

            # print "Running", cmd, params

            # ShellExecute() doesn't seem to allow us to fetch the PID or handle
            # of the process, so we can't get anything useful from it. Therefore
            # the more complex ShellExecuteEx() must be used.

            # procHandle = win32api.ShellExecute(0, lpVerb, cmd, params, cmdDir, showCmd)

        procInfo = ShellExecuteEx(nShow=showCmd,
                                fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                                lpVerb=lpVerb,
                                lpFile=cmd,
                                lpParameters=params)

        if wait:
            procHandle = procInfo['hProcess']
            obj = win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
            rc = win32process.GetExitCodeProcess(procHandle)
            #print "Process handle %s returned code %s" % (procHandle, rc)
        else:
            rc = None

        return rc
    #
    if not isUserAdmin():
        runAsAdmin()  # will try to relaunch script as admin will prompt for user\pass and open in seperate window
        sys.exit(1)
    if isUserAdmin():
        if interactive:
            print(install_banner)
        else:
            pass
        #hard limit on version moving forward
        #will work in better logic to avoid issue
        if interactive:
            write_setup_log("[?] Checking python version",True)
        else:
            write_setup_log("[?] Checking python version",False)
        py_ver = platform.python_version_tuple()
        if py_ver[0] == "3":
            if py_ver[1] >= "10":
                if py_ver[2] >= "0":
                    if interactive:
                        write_setup_log(f"[*] Running python {platform.python_version()}",True)
                    else:
                        write_setup_log(f"[*] Running python {platform.python_version()}",False)
        else:
            #this should never be hit but,
            if interactive:
                write_setup_log(f"@ least python 3.10.0 required\nYour version: {platform.python_version()} exiting",True)
            else:
                write_setup_log(f"@ least python 3.10.0 required\nYour version: {platform.python_version()} exiting",False)
            sys.exit()
        #make sure we have everything we need before continuing
        get_artillery_dependencies()
        #start our imports
        from win32evtlogutil import RemoveSourceFromRegistry
        import requests
        import win32com.client
        #setup some constants
        SRC_PATH = os.getcwd()
        PROGRAM_DATA = os.environ["PROGRAMDATA"]
        PROGRAM_FILES = os.environ["PROGRAMFILES(X86)"]
        INSTALL_PATH = os.path.join(PROGRAM_FILES, "Artillery")
        #create loop for install/uninstall not perfect but works saves answer for next step
        if not os.path.isfile(os.path.join(INSTALL_PATH,"artillery.py")):
            if interactive:
                write_setup_log("[*] Running in interactive install mode ",True)
                answer = input("[*] Do you want to install Artillery [y/n]: ")
            else:
                #always print this line in silent mode
                write_setup_log("[*] Running in non interactive install mode with automatic \'yes\' selection",True)
                answer = 'y'
        #if above is false it must be installed so ask to uninstall
        else:
            if os.path.isfile(os.path.join(INSTALL_PATH,"artillery.py")) and interactive:
                write_setup_log("[*] Running in interactive uninstall mode ",True)
                answer = input("[*] Artillery detected. Do you want to uninstall [y/n:] ")
            else:
                #always print this line in silent mode
                write_setup_log("[*] Running in non interactive uninstall mode with automatic \'yes\' selection",True)
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
            print("You must be root to run this script!\r\n")
        sys.exit(1)
    print(install_banner)
    #if we are root create loop for install/uninstall not perfect but works saves answer for next step
    #all the following paths will be changed to os.path.join methods for posix platforms
    if not os.path.isfile("/etc/init.d/artillery"):
        if interactive:
            answer = input("Do you want to install Artillery and have it automatically run when you restart [y/n]: ")
        else:
            answer = 'y'
    #if above is true it must be installed so ask to uninstall
    else:
        #should we check for artillery.py instead?
        if os.path.isfile("/etc/init.d/artillery") and interactive:
            answer = input("[*] Artillery detected. Do you want to uninstall [y/n:] ")
        else:
            answer = 'y'
        #put this here to create loop
        if (answer.lower() in ["yes", "y"]) or not interactive:
            answer = "uninstall"

if answer.lower() in ["yes", "y"]:
    if ('linux' or 'linux2' or 'darwin') in sys.platform:
        print("[*] Beginning installation. This should only take a moment.")
        #replace root_check folder
        if not os.path.isdir("/var/artillery_check_root"):
            os.mkdir(path="/var/artillery_check_root")
            #set permisions to 700
            os.chmod("/var/artillery_check_root", 0o700)
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
    #Changed order of cmds. was giving error about file already exists.
    #also updated location to be the same accross all versions of Windows
    if 'win32' in sys.platform:
        if interactive:
            write_setup_log(f"[*] Copying files over to {INSTALL_PATH}",True)
        else:
            write_setup_log(f"[*] Copying files over to {INSTALL_PATH}",False)
        shutil.copytree(SRC_PATH, INSTALL_PATH)
        if interactive:
            write_setup_log("[*] Creating additional dirs",True)
        else:
            write_setup_log("[*] Creating additional dirs",False)
        os.makedirs(os.path.join(INSTALL_PATH, "logs"))
        os.makedirs(os.path.join(INSTALL_PATH,"database"))
        os.makedirs(os.path.join(INSTALL_PATH,"src","program_junk"))
        if interactive:
            write_setup_log("[*] Copy Complete",True)
        else:
            write_setup_log("[*] Copy Complete", False)
        #create .bat file for artillery so as to remove from repo
        #we know its not there just create it
        with open(file=os.path.join(INSTALL_PATH,"artillery_start.bat"), mode='x',encoding='utf-8') as startup:     
            contents = create_batch_file(path=os.path.join(INSTALL_PATH,"Artillery.py"))
            startup.write(contents)
        #create artillery desktop shortcut
        if interactive:
            write_setup_log("[*] Creating Artillery desktop shortcut",True)
        else:
            write_setup_log("[*] Creating Artillery desktop shortcut",False)
        make_shorcut(targetpath=os.path.join(INSTALL_PATH,"artillery_start.bat"),
                    shortcutname="artillery.lnk",
                    icon=os.path.join(INSTALL_PATH,"src","icons","bd_icon.ico"),
                    description="Artillery startup",
                    args=None,
                    destination='desktop')
        #create logon shorcut if you want
        if interactive:
            start_up = input("[*] Would you like to create a shorcut to start artillery @ user logon?.[y]")
        else:
            start_up = "y"
        if start_up == "y":
            if interactive:
                write_setup_log("[*] Creating startup shortcut",True)
            else:
                write_setup_log("[*] Creating startup shortcut",False)
            make_shorcut(targetpath=os.path.join(INSTALL_PATH,"artillery_start.bat"),
                    shortcutname="artillery.lnk",
                    icon=os.path.join(INSTALL_PATH,"src","icons","bd_icon.ico"),
                    description="Logon start",
                    args=None,
                    destination='startup')
        #create firewall rules if flag present
        #will probably put a check here for the rule even if flag is not passed at runtime
        #to prevent uneeded work
        #rules are automatically created by windows on launch but it says python in windows firewall
        #here it can be the same rule i just have control of the name i see
        if firewall is True:
            #artillery is installed at this point so make the rule
            if interactive:
                write_setup_log("Simulating creating incoming allow rule for artillery",True)
            else:
                write_setup_log("Simulating creating incoming allow rule for artillery",True)



    if ('linux' or 'linux2' or 'darwin') in sys.platform:
        if interactive:
            #this seems a little out of place if we just downloaded this were already on
            # latest plus we just copied everything over and created some extra stuff
            # this will be changed to a config flag in future we will just copy over 
            #like on windows to be consistent
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
            #create extra folders here if we select yes
            if not os.path.isdir("/var/artillery/database"):
                os.makedirs("/var/artillery/database")
            if not os.path.isdir("/var/artillery/src/program_junk"):
                os.makedirs("/var/artillery/src/program_junk")
        else:
            # extra folders exist here if we select no
            print("[*] Copying setup files over...")
            subprocess.Popen("cp -rf * /var/artillery/", shell=True).wait()
            #create extra folders here
            if not os.path.isdir("/var/artillery/database"):
                os.makedirs("/var/artillery/database")
            if not os.path.isdir("/var/artillery/src/program_junk"):
                os.makedirs("/var/artillery/src/program_junk")
        #would create base config here
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
        #added to start after install.launches in seperate window
        if 'win32' in sys.platform:
            #these will all be re-worked
            os.chdir("src\\windows")
            #register dll
            if interactive:
                write_setup_log("[*] Registering dll with system",True)
            else:
                write_setup_log("[*] Registering dll with system",False)
            subprocess.run(['cmd', '/C', 'reg', 'import', 'ArtilleryEvents.reg'],shell=True)
            time.sleep(1)
            if interactive:
                write_setup_log("[*] Artillery has been installed",True)
            else:
                write_setup_log("[*] Artillery has been installed",False)
            time.sleep(1)
            #launch from install dir
            if interactive:
                write_setup_log("[*] Launching artillery from install dir",True)
            else:
                write_setup_log("[*] Launching artillery from install dir",False)
            try:
                #launches artillery in a new process
                subprocess.call(['cmd', '/C', 'python', f"{INSTALL_PATH}\Artillery.py"],shell=True,creationflags=subprocess.DETACHED_PROCESS,timeout=3)
            except subprocess.TimeoutExpired:
                #will do a check to see if running for now i just pass
                pass
            #copy over the setup log and delete the original for future runs   
            if os.path.isfile(LOG_LOCATION):
                logdest = os.path.join(INSTALL_PATH,"logs")
                #always say where the logs are regardless of mode
                write_setup_log(f"[*] Setup complete copying logs to {logdest}",True)
                subprocess.call(['cmd', '/C', 'copy', LOG_LOCATION, logdest],shell=True)
                time.sleep(1)
                subprocess.call(['cmd', '/C', 'del', LOG_LOCATION],shell=True)
        #setup complete
            
    else:
        # n was pressed
        if ('linux' or 'linux2' or 'darwin') in sys.platform:
            print("[*] Installation complete. Edit /var/artillery/config in order to config artillery to your liking")
        if 'win32' in sys.platform:
            os.chdir("src\\windows")
            #register dll
            if interactive:
                write_setup_log("[*] Registering dll with system",True)
            else:
                write_setup_log("[*] Registering dll with system",False)
            time.sleep(1)
            subprocess.run(['cmd', '/C', 'reg', 'import', 'ArtilleryEvents.reg'],shell=True)
            if interactive:
                write_setup_log("[*] Artillery has been installed",True)
            else:
                write_setup_log("[*] Artillery has been installed",False)
            if os.path.isfile(LOG_LOCATION):
                logdest = os.path.join(INSTALL_PATH,"logs")
                #always say where the logs are regardless of mode
                write_setup_log(f"[*] Setup complete copying logs to {logdest}",True)
                subprocess.call(['cmd', '/C', 'copy', LOG_LOCATION, logdest],shell=True)
                time.sleep(1)
                subprocess.call(['cmd', '/C', 'del', LOG_LOCATION],shell=True)
    #setup complete
#added root check to uninstall for linux
if answer == "uninstall":
    if ('linux' or 'linux2' or 'darwin') in sys.platform:
        try:   # check if the user is root
            if os.path.isdir("/var/artillery_check_root"):
                os.rmdir('/var/artillery_check_root')
                # if not throw an error and quit
        except OSError as e:
            if (e.errno == errno.EACCES or e.errno == errno.EPERM):
                print("[*] You must be root to run this script!\r\n")
            sys.exit(1)
        else:  # remove all of artillery
            os.remove("/etc/init.d/artillery")
            subprocess.Popen("rm -rf /var/artillery", shell=True)
            subprocess.Popen("rm -rf /etc/init.d/artillery", shell=True)
            print("[*] Artillery has been uninstalled. Manually kill the process if it is still running.")
    #Delete routine to remove artillery on windows.added uac check
    if 'win32' in sys.platform:
        if not isUserAdmin():
            runAsAdmin()
        if isUserAdmin():
            #delete shortcuts(if exists)
            #we only create 2 shortcuts for now.
            #one on the desktop
            users_desktop = os.path.join(os.path.expanduser("~"), "Desktop")  # Path to the user's desktop
            desktop_path = os.path.join(users_desktop)
            desktop_link = os.path.join(desktop_path,"artillery.lnk")
            if os.path.isfile(desktop_link):
                if interactive:
                    write_setup_log("[*] Removing desktop shortcut",True)
                else:
                    write_setup_log("[*] Removing desktop shortcut",False)
                subprocess.call(['cmd', '/C', 'del', desktop_link])
            #samething for startup
            program_data = os.environ["ProgramData"]
            full_path = os.path.join(program_data, "Microsoft","Windows","Start Menu","Programs","Startup")
            startup_link = os.path.join(full_path,"artillery.lnk")
            if os.path.isfile(startup_link):
                if interactive:
                    write_setup_log("[*] Removing startup shortcut",True)
                else:
                    write_setup_log("[*] Removing startup shortcut",False)
                subprocess.call(['cmd', '/C', 'del', startup_link])
            
            #delete firewall rules
            #will probably put a check here for the rule even if flag is not passed at runtime
            if firewall is True:
                if interactive:
                    write_setup_log("[*] Simulating deleting firewall rules",True)
                else:
                    write_setup_log("[*] Simulating deleting firewall rules",False)
            #remove artillery files
            if interactive:
                write_setup_log(f"[*] Removing artillery files located in {INSTALL_PATH}",True)
            else:
                write_setup_log(f"[*] Removing artillery files located in {INSTALL_PATH}",False)
            subprocess.call(['cmd', '/C', 'rmdir', '/S', '/Q', INSTALL_PATH])
            #remove dll entries
            UninstallDLL()
            if os.path.isfile(LOG_LOCATION):
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")  # Path to the user's desktop
                logdest = os.path.join(desktop_path)
                if interactive:                                                          #this line will be removed as we will check and kill in future
                    write_setup_log("[*] Artillery has been uninstalled.\n[*] Manually kill the process if it is still running.",True)
                else:
                    write_setup_log("[*] Artillery has been uninstalled.\n[*] Manually kill the process if it is still running.",False)
                #always say where the logs are regardless of mode
                write_setup_log(f"[*] Uninstall complete copying logs to {logdest}",True)
                t = subprocess.check_output(['cmd', '/C', 'copy', LOG_LOCATION, logdest],shell=True)
                time.sleep(1)
                subprocess.call(['cmd', '/C', 'del', LOG_LOCATION],shell=True)
    #uninstall complete
