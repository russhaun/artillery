'''
this is a reworked version of restart.py to add in windows.WIP
'''

import subprocess
import os
from subprocess import CalledProcessError
import time
import sys
from pathlib import PureWindowsPath
from src.config import is_windows_os, is_posix_os
from src.core import *

#set some stuff up just for windows
if is_windows_os is True:
    import win32gui
    import win32process
    from win32api import GetUserNameEx
    from src.pyuac import isUserAdmin, runAsAdmin
    EXE_FILE = "Artillery.py"
    EXE_PATH = str(globals.g_apppath)
    PID_INFO_PATH = globals.g_pidfile
    PID = []
    #userneme in domain\user format
    U_INFO = GetUserNameEx(2)


def grab_main_window():
    '''
     looks for artillery window by name and returns id. Returns False if not found.
    '''
    try:
        if win32gui.FindWindow('ConsoleWindowClass', 'Artillery - Advanced Threat Detection'):
            hwnd = win32gui.FindWindow('ConsoleWindowClass', 'Artillery - Advanced Threat Detection')
            threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
            #return true and a string to use with taskkill
            return (True,str(pid))
    except win32gui.error as err:
        return (False,0)


def kill_artillery_win():
    '''kills active artillery window returned from grab_main_window() and then restarts main
    artillery file'''
    mainwindow = grab_main_window()
    mainwindow_true = mainwindow[0]
    try:
        if mainwindow_true:
            write_console('[*] Finding Process info.....')
            processid =  mainwindow[1]
            #if mainwindow_true:
            write_console("[!] MainWindow ProcessID: " + str(processid))
            write_console('[*] Attempting to kill Artillery now.....')
            write_console("[!] killing python with a big sword.....")
            try:
                    #kill boot loader that was found.
                kill_bootloader = subprocess.check_call(['cmd', '/C', 'taskkill', '/PID', mainwindow[1]], shell=True)
                write_console("[!] Sucessflly removed it's head.....")
                return True
            except CalledProcessError as err:
                write_console("[*] Looks like this process is dead already. ")
                return False
        else:
            write_console("[!] Bootloader process not present.....") 
            return False
    # else:
    #     write_console('[*] pid.txt was not found\n[*] Artillery must be run @ least once.......')
    #     pause = input("[*] File was not found press enter to quit:")
    except FileNotFoundError as err:
        pass


def restart_artillery_win():
    '''restarts main file by calling after waiting a few seconds
    to allow previous instance if any to close down'''
    # check to see if artillery is running
    check = kill_artillery_win()
    if check:
        write_console("[!] Process Killed\n[*] Launching now..... ")
        #make sure proccess is dead wait a sec
        time.sleep(1)
        try:
            if os.path.isdir(EXE_PATH):
                binary = PureWindowsPath(EXE_PATH, EXE_FILE)
                #opens exe in seperate window
                subprocess.Popen(["python",str(binary)], creationflags=subprocess.CREATE_NEW_CONSOLE)
                return
            else:
                pause = input('[*] artillery.py was not found. Please make sure the file exists.\n[*] Press enter to continue')
        except FileNotFoundError as e:
            pass
    else:
        write_console("[*] Launching now..... ")
        time.sleep(3)
        try:
            if os.path.isdir(EXE_PATH):
                binary = PureWindowsPath(EXE_PATH, EXE_FILE)
                #opens exe in seperate window
                subprocess.Popen(["python",str(binary)], creationflags=subprocess.CREATE_NEW_CONSOLE)
                return
            else:
                pause = input('[*] artillery.py was not found. Please make sure the file exists.\n[*] Press enter to continue')
        except FileNotFoundError as e:
            pass






if __name__ == "__main__":
    if is_windows_os is True:
        if not isUserAdmin():
            runAsAdmin()
            sys.exit(1)
        if isUserAdmin():
            time.sleep(2)
            write_console(f"[*] Running as: {U_INFO}")
            restart_artillery_win()
    #
    #
    if is_posix_os is True:
        # kill running instance of artillery
        kill_artillery()
        #
        if os.path.isfile("/var/artillery/artillery.py"):
            print(f"[*] {grab_time()}: Restarting Artillery Server...")
            write_log("Restarting the Artillery Server process...", 1)
            subprocess.Popen(["python3", "/var/artillery/artillery.py", "&"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
