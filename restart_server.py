
import subprocess
import os
from subprocess import CalledProcessError
import time
import sys
from pathlib import PureWindowsPath
from src.core import *
##THIS ENTIRE SCRIPT WILL BE REPLACED IN FUTURE VERSIONS
##WITH A MORE ROBUST CMDLINE UTILITY IN PROGRESS WHICH WILL CONSOLIDATE
##ALL ARTILLERY CMDLINE TOOLS INTO ONE UTILITY DEALING WITH SERVICE MANAGEMENT
##THIS INCLUDES THE ABILITY TO START, STOP, RESTART AND CHECK SERVICE STATUS 
#THIS FILE WILL BE UPDATED TO USE THE SAME METHODS AS SERVICEMANAGER FROM TRAY APP


#set some stuff up just for windows
if 'win32' in sys.platform:
    import win32gui
    import win32process
    from win32api import GetUserNameEx
    from src.pyuac import isUserAdmin, runAsAdmin
    
    EXE_PATH = settings.get_config('global',"APP_PATH")
    EXE_FILE = settings.get_config('global',"APP_FILE")
    PID_INFO_PATH = settings.get_config('global',"PIDFILE")
    PID = []
    #userneme in domain\user format
    U_INFO = GetUserNameEx(2)


def GrabBootLoader():
    '''looks for artillery window process and returns id. it checks
     for console version 1st and then ui version. Returns None if not found.'''
    try:
        if win32gui.FindWindow('ConsoleWindowClass', 'Artillery - Advanced Threat Detection'):
            hwnd = win32gui.FindWindow('ConsoleWindowClass', 'Artillery - Advanced Threat Detection')
            threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
            #return a string to use with taskkill
            return str(pid)
        else:
            if win32gui.FindWindow(None, 'Artillery Shell'):
                hwnd = win32gui.FindWindow(None, 'Artillery Shell')
                threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
                #return a string to use with taskkill
                return str(pid)
    except win32gui.error as err:
        return False


def kill_artillery_win():
    '''opens pid.txt file made from artillery.exe or artilleryui.exe to grab current
    PID to terminate. Note pyinstaller exe's create 2 running instances.
    1 for bootloader and 1 for actual code. for this to work we need to kill both'''
    try:
        if os.path.isfile(PID_INFO_PATH):
            log_event("[*] Finding Process info.....", 0, None, True)
            #grab bootloader id
            bootloader = GrabBootLoader()
            #read main id from file
            with open(PID_INFO_PATH, 'r') as p_id:
                for line in p_id:
                    line = line.strip()
                    PID.append(line)
            p_id.close()
            mainwindow = PID[0]
            if bootloader:
                #this could all be condensed into one call but for clarity
                log_event("[*] Bootloader ProcessID: " + bootloader, 0, None, True)
                log_event("[*] MainWindow ProcessID: " + mainwindow, 0, None, True)
                log_event('[*] Attempting to kill Artillery now.....', 0, None, True)
                log_event("[!] killing python with a big sword.....", 0, None, True)
                try:
                    #kill boot loader that was found.
                    kill_bootloader = subprocess.check_call(['cmd', '/C', 'taskkill', '/PID', bootloader], shell=True)
                    log_event("[!] Sucessfully removed it's head.....", 0, None, True)
                    #ArtilleryStopEvent()
                    return True
                except CalledProcessError as err:
                    log_event("[*] Looks like this process is dead already.", 0, None, True)
                    return False
            else:
                log_event("[!] Bootloader process not present.....", 0, None, True)
                return False
        else:
            log_event('[*] pid.txt was not found\n[*] Artillery must be run @ least once.......', 1, None, True)
            pause = input("[*] File was not found press enter to quit:")
    except FileNotFoundError as err:
        pass


def restart_artillery_win():
    '''restarts main exe by calling after waiting a few seconds
    to allow previous instance if any to close down'''
    # check to see if artillery is running
    check = kill_artillery_win()
    if check:
        log_event("[!] Process Killed\n[*] Launching now..... ", 0, None, True)
        subprocess.call(['cmd', '/C', 'cls'])
        #make sure proccess is dead wait a sec
        time.sleep(1)
        try:
            if os.path.isdir(EXE_PATH):
                #opens exe in seperate window
                os.system(f"start cmd /K artillery_start.bat")
                return
            else:
                pause = input('[*] artillery_start.bat was not found. Please make sure the file exists.\n[*] Press enter to continue')
        except FileNotFoundError as e:
            pass
    else:
        log_event("[*] Launching now..... ", 0, None, True)
        time.sleep(3)
        try:
            if os.path.isdir(EXE_PATH):
                #opens exe in seperate window
                os.system("start cmd /K artillery_start.bat")
            else:
                pause = input('[*] artillery_start.bat was not found. Please make sure the file exists.\n[*] Press enter to continue')
        except FileNotFoundError as e:
            pass


def main():
    cmd = ""
    try:
        cmd = input("[*] Restart Artillery instance?:\n[*] Kill Artillery instance?:\n[*] Type restart or kill respectivley\n[*] Type exit to quit\n[*] \\:")
    except Exception as e:
        print(str(e))
    result = cmd
    if result == 'kill':
        kill_artillery_win()
        looper()
    elif result == 'restart':
        restart_artillery_win()
        looper()
    elif result == 'exit':
        log_event("Closing software please wait.....", 0, None, True)
        time.sleep(3)
        sys.exit()
    else:
        log_event(f"[!] Unknown command: {cmd}", 1, None, True)
        looper()


def looper():
    main()


if __name__ == "__main__":
    if 'win32' in sys.platform:
        if not isUserAdmin():
            runAsAdmin()
            sys.exit(1)
        if isUserAdmin():
            time.sleep(2)
            log_event(f"[*] Running as: {U_INFO}", 0, None, True)
            looper()
    if ('linux' or 'linux2' or 'darwin') in sys.platform:
        # kill running instance of artillery
        kill_artillery()
        #
        if os.path.isfile("/var/artillery/artillery.py"):
            log_event("Restarting the Artillery Server process...",0,None,True)
            subprocess.Popen(["python3", "/var/artillery/artillery.py", "&"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
