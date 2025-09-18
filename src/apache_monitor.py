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
    apache_email_logger = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())
    def tail(some_file):
        this_file = open(some_file)
        # Go to the end of the file
        this_file.seek(0, 2)

        while True:
            line = this_file.readline()
            if line:
                yield line
            yield None


def start_apache_log_monitor():
    """
    Monitors Access and Error logs on apache servers
    """
    if settings.is_config_enabled("APACHE_MONITOR"):
        if is_posix():
            log_event(f"Starting {__appname__} v{__vesion__}",0,None,False)
            threading.Thread(group=None,target=tail,args=(settings.get_config('current','ACCESS_LOG')),daemon=True).start()
            threading.Thread(group=None,target=tail,args=(settings.get_config('current','ERROR_LOG')),daemon=True).start()
        if is_windows():
            pass
start_apache_log_monitor()