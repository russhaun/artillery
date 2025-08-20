import sys
from .core import settings,log_event
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
    if 'linux'or'linux2'or 'darwin' in sys.platform :
        log_event("Monitoring apache logs",0,None,False)
        #these will be threaded later
        # tail(access_log_path)
        # tail(error_log_path)
        pass