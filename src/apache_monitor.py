# all standard python imports such as sys,os and the like are in core.py no need to
 #include again. only add libraries that are not a part of std libs.aka neeed to be pip installed
#left to show whats imported
#import threading
from .core import threading,log_event,is_posix,is_windows,settings
from .email_handler import *

apache_email_logger = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())

if is_posix():
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
    if is_posix():
        log_event("Monitoring apache logs",0,None,False)
        #
        threading.Thread(group=None,target=tail,args=(settings.get_config('current','ACCESS_LOG')),daemon=True).start()
        threading.Thread(group=None,target=tail,args=(settings.get_config('current','ERROR_LOG')),daemon=True).start()
    if is_windows():
        pass