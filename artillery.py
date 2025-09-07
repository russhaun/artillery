################################################################################
#
#  Artillery - An active honeypotting tool and threat intelligence feed
#
# Written by Dave Kennedy (ReL1K) @HackingDave
#
# A Binary Defense Project (https://www.binarydefense.com) @Binary_Defense
#
################################################################################
#

from src.core import threading,os,sys,time,signal,argparse,errno,is_windows,is_posix,settings,log_event,set_console_title, set_console_icon, current_version, freeze_check,get_pid,get_os,create_firewall_rules

#
if is_windows():
    from src.core import win32evtlog,write_windows_eventlog,isUserAdmin,runAsAdmin
    #from src.pyuac import isUserAdmin, runAsAdmin
    #from src.event_log import info
#################################################################################


class MainWindow():
    """
        Main Class file for handling gathering of all options avalible to artillery
    and presenting to user. All project scripts get imported and are
    executed from this class

    """

    def __init__(self) -> None:
        """init some defaults for class"""
        self.windowname = "Artillery - Advanced Threat Detection"
        self.appname = settings.get_config('global','APP_NAME')
        self.apppath = settings.get_config('global','APP_PATH')
        self.icon_path = settings.get_config('global','ICON_PATH')
        self.configfile = settings.get_config('global','CONFIG_FILE')
        self.logfile = settings.get_config('global','ALERT_LOG')
        self.banlist = settings.get_config('global','BANLIST')
        self.running_threads = []

    #
    
    def run(self):
        """runs final class object with configured settings"""
        FILE_PATH = freeze_check()
        log_event(f"[*] Artillery is running from {FILE_PATH}",0,None,False)
        set_console_title(self.windowname)
        current_version()
        get_os()
        get_pid()
        set_console_icon(self.windowname,os.path.join(self.icon_path,"bd_icon.ico"))
        
        self.load_services_as_thread()

    def shutdown(self):
        """calls sys.exit() and closes software"""
        if is_windows():
            write_windows_eventlog("Artillery",101,win32evtlog.EVENTLOG_INFORMATION_TYPE,False,None,None)
        log_event("[!] Ctrl-C Detected! Closing down.",0,None,True)
        log_event("[!] Exiting Artillery... hack the gibson.",0,None,True)
        time.sleep(5)
        sys.exit()

    def load_services_as_thread(self):
        """
        Starts load_services() in a thread.
        """
        threading.Thread(group=None,target=self.load_services,args=(),daemon=True).start()

    def load_services(self) -> None:
        """
            Loads all availible services depending on config returned
        all values are retrieved from config.py where all config
        checks are performed. this will be modified even further at some point
        """

        #   if we are running posix then lets create a new iptables chain
        # should we only set this up if banning is enabled?
        # this should be done later in process will be moved
        if is_posix():
            time.sleep(2)
            log_event("[*] Creating iptables entries, hold on.",0,None,True)
            create_firewall_rules()
            log_event("[*] iptables entries created.",0,None,True)
        #update artillery
        if settings.is_config_enabled("AUTO_UPDATE") == True:
            from src.core import update
            threading.Thread(group=None,target=update,args=(),daemon=True).start()
        #start anti_dos
        if settings.is_config_enabled("ANTI_DOS") == True:
            from src.anti_dos import start_anti_dos
            threading.Thread(group=None,target=start_anti_dos,args=(),daemon=True).start()
        #spawn honeypot
        if settings.is_config_enabled("ENABLE_HONEYPOT") == True:
            from src.honeypot import start_honeypot
            threading.Thread(group=None,target=start_honeypot,args=(),daemon=True).start()
        #start ssh monitor
        if settings.is_config_enabled("SSH_BRUTE_MONITOR") == True:
            from src.ssh_monitor import start_ssh_monitor
            threading.Thread(group=None,target=start_ssh_monitor,args=(),daemon=True).start()
        #start ftp monitor
        if settings.is_config_enabled("FTP_BRUTE_MONITOR") == True:
            from src.ftp_monitor import start_ftp_monitor
            threading.Thread(group=None,target=start_ftp_monitor,args=(),daemon=True).start()
        #start monitor engine
        if settings.is_config_enabled("MONITOR") == True:
            from src.monitor import monitor_start
            threading.Thread(group=None,target=monitor_start,args=(),daemon=True).start()
        # check system hardening
        if settings.is_config_enabled("SYSTEM_HARDENING") == True:
            from src.harden import hardening_checks
            threading.Thread(group=None,target=hardening_checks,args=(),daemon=True).start()
        # check to see if we are a threat server or not
        if settings.is_config_enabled("THREAT_SERVER") == True:
            from src.core import threat_server
            threading.Thread(group=None,target=threat_server,args=(),daemon=True).start()
        #recycle banlist if enabled
        #honestly this function isn't even needed. 
        #the banlist is completly re-written on update
        #and that time is every 24 hrs
        if settings.is_config_enabled("RECYCLE_IPS") == True:
            from src.core import refresh_banlist
            threading.Thread(group=None,target=refresh_banlist,args=(),daemon=True).start()
        #start apache monitor
        if settings.is_config_enabled("APACHE_MONITOR") == True:
            from src.apache_monitor import start_apache_log_monitor
            threading.Thread(group=None,target=start_apache_log_monitor,args=(),daemon=True).start()
        #pull additional source feeds from external parties other than 
        if settings.is_config_enabled("SOURCE_FEEDS") == True:
            from src.core import pull_source_feeds
            threading.Thread(group=None,target=pull_source_feeds,args=(),daemon=True).start()
        #
        log_event(f"[*] Artillery has started.",0,None,True)
        log_event(f"[*] Console logging enabled.",0,None,True)
        log_event(f"[*] Use Ctrl+C to exit.",0,None,True)
        #this will be moved into syslog function in future and called with log_event
        if is_windows():
            write_windows_eventlog('Artillery', 100, win32evtlog.EVENTLOG_INFORMATION_TYPE, False, None,msg=None)

def master_timer():
    """This function sleeps for the max that time.sleep() allows in a loop
    that calculates out to around a little over 1yr.

    the math is this:

           1yr = 31536000 secs.
           py3 max = 4294967 secs.

           4294967 x 8 = 34359736 secs

    so i added 1 to the total count to give me the yr i needed at 9 it quits

    """
    count_max = 9
    current_count = 0
    #4294967
    timer = [4294967]
    while current_count is not count_max:
        current_count += 1
        time.sleep(timer[0])

def admin_check(app: str) -> None:
    """
        Used with Mainwindow class. admin/root check for windows/linux platforms.
    takes app as string to use for calling app.run() if admin is True
    """
    if is_windows():
        if not isUserAdmin():
            runAsAdmin(cmdLine=None, wait=False)
            sys.exit(1)
        if isUserAdmin():
            app.run()
#
    if is_posix():
        # Check to see if we are root
        try:  # try and delete folder
            if os.path.isdir("/var/artillery_check_root"):
                os.rmdir('/var/artillery_check_root')
        #if not thow error and quit
        except OSError as err:
            if (err.errno == errno.EACCES or err.errno == errno.EPERM):
                
                log_event("[*] You must be root to run this script!\r\n",0,None,True)
                sys.exit(1)
        else:
            #if root run app
            app.run()

if __name__ == "__main__":
    RUNNING = True
    def sig_handler(signum, frame):
        """
        handles ctrl-c events to exit software.
        """
        global RUNNING
        RUNNING = False
        app.shutdown()
    #define signal to catch ctrl-c event
    signal.signal(signal.SIGINT, sig_handler)
    while RUNNING:
        #load the class
        app = MainWindow()
        #check admin status. i know this is wrong. check is in class
        #im passing the actual object MainWindow here. but it works
        #because i force a string object in call
        admin_check(app)
        #sleep for a long f-ing time approx 4.2 mil secs about 49.7 days in a loop
        #for a yr
        master_timer()
