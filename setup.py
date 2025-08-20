#!/usr/bin/python
#
# quick script for installing artillery
#

import time
import subprocess
import os
import shutil
import sys
import errno
import argparse
import traceback
import types

# Argument parse. Aimed to provide automatic deployment options
interactive = True  # Flag to select interactive install, typically prompting user to answer [y/n]
parser = argparse.ArgumentParser()
parser.add_argument("-y", action='store_true', help='silently installs\\uninstalls with automatic \'yes\' selection. must run with root/admin privileges')
args = parser.parse_args()
if args.y:  # Check if non-interactive install argument is provided using an apt parameter style, -y
    print("Running in non interactive mode with automatic \'yes\' selection")
    interactive = False

#define some functions for use
if 'win32' in sys.platform:
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
        print('''   
            Welcome to the Artillery installer.\n\n Artillery is a honeypot, file monitoring, and overall security tool\n used to protect your nix and windows systems using various methods.
                Written by: Dave Kennedy (ReL1K)
    ''')
    #setup some constants
    SRC_PATH = os.getcwd()
    PROGRAM_FILES = os.environ["PROGRAMFILES(X86)"]
    INSTALL_PATH = os.path.join(PROGRAM_FILES, "Artillery")
    #create loop for install/uninstall not perfect but works saves answer for next step
    if not os.path.isfile(os.path.join(INSTALL_PATH,"artillery.py")):
        if interactive:
            answer = input("[*] Do you want to install Artillery [y/n]: ")
        else:
            answer = 'y'
    #if above is false it must be installed so ask to uninstall
    else:
        if os.path.isfile(os.path.join(INSTALL_PATH,"artillery.py")) and interactive:
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
            print("You must be root to run this script!\r\n")
        sys.exit(1)
    print('''   
            Welcome to the Artillery installer.\n\n Artillery is a honeypot, file monitoring, and overall security tool\n used to protect your nix and windows systems using various methods.
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
            os.makedirs("/var/artillery_check_root")
        #these folders below can be created after base files are present
        #either from git clone or copying from this installer they will be moved at a later date
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
    #Changed order of cmds. was giving error about file already exists.
    #also updated location to be the same accross all versions of Windows
    if 'win32' in sys.platform:
        shutil.copytree(SRC_PATH, INSTALL_PATH)
        os.makedirs(os.path.join(INSTALL_PATH, "logs"))
        os.makedirs(os.path.join(INSTALL_PATH,"database"))
        os.makedirs(os.path.join(INSTALL_PATH,"src","program_junk"))
        #because artillery ships with no config write out base file
        #(just the header)so when artillery runs something is there
        #it will populate itself.this will be broken out so both platforms 
        # can use it
        conf_file = os.path.join(INSTALL_PATH,"config")
        #setup our banner
        banner = "#############################################################################################\n"
        banner += "#\n"
        banner += "# This is the Artillery configuration file. Change these variables and flags to change how\n"
        banner += "# this behaves.\n"
        banner += "#\n"
        banner += "# Artillery written by: Dave Kennedy (ReL1K)\n"
        banner += "# Website: https://www.binarydefense.com\n"
        banner += "# Email: info [at] binarydefense.com\n"
        banner += "# Download: git clone https://github.com/binarydefense/artillery artillery/\n"
        banner += "# Install: python setup.py\n"
        banner += "#\n"
        banner += "#############################################################################################\n"
        banner += "#\n"
        #we kow its not there just create it
        with open(file=conf_file,mode="x",encoding="utf-8") as conf:
            conf.write(banner)
        #create firewall rules,shorcuts here?
        

    if ('linux' or 'linux2' or 'darwin') in sys.platform:
        if interactive:
            #this seems a little out of place if we just downloaded this were already on
            # latest. this will be changed to a config flag in future we will just copy over 
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
            #would create extra folders here
        else:
            print("[*] Copying setup files over...")
            subprocess.Popen("cp -rf * /var/artillery/", shell=True).wait()
            #would create extra folders here
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
            # this cmd is what they were refering to as "no longer supported"? from update-rc.d on install.
            # It looks like service starts but you have to manually launch artillery
            subprocess.Popen("/etc/init.d/artillery start", shell=True).wait()
            print("[*] Installation complete. Edit /var/artillery/config in order to config artillery to your liking")
        #added to start after install.launches in seperate window
        if 'win32' in sys.platform:
            os.chdir("src\\windows")
            #copy over banlist
            #this will be removed
            os.system("start cmd /K banlist.bat")
            #Wait to make sure banlist is copied over
            time.sleep(2)
            #launch from install dir
            os.system("start cmd /K launch.bat")
            #cleanup cache folder
            time.sleep(2)
            os.system("start cmd /K del_cache.bat")


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
            #delete firewall rules,shortcuts and startup task (if exists)
            #remove program files
            subprocess.call(['cmd', '/C', 'rmdir', '/S', '/Q', INSTALL_PATH])
            #del uninstall cache
            os.chdir("src\\windows")
            os.system("start cmd /K del_cache.bat")
            #just so they can see this message sleep a sec
            print("[*] Artillery has been uninstalled.\n[*] Manually kill the process if it is still running.")
            time.sleep(3)
