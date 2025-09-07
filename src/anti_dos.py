
# basic for now, more to come
#
# all standard python imports such as sys,os and the like are in core.py no need to
 #include again. only add libraries that are not a part of std libs.aka neeed to be pip installed
# left to show whats imported
# import subprocess
from .core import is_posix,is_windows,subprocess,settings
from .email_handler import *

antidos_email_logger = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())

def start_anti_dos():
    if is_posix():
        log_event("[*] Activating anti DoS.",0,None,True)
        anti_dos_ports = settings.get_config('current', 'ANTI_DOS_PORTS')
        anti_dos_ports_split = anti_dos_ports.split(",")
        for ports in anti_dos_ports_split:
            subprocess.Popen("iptables -A ARTILLERY -p tcp --dport %s -m limit --limit %s/minute --limit-burst %s -j ACCEPT" %
                (ports, settings.get_config('current',"ANTI_DOS_THROTTLE_CONNECTIONS"), settings.get_config('current','ANTI_DOS_LIMIT_BURST')), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).wait()
    if is_windows():
        pass