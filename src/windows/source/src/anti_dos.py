
#!/usr/bin/python
# all standard python imports such as sys,os and the like are in core.py no need to
# include again import from core.py. only add libraries that are not a part of std libs.aka neeed to be pip installed
# please only add to respective is_platform call when importing 3rd party or from core.py
###################################################################################################
from .core import is_posix,is_windows,log_event,settings

__appname__ = "Anti-Dos"
__vesion__ = "1.0"
__author__ = ""
__requires__ = []
__description__ = "Sets limits in iptables chain to limit connections"


if is_posix():
    from .core import threading,subprocess
    from .email_handler import *
    antidos_email_logger = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())
    def start_anti_dos():  
        anti_dos_ports = settings.get_config('current', 'ANTI_DOS_PORTS')
        anti_dos_ports_split = anti_dos_ports.split(",")
        for ports in anti_dos_ports_split:
            subprocess.Popen("iptables -A ARTILLERY -p tcp --dport %s -m limit --limit %s/minute --limit-burst %s -j ACCEPT" %
                (ports, settings.get_config('current',"ANTI_DOS_THROTTLE_CONNECTIONS"), settings.get_config('current','ANTI_DOS_LIMIT_BURST')), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).wait()
        
def setup_antidos():
    if settings.is_config_enabled("ANTI_DOS") == True:
        if is_posix():
            log_event(f"[*] Starting {__appname__} v{__vesion__}",0,None,True)
            threading.Thread(group=None,target=start_anti_dos,args=(),daemon=True).start()
        if is_windows():
            pass
setup_antidos()