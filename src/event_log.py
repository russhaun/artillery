"""
Script for use with Artillery from BinaryDefense it uses pywin32 api to send messages to eventlog on
windows systems. dll used is custom built for artillery
"""

# from pathlib import PureWindowsPath
# import os
from win32evtlogutil import ReportEvent, SafeFormatMessage
from win32api import GetCurrentProcess
from win32security import GetTokenInformation, TokenUser, OpenProcessToken
from win32con import TOKEN_READ
import win32evtlog
from .core import settings
#set some constants that we will use
mymsgDLL = settings.get_config('global',"EVENT_DLL")
data = "Application\0Data".encode("ascii")
#category is always one for now
category = int(1)
process = GetCurrentProcess()
token = OpenProcessToken(process, TOKEN_READ)
my_sid = GetTokenInformation(token, TokenUser)[0]
info = win32evtlog.EVENTLOG_INFORMATION_TYPE
warning = win32evtlog.EVENTLOG_WARNING_TYPE
err = win32evtlog.EVENTLOG_ERROR_TYPE

def write_windows_eventlog(AppName: str, eventID: int, event_type: str, send_toast: bool, ip: None):
    """
    Writes an event to windows event log using custom dll

    values:
        - AppName = name of app in windows eventlog
        - eventid = eventid to use
        - event_type = type of alert to use
        - send_toast = send toast alert or not. values accepted TRUE FALSE
        - ip = used for toast alerts if enabled can be None

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
    #place all globals here to make it easier to manipulate data from event
    ReportEvent(AppName, eventID, eventCategory=category, eventType=event_type, data=data, sid=my_sid)

def read_windows_eventlog(LogName: str, eventID: int, event_type: str):
    pass
   