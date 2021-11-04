
import subprocess
import os
from subprocess import CalledProcessError
import time
import sys
from pathlib import PureWindowsPath
from src.globals import  *
from src.core import *
#init_globals, is_windows, is_posix, kill_artillery, write_log, write_console, grab_time
try:
    init_globals()
except Exception as e:
    write_console(e)
#set some stuff up just for windows
if is_windows():
    import win32gui
    import win32process
    from win32api import GetUserNameEx
    from src.pyuac import isUserAdmin, runAsAdmin
    from src.events import ArtilleryStopEvent
    EXE_FILE = "Artillery.exe"
    EXE_PATH = str(globals.g_apppath)
    PID_INFO_PATH = globals.g_pidfile
    PID = []
    #userneme in domain\user format
    U_INFO = GetUserNameEx(2)

def GrabBootLoader():
    '''looks for artillery window process and returns id. it checks
     for console version 1st and then ui version. Returns None if not found.'''
    try:
        if win32gui.FindWindow('ConsoleWindowClass', 'Artillery - Advanced Threat Detection'):
            hwnd = win32gui.FindWindow('ConsoleWindowClass', 'Artillery - Advanced Threat Detection')
            threadid,pid = win32process.GetWindowThreadProcessId(hwnd)
            #return a string to use with taskkill
            return str(pid)
        else:
            if win32gui.FindWindow(None, 'Artillery Shell'):
                hwnd = win32gui.FindWindow( None, 'Artillery Shell')
                threadid,pid = win32process.GetWindowThreadProcessId(hwnd)
                #return a string to use with taskkill
                return str(pid)
    except win32gui.error as err:
        return False
#
def kill_artillery_win():
    '''opens pid.txt file made from artillery.exe or artilleryui.exe to grab current
    PID to terminate. Note pyinstaller exe's create 2 running instances.
    1 for bootloader and 1 for actual code. for this to work we need to kill both'''
    try:
        if os.path.isfile(PID_INFO_PATH):
            write_console('[*] Finding Process info.....')
            #grab bootloader id
            bootloader = GrabBootLoader()
            #read main id from file
            with open(PID_INFO_PATH, 'r') as id:
                for line in id:
                    line = line.strip()
                    PID.append(line)
            id.close()
            mainwindow = PID[0]
            if bootloader:
                write_console("[!] Bootloader ProcessID: "+ bootloader)
                write_console("[*] MainWindow ProcessID: "+ mainwindow)
                write_console('[*] Attempting to kill Artillery now.....')
                write_console("[!] killing python with a big sword.....")
                try:
                    #kill boot loader that was found.
                    kill_bootloader = subprocess.check_call(['cmd', '/C', 'taskkill', '/PID', bootloader], shell=True)
                    write_console("[!] Sucessflly removed it's head.....")
                    #subprocess.run(['cmd','/C', 'tasklist', '/FI', 'imagename eq ArtilleryUI.exe'])
                    ArtilleryStopEvent()
                    return True
                except CalledProcessError as err:
                    write_console("[*] Looks like this process is dead already. ")
                    return False
            else:
                write_console("[!] Bootloader process not present.....")
                return False
        else:
            write_console('[*] pid.txt was not found\n[*] Artillery must be run @ least once.......')
            pause = input("[*] File was not found press enter to quit:")
    except FileNotFoundError as err:
        pass

def restart_artillery_win():
    '''restarts main exe by calling after waiting a few seconds
    to allow previous instance if any to close down'''
    # check to see if artillery is running
    check = kill_artillery_win()
    if check:
        write_console("[!] Process Killed\n[*] Launching now..... ")
        subprocess.call(['cmd', '/C', 'cls'])
        #make sure proccess is dead wait a sec
        time.sleep(1)
        try:
            if os.path.isdir(EXE_PATH):
                binary = PureWindowsPath(EXE_PATH,EXE_FILE)
                #opens exe in seperate window
                subprocess.Popen([str(binary)], creationflags=subprocess.CREATE_NEW_CONSOLE)
                return
            else:
                pause = input('[*] artillery_start.bat was not found. Please make sure the file exists.\n[*] Press enter to continue')
        except FileNotFoundError as e:
            pass
    else:
        write_console("[*] Launching now..... ")
        time.sleep(3)
        try:
            if os.path.isdir(EXE_PATH):
                binary = PureWindowsPath(EXE_PATH,EXE_FILE)
                #opens exe in seperate window
                subprocess.Popen([str(binary)], creationflags=subprocess.CREATE_NEW_CONSOLE)
                return
            else:
                pause = input('[*] artillery_start.bat was not found. Please make sure the file exists.\n[*] Press enter to continue')
        except FileNotFoundError as e:
            pass
#
#
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
        write_console("Closing software please wait.....")
        time.sleep(3)
        sys.exit()
    else:
        write_console("[!] Unknown command: " +cmd)
        looper()


def looper():
    main()



if __name__ == "__main__":
    if is_windows():
        if not isUserAdmin():
            runAsAdmin()
            sys.exit(1)
        if isUserAdmin():
            time.sleep(2)
            write_console(f"[*] Running as: {U_INFO}")
            looper()
           