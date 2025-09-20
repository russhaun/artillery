#!/usr/bin/python
# all standard python imports such as sys,os and the like are in core.py no need to
# include again import from core.py. only add libraries that are not a part of std libs.aka neeed to be pip installed
# please only add to respective is_platform call when importing 3rd party or from core.py
###################################################################################################
from .core import threading,log_event,is_posix,is_windows,settings

__appname__ = "Apache log monitor"
__vesion__ = "1.0"
__author__ = ""
__requires__ = []
__description__ = "Monitors apache ERROR and ACCESS logs."
#

#
if is_posix():
    from .email_handler import *
    #from pathlib import PurePosixPath
    apache_email_logger = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())
    def tail(path:list):
        #mabye file is not there?#debian 13 base
        # if os.path.isfile(str(path)):
        #     log_event(f"[*] Starting tail on {str(path)}",0,None,True)
        this_file = open(file=str(path),mode='r',encoding='utf-8')
        # Go to the end of the file
        this_file.seek(0, 2)
        while True:
            line = this_file.readline()
            if line:
                yield line
            yield None
    
    def access_logs():
        acceslog = settings.get_config('current','ACCESS_LOG')
        #mabye file is not there?#debian 13 base
        if os.path.isfile(str(acceslog)):
            log_event(f"[*] Starting tail on {str(acceslog)}",0,None,True)
            lines = tail(acceslog)
            for line in lines:
                log_event(f"{line}",0,None,True)
        else:
            log_event(f"[*] {acceslog} not found stopping tail",0,None,True)
        
    def error_logs():
        errorlog = settings.get_config('current','ERROR_LOG')
        #mabye file is not there?#debian 13 base
        if os.path.isfile(str(errorlog)):
            log_event(f"[*] Starting tail on {str(errorlog)}",0,None,True)
            lines = tail(errorlog)
            for line in lines:
                log_event(f"{line}",0,None,True)
        else:
            log_event(f"[*] {errorlog} not found stopping tail",0,None,True)

def start_apache_log_monitor():
    """
    Monitors Access and Error logs on apache servers
    """
    "/var/log/apache2/access.log"
    if settings.is_config_enabled("APACHE_MONITOR") == True:
        if is_posix():
            log_event(f"[*] Starting {__appname__} v{__vesion__}",0,None,True)
            threading.Thread(group=None,target=access_logs,args=(),daemon=True).start()
            threading.Thread(group=None,target=error_logs,args=(),daemon=True).start()
        if is_windows():
            pass
start_apache_log_monitor()