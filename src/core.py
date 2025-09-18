# #################################core module for reusable / central code####################################
#  All std libs used throughout software are located in this file
# no need to import in new modules. From new module just do 'from .core import 'modulename''
# assuming your module is in src/ folder and you will get every thing in here.
#
#   If your module needs third party libs include them in that file only
# by using is_windows()/is_posix() functions to avoid platform issues 
# if there is a std lib you need post a msg and it will be added . 
# some libs appear greyed out that only means the lib is not used in this file
# but is used in other modules that import core.py
# this is done to keep all std lib imports in one place for easy management
# and uneeded import checks.
#
#   @ runtime during import of this file __init__.py is called first. 
# It imports config.py which will load all settings into a global ditionary.
# If no config file or any files for that matter that artillery needs.
# If not there creates it. ex:alert/runtime/exception/banlist/localbanlist logs
# this eliminates most code that checks for a file because they are just there.
# regardless if user deleted them or not, and platform differences.
# 
#   This way all modules can just import settings from core and grab any setting they need and do work. 
# By doing settings.get_config('section','option') returns value.
# sections are:
#  
#    'global' global holds thing such as app_path,app_name,log_path etc.
#    'current' holds all user configurable options such as honeypot ports,ban options, alerting options found at runtime in config file.
# 
#     ex: settings.get_config('global','APP_PATH')
#  
# There is also settings.is_config_enabled('option') for on/off options. returns True or False
#
#    'option' refers to setting in config fie'

#     ex:  settings.is_config_enabled("ENABLE_HONEYPOT")
#
#   There is also settings.get_enabled_services() function(working but not in use yet).
# which when run returns a tuple of 4 dicts which are:
#
#       AVAILIBLE_SERVICES  #all settings artillery knows about basically the whole config file
#       ENABLED_SERVICES    #all services that return 'ON'
#       DISABLED_SERVICES   #all services that return 'OFF'
#       CONFIGURATION_SETTINGS #all txt related values in config.
#   
#   This will eventually allow me in the future to just pass settings to the modules themselves
# they will just do what the settings given tell them
# With these i will be able to further automate loading artillery by reducing
# checks for config
#
# 
# This will make it easy to add new settings on the fly if needed.
# All settings are stored in memory after initial load.
# A config read is done ONCE at runtime
# sorry if this is long winded i felt the need to explian the changes
# these are architectual changes in the way imports are done
##############################################################################################################

from re import U
import argparse
import errno
import subprocess
import time
import re
import os
import hashlib
import _thread as thread
import threading
import sys
import shutil
import socket
import socketserver as SocketServer
from socket import socket as _socket
import platform
from requests import Request, Session
import logging
import logging.handlers
import datetime
import signal
from string import *
import string
from zipfile import ZipFile
from logging.handlers import SMTPHandler
import random
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

#Import new settings class. import into other files from here.
# ex from .core import settings
from . import settings,write_configuration_log
#define these as soon as possible
def is_posix():
    '''returns true platform is posix related'''
    return os.name == "posix"
#
def is_windows():
    '''returns true platform is Windows related'''
    return os.name == "nt"
if is_windows():
    from win32api import SetConsoleTitle, GetCurrentProcessId,GetUserName
    from win32evtlogutil import ReportEvent, SafeFormatMessage,FormatMessage
    from win32api import GetCurrentProcess
    from win32security import GetTokenInformation, TokenUser, OpenProcessToken
    from win32con import TOKEN_READ
    import win32con
    import win32evtlog
    import win32gui
    import win32security
    from winreg import *
    from pathlib import PureWindowsPath
    import pywintypes
    import win32file
    #import win32con as con
    import ntsecuritycon as con
    import win32process
    import win32com.client as win32comclient
    import win32file
    import win32pipe
    import win32event
    import winerror
    
    def write_windows_eventlog(AppName: str, eventID: int, event_type: int, send_toast: bool, ip: None, msg:str|None):
        """
            Writes an event to windows event log using custom dll

            values:
                - AppName = name of app in windows eventlog
                - eventid = eventid to use
                - event_type = type of alert to use  info,warning,err
                - send_toast = send toast alert or not. values accepted TRUE FALSE
                - ip = used for toast alerts if enabled can be None
                - msg = the msg you want to appear in the details section of event default if None

            event types:
                possible event types are.

                - "win32evtlog.EVENTLOG_INFORMATION_TYPE"
                -  "win32evtlog.EVENTLOG_WARNING_TYPE"
                -  "win32evtlog.EVENTLOG_ERROR_TYPE"


            messages:
                all mesages are stored in dll. possible entries for func are as follows
                Future events are planned. for now the msg's are hard coded
                -    Event,                  eventid,           type
                - ######################################################
                - ARTILLERY_START            100              info
                - ARTILLERY_STOP             101              info
                - HONEYPOT_ATTACK            200              warning
                - Smb_Client_Enabled         300              warning
                - Smb_Server_Enabled         301              warning
                - WPAD_Running               302              warning
                - LLMNR_Key_Not_Present      303              warning
                - Smb_Disable_Help           310              info
                - DLL_Installed              500              info
                - Dll_Removed                501              info
                - Artillery_Installed        502              info
                - Artillery_Removed          503              info

            for ex.

                - write_windows_eventlog('Artillery', 200, warning, True, ip)

                This will log a honeypot attack message and send toast alert with values given


            Calls ReportEvent() from pywin32.

                - ReportEvent(AppName, eventID, eventCategory=int(category), eventType=event_type, data=data, sid=my_sid)


            """
        category = int(1)
        process = GetCurrentProcess()
        token = OpenProcessToken(process, TOKEN_READ)
        my_sid = GetTokenInformation(token, TokenUser)[0]
            #grab a msg if any
        if msg is not None:
            data = f"Application\0Data{msg}".encode("ascii")
        else:
            data = "Your\0awesome\0additions\0to\0Artillery".encode("ascii")   
            #working on getting info straight to main event window with string inserts
            #building new event dll as we speak.
            #used to test and make sure right types are being passed in
        # print(f"Appname expected str got: {type(AppName)}")
        # print(f"Eventid expected int got: {type(event_type)}")
        # print(f"Catagory expected int got: {type(category)}")
        # print(f"Eventtype expected int got: {type(event_type)}")
        # print(f"Data expected bytes got: {type(data)}")
        # print(f"sid expected Pysid got: {type(my_sid)}")
        ReportEvent(str(AppName), int(eventID), eventCategory=int(category), eventType=event_type, data=bytes(data), sid=my_sid)

def syslog(message, alerttype, evtid):
    """
    Handles various logging methods availible. writes to SYSLOG, Remote SYSLOG, FILE

        :param msg ex: "alert detected from 'addr'"
        :param alerttype ex: an int describing the level of the alert
        :param evtid ex: only used on windows this is the eventid used in msg dll
    """
    logtype = settings.get_config("current","SYSLOG_TYPE")
    alertindicator = ""
    if alerttype == -1:
        alertindicator = ""
    elif alerttype == 0:
        alertindicator = "[INFO]"
    elif alerttype == 1:
        alertindicator = "[WARN]"
    elif alerttype == 2:
        alertindicator = "[ERROR]"
    # if we are sending remote syslog
    if logtype == "REMOTE":
        import socket
        FACILITY = {
            'kern': 0, 'user': 1, 'mail': 2, 'daemon': 3,
            'auth': 4, 'syslog': 5, 'lpr': 6, 'news': 7,
            'uucp': 8, 'cron': 9, 'authpriv': 10, 'ftp': 11,
            'local0': 16, 'local1': 17, 'local2': 18, 'local3': 19,
            'local4': 20, 'local5': 21, 'local6': 22, 'local7': 23,
        }
        LEVEL = {
            'emerg': 0, 'alert': 1, 'crit': 2, 'err': 3,
            'warning': 4, 'notice': 5, 'info': 6, 'debug': 7
        }
        def syslog_send(
            message, level=LEVEL['notice'], facility=FACILITY['daemon'],
                        host='localhost', port=514):
            # Send syslog UDP packet to given host and port.
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data = '<%d>%s' % (level + facility * 8, message + "\n")
            sock.sendto(data.encode("ascii"), (host, port))
            sock.close()
        # send the syslog message
        remote_syslog = settings.get_config("current","SYSLOG_REMOTE_HOST")
        remote_port = int(settings.get_config("current","SYSLOG_REMOTE_PORT"))
        syslogmsg = message
        if alertindicator != "":
            syslogmsg = "Artillery%s: %s" % (alertindicator, message)
        #syslogmsg = "%s %s Artillery: %s" % (grab_time(), alertindicator, message)
        syslog_send(syslogmsg, host=remote_syslog, port=remote_port)
    # if we are sending local syslog messages
    #not currently in use although defind on windows
    # i use a custom dll for alerts
    #am  working on a solution
    elif logtype == "LOCAL":
        my_logger = logging.getLogger('Artillery')
        my_logger.setLevel(logging.DEBUG)
        if is_posix():
            handler = logging.handlers.SysLogHandler(address='/dev/log')
        if is_windows():
            #this will probably need to be changed to use our custom dll
            #i have not tested this yet
            #i have a working solution in win_func.py that is not used here
            handler = logging.handlers.NTEventLogHandler("Artillery",settings.get_config("global","EVENT_DLL"),"Application")
        my_logger.addHandler(handler)
        for line in message.splitlines():
            if alertindicator != "":

                my_logger.critical("Artillery%s: %s\n" % (alertindicator, line))
            else:
                my_logger.critical("%s\n" % line)

    # if we don't want to use local syslog and just write to file in
    # logs/alerts.log
    # this will eventually replace write_log func
    #this could be removed and replaced in log event function
    elif logtype == "FILE":
        if is_windows():
            #files are written out regardless of this setting in file
            pass
        else:
            with open(file=settings.get_config('global', "ALERT_LOG"),mode='a',encoding='utf-8') as alertlog:
                msg = f"{grab_time()} Artillery{alertindicator}: {message}\n"
                alertlog.write(msg)
    
    #check to see if there is a windows event
    #
    if evtid == None:
        pass
    else:
        #unset for now but working
        # write_windows_eventlog("Artillery",evtid, alertindicator,False,None)
        pass
#from here logging is availible everywhere
def log_event(alert: str, loglvl: int, evtid: int | None, console: bool)->None:
    """
    Logs events on artillery using configured settings. Hands off to syslog function  

        :param alert ex: f"alert detected from {addr}"
        :param loglvl ex: an int 0/1/2 describing the level of the alert info/warn/error
        :param evtid ex: only used on windows this is the eventid used in msg dll can be None
        :param console ex: print to active console True or False

        ex: log_event("oops something went wrong with "insert error here",2,100,True")

        result: (logs to configured syslog, sets level as error, windows event id, prints to console)


        loglvl 0 events [INFO] will be written to runtime.log##startup/shutdown and other operational msgs\n
        loglvl 1 events [WARN] will be written to alerts.log## alerts from modules in project ex: honeypot\n
        loglvl 2 events [ERROR] will be written to exceptions.log## alerts from exceptions ex: try/except blocks\n
        loglvls with a higher number can be redirected to custom files?

        With this i can remove FILE as an option in config as these will always write local copies of info for
        local review, alerts fall through to syslog function
        This will be threaded @ some point in the near future
    """
    #
    if console == True:
        if settings.is_config_enabled("CONSOLE_LOGGING") == True:
            alertlines = alert.split("\n")
            for alertline in alertlines:
                print(f"{grab_time()}: {alertline}",flush=True)
    #
    log = ""
    msg = ""
    if loglvl == 0:
        log = settings.get_config("global", "RUNTIME_LOG")
        msg = f"{grab_time()} Artillery[INFO]: {alert}"
    #
    if loglvl == 1:
        log = settings.get_config("global", "ALERT_LOG")
        msg = f"{grab_time()} Artillery[WARN]: {alert}"
    #
    if loglvl == 2:
        log = settings.get_config("global", "EXCEPTION_LOG")
        msg = f"{grab_time()} Artillery[ERROR]: {alert}"
    #
    with open(file=log,mode='a',encoding='utf-8') as event:
                event.write(str(msg) + "\n")
    #do email stuff here???

    #could probably do windows events in here as well
    #maybe don't pass this through?
    syslog(alert,loglvl,evtid)
    #these are windows only for now
def set_console_title(name:str) -> None:
    '''sets title of window on windows systems using pywin32.winapi'''
    if is_windows():
        SetConsoleTitle(name)
        return
    if is_posix():
        pass
    
def set_console_icon(window_title, icon_path):
        
    """
        Sets the icon for a console window.

        Args:
            window_title (str): The title of the console window.
            icon_path (str): The path to the .ico file.
    """
    if is_windows():
        
        import win32con
        try:
        # Find the window handle
            hwnd = win32gui.FindWindow(None, window_title)
            if not hwnd:
                print(f"Window with title '{window_title}' not found.")
                return
            # Load the icon
            # LR_LOADFROMFILE loads from a file, IMAGE_ICON specifies an icon
            hicon = win32gui.LoadImage(
                0, icon_path, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE
            )
            if not hicon:
                print(f"Failed to load icon from '{icon_path}'.")
                return

            # Set the large icon
            win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)
            # Set the small icon
            win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)

            #print(f"Icon set for window '{window_title}'.")

        except Exception as e:
            print(f"An error occurred: {e}")
    if is_posix():
        pass
        #import platform specific stuff here?
        #so i can put all windows functions in here
        #some merging of functions is needed
# grab the current time
def grab_time() -> str:
    '''grabs current time and returns it in %Y-%m-%d %H:%M:%S format'''
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def gethostname() -> str:
    '''grabs hostname and returns it'''
    return socket.gethostname()

def get_host_ip() ->str:
    '''
    Grabs default internet connected ip and returns it.
    '''
    return socket.gethostbyname(gethostname())

def convert_to_classc(param) ->str:
    '''converts an ipaddr to cover whole block. ex: if the attacker addr is 192.168.2.1
    the resulting entry put in banlist is 192.168.2.0/24. Therefor blocking the entire range'''
    ipparts = param.split('.')
    classc = ""
    if len(ipparts) == 4:
        classc = ipparts[0] + "." + ipparts[1] + "." + ipparts[2] + ".0/24"
    return classc

###this fuction wiil change in future
#it will be replaced with acually calling
#removeban.py directly which handles this now
def ban(ip):
    '''checks to see if a certain ip is on the banlist already if not adds it.
    On linux will add entry to iptables. On windows adds to routing table.'''
    ip = ip.rstrip()
    ban_check = settings.get_config("current","HONEYPOT_BAN").lower()
    ban_classc = settings.get_config("current","HONEYPOT_BAN_CLASSC").lower()
    test_ip = ip
    if "/" in test_ip:
        test_ip = test_ip.split("/")[0]
    #this check can be removed in future i do this on server connect
    # might produce dupe logs
    if is_whitelisted_ip(test_ip):
        log_event(f"Not banning IP {test_ip}, whitelisted",0,None,False)
        #write_log("Not banning IP %s, whitelisted" % test_ip)
        return
    if ban_check == "on":
        #none below upto platform check is needed as 
        #ip is verified before it gets to this point
        if not ip.startswith("#"):
            if not ip.startswith("0."):
                #this can be removed as we only accept connection if valid ip
                if is_valid_ipv4(ip.strip()):
                    # if we are running nix variant then trigger ban through
                    # iptables
                    if is_posix():
                        #this can be removed as well only accept connection if is not already banned
                        if not is_already_banned(ip):
                            if ban_classc == "on":

                                ip = convert_to_classc(ip)
                                subprocess.Popen(
                                    "iptables -I ARTILLERY 1 -s %s -j DROP" % ip, shell=True).wait()
                            iptables_logprefix = settings.get_config("current","HONEYPOT_BAN_LOG_PREFIX")
                            if iptables_logprefix != "":
                                subprocess.Popen("iptables -I ARTILLERY 1 -s %s -j LOG --log-prefix \"%s\"" % (ip, iptables_logprefix), shell=True).wait()

                    # if running windows then route attacker to some bs address.
                    if is_windows():
                        #from ..utils.event_log import write_windows_eventlog, warning
                        #lets try and write an event log
                        #log_event(f"Banning {ip} for connecting to a honeypot port",1,200)
                        write_windows_eventlog("Artillery", 200, win32evtlog.EVENTLOG_WARNING_TYPE, False, None,msg=None)
                        #now lets block em or mess with em route somewhere else?
                        routecmd = "route ADD %s MASK 255.255.255.255 10.255.255.255"
                        if ban_check == 'on':
                            if ban_classc == "on":
                                ip = convert_to_classc(ip)
                                ipparts = ip.split(".")
                                routecmd = "route ADD %s.%s.%s.0 MASK 255.255.255.0 10.255.255.255" % (ipparts[0], ipparts[1], ipparts[2])
                                subprocess.Popen("%s" % (routecmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                            else:
                                # or use the old way and just ban the individual ip
                                subprocess.Popen(routecmd % (ip), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    #add check with does_line_exist here
                    # add new IP to banlist
                    fileopen = open(settings.get_config('global',"BANLIST"), "r")
                    data = fileopen.read()
                    if ip not in data:
                        filewrite = open(settings.get_config('global',"BANLIST"), "a")
                        filewrite.write(ip + "\n")
                        filewrite.close()

                    if settings.is_config_enabled("LOCAL_BANLIST") == True:
                        fileopen = open(settings.get_config('global', "LOCAL_BANLIST"), "r")
                        data = fileopen.read()
                        if ip not in data:
                            filewrite = open(settings.get_config('global', "LOCAL_BANLIST"), "a")
                            filewrite.write(ip + "\n")
                            filewrite.close()


def update():
    '''updates artillery on linux platforms'''
    def get_updates():
        if settings.is_config_enabled("AUTO_UPDATE") == True:
            if is_posix():
                log_event("Running auto update (git pull)",0,None,True)
                if os.path.isdir(settings.get_config('global', "APPPATH") + "/.svn"):
                    print(
                        "[!] Old installation detected that uses subversion. Fixing and moving to github.",flush=True)
                    try:
                        if len(settings.get_config('global', "APPPATH")) > 1:
                            shutil.rmtree(settings.get_config('global', "APPPATH"))
                        subprocess.Popen(
                            "git clone https://github.com/binarydefense/artillery", shell=True).wait()
                    except:
                        print(
                            "[!] Something failed. Please type 'git clone https://github.com/binarydefense/artillery %s' to fix!" % settings.get_config('global', "APPPATH"),flush=True)

                #subprocess.Popen("cd %s;git pull" % settings.get_config('global', "APPPATH"),
                #                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                update_cmd = execOScmd("cd %s; git pull" % settings.get_config('global', "APPPATH"))
                errorfound = False
                abortfound = False
                errormsg = ""
                for l in update_cmd:
                    errormsg += "%s\n" % l
                    if "error:" in l:
                        errorfound = True
                    if "Aborting" in l:
                        abortfound = True
                if errorfound and abortfound:
                    msg = f"Error updating artillery, git pull was aborted. Error:\n{errormsg}"
                    log_event(msg,2,None,True)
                    msg = "I will make a copy of the config file, run git stash, and restore config file"
                    log_event(msg,2,None,True)
                    saveconfig = "cp '%s' '%s.old'" % (settings.get_config('global',"LOGFILE"), settings.get_config('global',"LOGFILE"))
                    execOScmd(saveconfig)
                    gitstash = "git stash"
                    execOScmd(gitstash)
                    gitpull = "git pull"
                    newpull = execOScmd(gitpull)
                    restoreconfig = "cp '%s.old' '%s'" % (settings.get_config('global',"LOGFILE"), settings.get_config('global',"LOGFILE"))
                    execOScmd(restoreconfig)
                    pullmsg = ""
                    for l in newpull:
                        pullmsg += "%s\n" % l
                    msg = "Tried to fix git pull issue. Git pull now says:"
                    log_event(msg,2,None,True)
                    #
                    log_event(pullmsg,2,None,True)
                else:
                    msg = f"Output 'git pull':\n{errormsg}"
                    log_event(msg,0,None,False)
            if is_windows():
                #call update.exe/py
                #if not and put the code here would require adding wx to project
                #don't want to do that
                pass
    threading.Thread(group=None,target=get_updates,args=(),daemon=True).start()
#
def addressInNetwork(ip, net):
    """
    returns true if the ip is in a given network
    """
    try:
        ipaddr = int(''.join(['%02x' % int(x) for x in ip.split('.')]), 16)
        netstr, bits = net.split('/')
        netaddr = int(''.join(['%02x' % int(x) for x in netstr.split('.')]), 16)
        mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
        return (ipaddr & mask) == (netaddr & mask)
    except:
        return False


def is_whitelisted_ip(ip)->bool:
    '''checks to see if a certain ip is on the whitelist and returns True or false'''
    # grab ips
    ipaddr = str(ip)
    whitelist = settings.get_config("current","WHITELIST_IP")
    whitelist = whitelist.split(',')
    for site in whitelist:
        if site.find("/") < 0:
            if site.find(ipaddr) >= 0:
                return True
            else:
                continue
        if addressInNetwork(ipaddr, site):
            return True
    return False

def is_valid_ipv6(ip):
    """validate ipv6 address.
    """
    pattern = re.compile(r"""
        ^
        \s*                         # Leading whitespace
        (?!.*::.*::)                # Only a single whildcard allowed
        (?:(?!:)|:(?=:))            # Colon iff it would be part of a wildcard
        (?:                         # Repeat 6 times:
            [0-9a-f]{0,4}           #   A group of at most four hexadecimal digits
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
        ){6}                        #
        (?:                         # Either
            [0-9a-f]{0,4}           #   Another group
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
            [0-9a-f]{0,4}           #   Last group
            (?: (?<=::)             #   Colon iff preceeded by exacly one colon
             |  (?<!:)              #
             |  (?<=:) (?<!::) :    #
             )                      # OR
         |                          #   A v4 address with NO leading zeros 
            (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            (?: \.
                (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            ){3}
        )
        \s*                         # Trailing whitespace
        $
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL)
    return pattern.match(ip) is not None
# these 3 functions below does_line_exist,banlist_add_line,banlist_remove_line
# are meant to replace is_already_banned()
def does_line_exist(line):
    '''
    Checks for the existence of a line in banlist.
    returns True or False
    '''
    present = False
    banlist = settings.get_config('global', "BANLIST")
    query = line.strip()
    with open(file=banlist,mode="r",encoding="utf-8") as blist:
        for l in blist:
            result = l.strip()
            if result == query:
                present = True
                break
    #
    return present

def banlist_add_line(line):
    '''
    adds a line to the banlist uses does_line_exist 
    to check if line is present
    '''
    exists = does_line_exist(line)
    
    if exists == True:
        #log the event
        log_event(f"[*] {line} already exists in banlist, not adding again", 0, None, True)
        return
    else:
        #add the line
        log_event(f"[*] Adding {line} to banlist.txt...",0,None,True)
        with open(file=settings.get_config('global', "BANLIST"),mode= "a",encoding='utf-8') as blist:
            blist.write(line + "\n")
        #if local banlist is enabled then add to that as well
        if settings.is_config_enabled("LOCAL_BANLIST") == True:
            with open(file=settings.get_config('global', "LOCAL_BANLIST"),mode="a",encoding='utf-8') as blist:
                blist.write(line + "\n")
        #log the addition
        log_event(f"[*] Added {line} to banlist.txt", 0, None, True)

def banlist_remove_line(line):
    '''
    removes a line from the banlist uses 
    does_line_exist to check if line is present
    '''
    exists = does_line_exist(line)
    
    if exists == False:
        #log the event
        #could just pass here dont care if it doesnt exist
        log_event(f"[*] {line} does not exist in banlist, not removing", 0, None, True)
        return
    else:
        #remove the line
        log_event(f"[*] Removing {line} from banlist", 0, None, True)
        with open(file=settings.get_config('global', "BANLIST"),mode= "r",encoding='utf-8') as blist:
            lines = blist.readlines()
        with open(file=settings.get_config('global', "BANLIST"), mode="w",encoding='utf-8') as blist:
            for l in lines:
                if l.strip() != line.strip():
                    blist.write(l)
        #if local banlist is enabled then remove from that as well
        if settings.is_config_enabled("LOCAL_BANLIST") == True:
            with open(file=settings.get_config('global', "LOCAL_BANLIST"), mode="r",encoding='utf-8') as blist:
                lines = blist.readlines()
            with open(file=settings.get_config('global', "LOCAL_BANLIST"),mode= "w",encoding='utf-8') as blist:
                for l in lines:
                    if l.strip() != line.strip():
                        blist.write(l)
        #log the removal
        log_event(f"[*] Removed {line} from banlist", 0, None, True)


def is_valid_ipv4(ip):
    '''validate ipv4 address.'''
    # if IP is cidr, strip net
    if "/" in ip:
        ipparts = ip.split("/")
        ip = ipparts[0]
    if not ip.startswith("#"):
        pattern = re.compile(r"""
    ^
    (?:
      # Dotted variants:
      (?:
        # Decimal 1-255 (no leading 0's)
        [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
      |
        0x0*[0-9a-f]{1,2}  # Hexadecimal 0x0 - 0xFF (possible leading 0's)
      |
        0+[1-3]?[0-7]{0,2} # Octal 0 - 0377 (possible leading 0's)
      )
      (?:                  # Repeat 0-3 times, separated by a dot
        \.
        (?:
          [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
        |
          0x0*[0-9a-f]{1,2}
        |
          0+[1-3]?[0-7]{0,2}
        )
      ){0,3}
    |
      0x0*[0-9a-f]{1,8}    # Hexadecimal notation, 0x0 - 0xffffffff
    |
      0+[0-3]?[0-7]{0,10}  # Octal notation, 0 - 037777777777
    |
      # Decimal notation, 1-4294967295:
      429496729[0-5]|42949672[0-8]\d|4294967[01]\d\d|429496[0-6]\d{3}|
      42949[0-5]\d{4}|4294[0-8]\d{5}|429[0-3]\d{6}|42[0-8]\d{7}|
      4[01]\d{8}|[1-3]\d{0,9}|[4-9]\d{0,8}
    )
    $
    """, re.VERBOSE | re.IGNORECASE)
        return pattern.match(ip) is not None

#only used on posix
def execOScmd(cmd, logmsg=""):
    '''execute OS command and to wait until it's finished'''
    if logmsg != "":
        log_event(f"execOSCmd: {logmsg}",0,None,False)
    p = subprocess.Popen('%s' % cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    outputobj = iter(p.stdout.readline, b'')
    outputlines = []
    for l in outputobj:
        thisline = ""
        try:
            thisline = l.decode()
        except:
            try:
                thisline = l.decode('utf8')
            except:
                thisline = "<unable to decode>"
        outputlines.append(thisline.replace('\\n', '').replace("'", ""))
    return outputlines

#unused code never called?
def execOScmdAsync(cmdarray):
    '''execute OS commands Asynchronously this one takes an array
    first element is application, arguments are in additional array elements'''
    p = subprocess.Popen(cmdarray)
    return
#only used on posix
def create_empty_file(filepath):
    '''creates an empty file at the given file path'''
    filewrite = open(filepath, "w")
    filewrite.write("")
    filewrite.close()
#not needed anymore as banlist is generated @ runtime if not present
def write_banlist_banner(filepath):
    '''writes out banlist.txt header to file'''
    filewrite = open(filepath, "w")
    banner = """#
#
#
# Binary Defense Systems Artillery Threat Intelligence Feed and Banlist Feed
# https://www.binarydefense.com
#
# Note that this is for public use only.
# The ATIF feed may not be used for commercial resale or in products that are charging fees for such services.
# Use of these feeds for commerical (having others pay for a service) use is strictly prohibited.
#
#
#
"""
    filewrite.write(banner)
    filewrite.close()
#only used on posix
def create_firewall_rules():
    '''reads in ip from banlist and other sources and adds them 
    to to a fresh iptables chain or windows firewall group
    for artillery at run time'''
    #
    #assume were not banning
    banning_enabled = False
    if is_posix():
        ban_check = settings.is_config_enabled("HONEYPOT_BAN")
        if ban_check == True:
            log_event("[*] Creating iptables entries, hold on.",0,None,True)
            banning_enabled = True
            # remove previous entry if it already exists
            execOScmd("iptables -D INPUT -j ARTILLERY", "Deleting ARTILLERY IPTables Chain")
            # create new chain
            log_event("Flushing iptables chain, creating a new one",0,None,False)
            execOScmd("iptables -N ARTILLERY -w 3")
            execOScmd("iptables -F ARTILLERY -w 3")
            execOScmd("iptables -I INPUT -j ARTILLERY -w 3")
        #setup our list to use
        bannedips = []
        banfile = open(file=settings.get_config('global',"BANLIST"), mode="r",encoding='utf-8').readlines()
        banlength = len(banfile)
        banlocation = settings.get_config('global',"BANLIST")
        msg = f"Read {str(banlength)} lines in {banlocation}"
        log_event(msg,0,None,False)
        #add all the ips in banlist
        for ip in banfile:
            if not ip in bannedips:
                bannedips.append(ip)
        # add loclalbanlist if enabled
        if settings.is_config_enabled("LOCAL_BANLIST") == True:
            localbanfile = open(file=settings.get_config('global', "LOCAL_BANLIST"), mode="r",encoding='utf-8').readlines()
            lbanlength = len(localbanfile)
            lbanlocation = settings.get_config('global', "LOCAL_BANLIST")
            log_event(f"Read {str(lbanlength)} lines in {lbanlocation}",0,None,False)
            #write_log("Read %d lines in '%s'" % (len(localbanfile), settings.get_config('global', "LOCAL_BANLIST")))
            for ip in localbanfile:
                if not ip in bannedips:
                    bannedips.append(ip)
        # if we are banning
        banlist = []
        if banning_enabled is True:
            # iterate through lines from ban file(s) and ban them if not already banned
            for ip in bannedips:
                #this whole piece can be replaced by is_valid_ip() this detects ipv4\\ipv6
                #it does away with the need to do this
                if not ip.startswith("#") and not ip.replace(" ", "") == "":
                    ip = ip.strip()
                    if ip != "" and not ":" in ip:
                        test_ip = ip
                    if "/" in test_ip:
                        test_ip = test_ip.split("/")[0]
                    #down to here
                    #
                    if not is_whitelisted_ip(test_ip):
                        if not ip.startswith("0."):
                            #this can be removed as well the check can be done above
                            # when ipv6 support is enabled:)
                            if is_valid_ipv4(ip.strip()):
                                if settings.get_config("current","HONEYPOT_BAN_CLASSC") == "ON":
                                    if not ip.endswith("/24"):
                                        ip = convert_to_classc(ip)
                                        banlist.append(ip)
                                else:
                                    banlist.append(ip)
                    else:
                        log_event(f"Not banning IP {ip}, whitelisted",0,None,False)
        #
        if len(banlist) > 0:
            # convert banlist into unique list
            log_event("Filtering duplicate entries in banlist",0,None,False)
            set_banlist = set(banlist)
            unique_banlist = (list(set_banlist))
            entries_at_once = 750
            total_nr = len(unique_banlist)
            msg = f"Mass loading {str(total_nr)} unique entries from banlist(s)"
            log_event(msg,0,None,True)
            nr_of_lists = int(len(unique_banlist) / entries_at_once) + 1
            iplists = get_sublists(unique_banlist, nr_of_lists)
            listindex = 1
            logindex = 1
            logthreshold = 25
            if len(iplists) > 1000:
                logthreshold = 100
            total_added = 0
            for iplist in iplists:
                ips_to_block = ','.join(iplist)
                massloadcmd = "iptables -I ARTILLERY -s %s -j DROP -w 3" % ips_to_block
                subprocess.Popen(massloadcmd, shell=True).wait()
                iptables_logprefix = settings.get_config("current","HONEYPOT_BAN_LOG_PREFIX")
                if iptables_logprefix != "":
                    massloadcmd = "iptables -I ARTILLERY -s %s -j LOG --log-prefix \"%s\" -w 3" % (ips_to_block, iptables_logprefix)
                    subprocess.Popen(massloadcmd, shell=True).wait()
                total_added += len(iplist)
                #log_event(f"{str(listindex)}/{str(len(iplists))} - Added {str(total_added)}/{str(total_nr)} IP entries to iptables chain.")
                write_log("%d/%d - Added %d/%d IP entries to iptables chain." % (listindex, len(iplists), total_added, total_nr))
                if logindex >= logthreshold:
                    write_console("    %d/%d : Update: Added %d/%d entries to iptables chain" % (listindex, len(iplists), total_added, total_nr))
                    logindex = 0
                listindex += 1
                logindex += 1   
            write_console("    %d/%d : Done: Added %d/%d entries to iptables chain, thank you for waiting." % (listindex-1, len(iplists), total_added, total_nr))
            log_event("[*] iptables entries created.",0,None,True)
    if is_windows():
        #figure 3 to 5 groups 800 limit per group
        #keep track and rotate out?
        #check @ runtime
        #will have to build logic
        #to work with removeban.py
        #which can do groups just not exposed
        pass
def get_sublists(original_list, number_of_sub_list_wanted):
    '''gets and returns x num of list based on original input'''
    sublists = list()
    for sub_list_count in range(number_of_sub_list_wanted):
        sublists.append(original_list[sub_list_count::number_of_sub_list_wanted])
    return sublists
#this will be re-worked in future
def is_already_banned(ip):
    '''checks to see if an ip is already banned and returns True or False
    checks routing table and banlist.txt, returns true or false for each

        :param ip  the ip to check

    '''
    #assume its not in either place
    route = False
    banlist = False
    ban_check = settings.get_config("current","HONEYPOT_BAN")
    ban_classc = settings.get_config("current","HONEYPOT_BAN_CLASSC")
    banfile = settings.get_config('global','BANLIST')
    #only check if banning is enabled
    if ban_check == "ON":
        #lets check the routing table first
        if is_posix():
            proc = subprocess.Popen("iptables -L ARTILLERY -n --line-numbers",
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if is_windows():
            proc = subprocess.Popen("route print",
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        iptablesbanlist = proc.stdout.readlines()
        #convert the ip to classc if needed
        if ban_classc == "ON":
            ip = convert_to_classc(ip)
        #check if ip is in the routing table
        if ip in iptablesbanlist:
            route = True
        #then check banlist it might be in the banlist but not in routing table?
        #maybe we have not seen it before. if is is do we just add from here or notify?
        #in the future this will be replaced with does_line_exist
        with open(file=banfile,mode='r',encoding='utf-8') as bancheck:
            for line in bancheck:
                line =line.strip()
                if line == ip:
                    #its in the banlist
                    banlist = True
        # will become a tuple response in future
        #return route, banlist
        return route
    else:
        #log_event("Honeypot banning is not enabled",0,None)
        return False
#in the raw version there is no tray listener this will be addressed in a future update
#i will not make a full-tray app like with the binary version but, a small just listener
# tray is possible 
def systray_alert(id: int, alert: str):
    """
    sends an alert to the systray app(only valid on windows)

        :param id ex:  int value respresenting msgid on windows
        :param alert ex: Brute force attempt from "addr"
        
    
    """
    if is_windows():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # i could use bind_address here instead from config? but what if its blank
            #so i just grab the default ip on gateway connected net
            #create flag to handle in config systray_listener and systray_port
            #host = "127.0.0.1"
            host = get_host_ip()
            port = 10080
            sock.connect((host, port))
            log_event(f"[+] Sending systray alert to {str(host)}:{str(port)}",0,None,False)
            sock.send(alert.encode('utf-8'))  
            response = sock.recv(4096)
            log_event(f"[+] Received {repr(response.decode('utf-8'))}",0,None,False)
        sock.close()
        return
    if is_posix():
        log_event("Systray alerts are not supported on this platform",0,None,False)
        return

#this function combines ip validation to one call
# just use this and you get support for both
def is_valid_ip(ip) -> bool:
    '''returns True if is a valid ip address.
    Works on Ipv4/Ipv6'''
    valid = False
    if is_valid_ipv4(ip):
        valid = True
    else:
        if is_valid_ipv6(ip):
            valid = True
    return valid


def bin2ip(b):
    '''convert a binary string into an IP address'''
    ip = ""
    for i in range(0, len(b), 8):
        ip += str(int(b[i:i + 8], 2)) + "."
    return ip[:-1]


def ip2bin(ip):
    '''convert an IP address from its dotted-quad format to its 32 binary digit representation'''
    b = ""
    inQuads = ip.split(".")
    outQuads = 4
    for q in inQuads:
        if q != "":
            b += dec2bin(int(q), 8)
            outQuads -= 1
    while outQuads > 0:
        b += "00000000"
        outQuads -= 1
    return b


def dec2bin(n, d=None):
    '''convert a decimal number to binary representation
    if d is specified, left-pad the binary number with 0s to that length'''
    s = ""
    while n > 0:
        if n & 1:
            s = "1" + s
        else:
            s = "0" + s
        n >>= 1

    if d is not None:
        while len(s) < d:
            s = "0" + s
    if s == "":
        s = "0"
    return s

#this function is never called
def printCIDR(attacker_ip):
    '''print a list of IP addresses based on the CIDR block specified'''
    trigger = 0
    whitelist = settings.get_config("current","WHITELIST_IP")
    whitelist = whitelist.split(",")
    for c in whitelist:
        match = re.search("/", c)
        if match:
            parts = c.split("/")
            baseIP = ip2bin(parts[0])
            subnet = int(parts[1])
            # Python string-slicing weirdness:
            # if a subnet of 32 was specified simply print the single IP
            if subnet == 32:
                ipaddr = bin2ip(baseIP)
            # for any other size subnet, print a list of IP addresses by concatenating
            # the prefix with each of the suffixes in the subnet
            else:
                ipPrefix = baseIP[:-(32 - subnet)]
                for i in range(2**(32 - subnet)):
                    ipaddr = bin2ip(ipPrefix + dec2bin(i, (32 - subnet)))
                    ip_check = is_valid_ip(ipaddr)
                    # if the ip isnt messed up then do this
                    if ip_check != False:
                        # compare c (whitelisted IP) to subnet IP address
                        # whitelist
                        if c == ipaddr:
                            # if we equal each other then trigger that we are
                            # whitelisted
                            trigger = 1

    # return the trigger - 1 = whitelisted 0 = not found in whitelist
    return trigger

#only used in posix will add support for others if interested
def threat_server():
    '''
    copies files for use with hosting a threat server
    '''
    def update_server():
        if settings.is_config_enabled("THREAT_SERVER") == True:
            if is_posix():
                public_http = settings.get_config("current","THREAT_LOCATION")
                if os.path.isdir(public_http):
                    banfiles = settings.get_config("current","THREAT_FILE")
                    if banfiles == "":
                        banfiles = settings.get_config('global',"BANLIST")
                    banfileparts = banfiles.split(",")
                    while 1:
                        for banfile in banfileparts:
                            thisfile = settings.get_config('global', "APPPATH") + "/" + banfile
                            subprocess.Popen("cp '%s' '%s'" % (thisfile, public_http), shell=True).wait()
                            #write_log("ThreatServer: Copy '%s' to '%s'" % (thisfile, public_http))
                        time.sleep(300)
            if is_windows():
                pass
    threading.Thread(group=None,target=update_server,args=(),daemon=True).start()
#this is only in use on certain posix func and will be removed in future
# this will be handled in log_event func 
def write_console(alert) -> None:
    '''writes alerts to console window'''
    if settings.is_config_enabled("CONSOLE_LOGGING") == True:
        alertlines = alert.split("\n")
        for alertline in alertlines:
            print("%s: %s" % (grab_time(), alertline),flush=True)
#this will be removed in future
#only used in create_iptables_subset()
def write_log(alert, alerttype=0):

    """writes a log depending on platform. On linux it uses syslog func. On windows writes to alerts.log
     """
   
    if is_posix():
        syslog(alert, alerttype,None)
    #
    if is_windows():
        pass

def kill_artillery() -> None:
    ''' kill running instances of artillery'''
    try:
        proc = subprocess.Popen(
            "ps -A x | grep artiller[y]", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        pid, err = proc.communicate()
        pid = [int(x.strip()) for line in pid.split()
               for x in line.split() if int(x.isdigit())]
        for i in pid:
            log_event("Killing the old Artillery process...",0,None,True)
            os.kill(i, signal.SIGKILL)

    except Exception as e:
        print(e,flush=True)


def cleanup_iptables_artillery() -> None:
    '''
    cleans up iptables entries related to artillery
    '''
    ban_check = settings.get_config("current","HONEYPOT_BAN")
    if ban_check == "ON":
        subprocess.Popen("iptables -D INPUT -j ARTILLERY",
                         stdout=subprocess.PIP, stderr=subprocess.PIPE, shell=True)
        subprocess.Popen("iptables -X ARTILLERY",
                         stdout=subprocess.PIP, stderr=subprocess.PIPE, shell=True)
        return 0

#this will be re-worked
def refresh_banlist() -> None:
    '''overwrite artillery banlist after certain time interval
        with the value retrived from config file for artillery_refresh '''
    def refresh():
        if settings.is_config_enabled("RECYCLE_IPS") == True:
            while 1:
                interval = settings.get_config("current","ARTILLERY_REFRESH")
                try:
                    interval = int(interval)
                except:
                    # if the interval was not an integer, then just pass and don't do
                    # it again
                    break
                # sleep until interval is up
                time.sleep(interval)
                log_event("clearing banlist.txt",0,None,True)
                # overwrite the log with nothing
                create_empty_file(settings.get_config('global',"BANLIST"))
                write_banlist_banner(settings.get_config('global',"BANLIST"))
                #update after refresh? as the file is now empty
    threading.Thread(group=None,target=refresh,args=(),daemon=True).start()
#
def format_ips(urls):

    '''
    Recieves and formats ip lists from pull_source_feeds() func.
    Only looks for "200 OK" and "404 Notfound". Only adds if 200 OK
    recieved, alerts on all others. And then writes it to banfile
    For now i only validate ipv4 addresess. ipv6 wil be added in a future update.
  
    '''
    
    ip4_lst = []
    ip6_lst = []
    count4 = 0
    count6 = 0
    #create sesion handler object
    session_handler = Session()
    #add custom headers
    headers ={'user-agent': 'Artillery Banlist Updater V1'}
    for url in urls:
        log_event(f"[*] Grabbing feed from {url}",0,None,True)
        if url.startswith("http"):
            req = Request(method='GET',url=url, headers=headers)
            prepped = req.prepare()
            response = session_handler.send(prepped)
            status = response.status_code
            data = response.text 
            if status == 200:
                #make any backups here
                #write_log("Backing up existing banlist")
                #subprocess.call(['cmd', '/C', 'copy', ban_file, backup_dest])
                #time.sleep(1)
                #convert data to a list
                line = data.split("\n")
                #check for ip4/ip6 address ignore anything else
                for item in line:
                    if is_valid_ipv4(item) == True:
                      count4 +=1
                      ip4_lst.append(item)
                    elif is_valid_ipv6(item) == True:
                      count6 +=1
                      ip6_lst.append(item)
                    else:
                        pass
            #
            elif status == 404:
                log_event(f"[*] HTTPError: Error 404, URL {url} not found.",1,None,True)
            else:
                #this is a catchall for things i don't know about
                msg = format(response.status_code)
                msg_to_string =  f"[!] Received URL Error trying to download feed from {url} Reason: {msg}"
                log_event(msg_to_string,1,None,True)
    
    #turn our lists into a string with just ips
    lst4 = '\n'.join(ip4_lst)
    lst6 = '\n'.join(ip6_lst)
    #send off to sort banlist
    sort_banlist(lst4, lst6)

def pull_source_feeds():
    '''update threat intelligence feed with other sources.'''
    def get_feeds():
        while 1:
            url_list = []
            counter = 0
            # if we are using source feeds
            if settings.is_config_enabled('SOURCE_FEEDS') == True:
                log_event("[*] Pulling from source feeds please wait.......",0,None,True)
                urls = ["http://rules.emergingthreats.net/blockrules/compromised-ips.txt", "http://lists.blocklist.de/lists/apache.txt", "http://lists.blocklist.de/lists/ssh.txt"]
                for url in urls:
                    url_list.append(url)
                counter = 1
            # if we are using threat intelligence feeds
            if settings.is_config_enabled('THREAT_INTELLIGENCE_FEED') == True:
                log_event("[*] Pulling from additional source feeds please wait.......",0,None,True)
                threat_feed = settings.get_config('current','THREAT_FEED')
                if threat_feed != "":
                    threat_feed = threat_feed.split(",")
                    for threats in threat_feed:
                        url_list.append(threats)
                counter = 1
            # if we used source feeds or ATIF
            if counter == 1:
                log_event("[*] Done pulling from source feeds.",0,None,False)
                format_ips(url_list)
                time.sleep(86400)  # sleep for 24 hours
    threading.Thread(group=None,target=get_feeds,args=(),daemon=True).start()
#
def sort_banlist(ip4,ip6) -> None:
    '''Create banlist from source_feeds list.This will wipe 
      the banlist and refresh on every run.after creating a backup
      of existing file first if exists.
    '''
    banner = """#
#
#
# Binary Defense Systems Artillery Threat Intelligence Feed and Banlist Feed
# https://www.binarydefense.com
#
# Note that this is for public use only.
# The ATIF feed may not be used for commercial resale or in products that are charging fees for such services.
# Use of these feeds for commerical (having others pay for a service) use is strictly prohibited.
#
#
#
  """
    uniquenewentries = 0
    ban_file = settings.get_config("global", "BANLIST")
    #backup_src = globalsettings.get("APP_PATH")
    #backup_dest = backup_src+"\\logs"
    cips = ip4.split("\n")
    #open the banlist
    with open(ban_file,"w",encoding="utf-8")as banlist:
        #make any backups here
        #write_log("Backing up existing banlist")
        #subprocess.call(['cmd', '/C', 'copy', ban_file, backup_dest])
        #time.sleep(1)
        #wipe the current contents and write new banner
        banlist.flush()
        banlist.write(banner + "\n")
        #and jump to last line
        banlist.seek(0, 2)
        for item in cips:
            #check to see if is valid ip or just junk
            line = is_valid_ipv4(item) 
            if line == True:
                if settings.is_config_enabled("HONEYPOT_BAN_CLASSC") == True:
                    ip = convert_to_classc(item)
                    uniquenewentries += 1
                    banlist.write(ip +"\n")
                else:
                    uniquenewentries += 1
                    banlist.write(item +"\n")
    log_event("[*] Done creating new banlist from source feeds.",0,None,True)
    #get current line count of banfile
    ban_file_len = open(ban_file,"r",encoding="utf-8").readlines()
    #subtract lines fron banlist header
    final_count = len(ban_file_len) - 13
    log_event(f"[*] Added {str(final_count)} entries to banlist",0,None,True)

def get_pid() -> None:
    """
    grabs current processid using GetCurrentProcessId() from pywin32.winapi
    on windows. os.getpid() on posix and saves to log file.
    """
    if is_windows():
        p_id = GetCurrentProcessId()
        pid_file = settings.get_config('global',"PIDFILE")
        log_event(f"[*] Current ProcessId: {str(p_id)}",0,None,False)
        if not os.path.isfile(path=pid_file):
            with open(file=pid_file,mode="x",encoding="utf-8") as pid:
                pid.write(str(p_id))
        else:
            with open(file=pid_file,mode="w",encoding="utf-8") as pid:
                pid.write(str(p_id))
    if is_posix():
        #i only report the pid on nix for now
        p_id = os.getpid()
        log_event(f"[*] Current ProcessId: {str(p_id)}",0,None,False)
#Artillery version info
####################################################################################
def current_version() -> None:
    '''returns current release of artillery'''
    ver = ['3.0.0']
    info = f"[*] Artillery Ver: {str(ver[0])}"
    log_event(info,0,None,True)
#
def freeze_check() -> str:
    '''check to see if we are runnning in a frozen executable or from the .py file. ex. pyinstaller'''
    frozen = 'not running'
    # if we are running in a bundle
    if getattr(sys, 'frozen', False):
        frozen = 'running'
        bundle_dir = sys._MEIPASS
        temp = 'cold'
    else:
        # if we are running in a normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
        temp = 'hot'
    if temp == 'cold':
        exe_path = os.path.dirname(sys.executable)
        mei_path = bundle_dir
        log_event(f"[*] Freeze Check: we are {frozen} frozen.",0,None,False)
        py_ver = platform.python_version()
        log_event(f"[*] Python ver: {py_ver}",0,None,False)
        return str(exe_path)
    else:
        py_ver = platform.python_version()
        log_event(f"[*] Freeze Check: we are {frozen} frozen.",0,None,False)
        log_event(f"[*] Python ver: {py_ver}",0,None,False)
        return(bundle_dir)
def get_os()-> None:
    '''This function uses pre-compiled lists to try and determine host os by comparing values to host entries
    if a match is found reports version.'''
    if is_posix:
        pass
    if is_windows:
        OsName = "Unknown version"
        OsBuild = "Unknown build"
        #reg key list
        reg = [r'SOFTWARE\Microsoft\Windows NT\CurrentVersion']
        #known os list
        kvl = ['Windows 7 Pro', 'Windows Server 2008 R2 Standard', 'Windows 8.1 Pro', 'Windows 10 Pro', 'Windows Small Business Server 2011 Essentials',
             'Windows Server 2012 R2 Essentials', 'Hyper-V Server 2012 R2','Windows Server 2016 Standard', 'Windows Server 2016 Essentials']
        #known builds
        b1 = ['7601', '9600', '1709', '17134', '18362', '19041', '19042','19043','14393','19044','19045']
        #final client cfg list
        ccfg = []
        try:
            oskey = reg[0]
            oskeyctr = 0
            oskeyval = OpenKey(HKEY_LOCAL_MACHINE, oskey)
            while True:
                ossubkey = EnumValue(oskeyval, oskeyctr)
                #dumps all results to txt file to parse for needed strings below
                osresults = open("version_check.txt", "a")
                osresults.write(str(ossubkey)+'\n')
                oskeyctr += 1
        #catch the error when it hits end of the key
        except WindowsError:
            osresults.close()
            #open up file and read what we got
            data = open('version_check.txt', 'r')
            # keywords from registry key in file
            keywords = ['ProductName', 'CurrentVersion', 'CurrentBuildNumber']
            exp = re.compile("|".join(keywords), re.I)
            for line in data:
                #write out final info wanted to list
                if re.findall(exp, line):
                    line = line.strip()
                    ccfg.append(line)
            data.close()
            #delete the version info file. we dont need it any more
            subprocess.call(['cmd', '/C', 'del', 'version_check.txt'])
            # now compare 3 lists from get_config function and client_config.txt to use for id
            #sort clientconfig list to have items in same spot accross platforms
            ccfg.sort(reverse=True)
            osresults = ccfg[0]
            buildresults = ccfg[2]
            for name in kvl:
                if name in osresults:
                    OsName = name
            for build in b1:
                if build in buildresults:
                    OsBuild = build
            #when were done comparing print what was found
            log_event(f"[*] Detected OS: {OsName} Build: {OsBuild}",0,None,True)
        return
def set_pipe_access():
    """
    Creates a pywintypes.SECURITY_ATTRIBUTES object with 
    a custom "Discretionary Access Control List(DACL)".
    The custom DACL grants generic r/w/e to the current user
    and full access for administrators. Used to control access to artillery srvc PIPE.
    """
    if is_windows():

        # Look up the SID for the current user
        user_name = GetUserName()
        user_sid, domain, type = win32security.LookupAccountName("", user_name)
        #get everyone and administrators
        everyone = win32security.LookupAccountName("", "Everyone")[0]
        admins = win32security.LookupAccountName("", "Administrators")[0]
            # For the current user, you can get their SID from their access token
            # For example, using win32api.GetTokenInformation(win32security.OpenProcessToken(...), win32security.TokenUser)
        # Add Access Control Entries (ACEs).
        # You add ACEs to the DACL to define specific permissions for each SID. You use AddAccessAllowedAce or AddAccessDeniedAce methods, specifying the ACL_REVISION, desired access rights (e.g., con.FILE_GENERIC_ALL, con.FILE_READ_DATA), and the target SID.
        # Python
        # 1. Create a new Discretionary Access Control List (DACL)
        dacl = win32security.ACL()
        #dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_GENERIC_READ, everyone)
        # 2. add admins
        #The ntsecuritycon module provides access constants.
        dacl.AddAccessAllowedAce(
            win32security.ACL_REVISION,
            con.FILE_ALL_ACCESS,
            admins
            )
        # 3. Add an Access Allowed Entry (ACE) for the user.
        dacl.AddAccessAllowedAce(
            win32security.ACL_REVISION,
            con.FILE_GENERIC_WRITE|con.FILE_GENERIC_READ|con.FILE_GENERIC_EXECUTE,  # Grant all access rights
            user_sid
        )
        # Optional: Add an ACE to deny access to the 'Everyone' group, for example.
        # everyone_sid, _, _ = win32security.LookupAccountName("", "Everyone")
        # dacl.AddAccessDeniedAce(
        #     win32security.ACL_REVISION,
        #     con.FILE_ALL_ACCESS,
        #     everyone_sid
        # )
        # 4. Create a new security descriptor
        sd = win32security.SECURITY_DESCRIPTOR()
        # 5. Set the new DACL on the security descriptor
        # The first argument, 1, indicates that a DACL is present.
        # The third argument, 0, indicates the DACL was explicitly specified.
        sd.SetSecurityDescriptorDacl(1, dacl, 0)
        # 6. Create the SECURITY_ATTRIBUTES object
        sa = pywintypes.SECURITY_ATTRIBUTES()
        # 7. Attach the custom security descriptor
        sa.SECURITY_DESCRIPTOR.SetSecurityDescriptorDacl(1,dacl,0)
        # 8. Optionally, set the bInheritHandle flag (False by default)
        sa.bInheritHandle = False
        return sa
def send_pipe(eventlevel:str, service:str|None,msg_str:str|None):
    """
    Sends msgs to created pipe. Only availible on windows systems(for now)
    we require a tuple of 3 items (eventlevel,service,string msg)
    send our msg we cast our tuple to str then back on the other side
    This will morph into a heartbeat type system with a loop to provide updates
    or control mesages to each module.
    """
    message = str((eventlevel,service,msg_str))
    pipeName = r"\\.\pipe\Asrvc"
    data = win32pipe.CallNamedPipe(pipeName, message.encode(), 512, 0)
    #then recieve response and convert it back
    # to a tuple and do stuff
    #()
    data_to_tup = tuple(data.decode().encode())
    msg = data.decode()
    print(f"The service sent back: {msg}")

def create_pipe():
    """
    Creates a Pipe on windows systems for interprocess comms.
    """
    def run_pipe():
        if is_windows():
            pipeName = r"\\.\pipe\Asrvc"
            openMode = win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED
            pipeMode = win32pipe.PIPE_TYPE_MESSAGE
            # When running as a service, we must use special security for the pipe
            pipeaccess = set_pipe_access()
        #
            pipeHandle = win32pipe.CreateNamedPipe(
                pipeName,
                openMode,
                pipeMode,
                win32pipe.PIPE_UNLIMITED_INSTANCES,
                0,
                0,
                6000,  # default buffers, and 6 second timeout.
                pipeaccess,
            )
            
            hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            # We need to use overlapped IO for this, so we dont block when
            # waiting for a client to connect.  This is the only effective way
            # to handle either a client connection, or a service stop request.
            overlapped = pywintypes.OVERLAPPED()
            # And create an event to be used in the OVERLAPPED object.
            overlapped.hEvent = win32event.CreateEvent(None, 0, 0, None)
            
            # Loop accepting and processing connections
            while 1:
                try:
                    hr = win32pipe.ConnectNamedPipe(pipeHandle, overlapped)
                except Exception as e:
                    print("Error connecting pipe!", e)
                    pipeHandle.Close()
                    break
            
                if hr == winerror.ERROR_PIPE_CONNECTED:
                    # Client is fast, and already connected - signal event
                    win32event.SetEvent(overlapped.hEvent)
                # Wait for either a connection, or a service stop request.
                timeout = win32event.INFINITE
                waitHandles = hWaitStop, overlapped.hEvent
                rc = win32event.WaitForMultipleObjects(waitHandles, 0, timeout)
                if rc == win32event.WAIT_OBJECT_0:
                    # Stop event
                    break
                else:
                    # Pipe event - read the data, and write it back.
                    # (We only handle a max of 255 characters for this sample)
                    try:
                        hr, data = win32file.ReadFile(pipeHandle, 256)
                        #convert our string recieved back to tuple
                        backtotup = tuple(data.decode().encode())
                        # data is accesed as eventlevel,src,msg_str
                        #start logic here
                        win32file.WriteFile(pipeHandle, ("You sent me:" + data.decode()).encode())
                        # And disconnect from the client.
                        win32pipe.DisconnectNamedPipe(pipeHandle)
                    except win32file.error:
                        # Client disconnected without sending data
                        # or before reading the response.
                        # Thats OK - just get the next connection
                        continue
        if is_posix():
            pass
    threading.Thread(group=None,target=run_pipe,args=(),daemon=True).start()