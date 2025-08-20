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
import signal
import time
import sys
import os
import _thread as thread
import argparse
import errno

from src.core import is_windows,is_posix, check_banlist_path,settings,log_event

#
if 'win32' in sys.platform:
    from src.pyuac import isUserAdmin, runAsAdmin
    from src.win_func import get_pid, get_title, get_os, current_version, freeze_check
    from src.event_log import write_windows_eventlog, info
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
        self.configfile = settings.get_config('global','CONFIG_FILE')
        self.logfile = settings.get_config('global','ALERT_LOG')
        self.banlist = settings.get_config('global','BANLIST')
        self.running_threads = []

    #
    #
    def run(self):
        """runs final class object with configured settings"""
        if is_windows():
            FILE_PATH = freeze_check()
            log_event(f"[*] Artillery is running from {FILE_PATH}",0,None,False)
            get_title(self.windowname)
            current_version()
            get_os()
            get_pid()
        # if is_posix():
        #     if not os.path.isdir(globals.g_apppath + "/database/"):
        #         os.makedirs(globals.g_apppath + "/database/")
        #     if not os.path.isfile(globals.g_apppath + "/database/temp.database"):
        #         filewrite = open(globals.g_apppath + "/database/temp.database", "w")
        #         filewrite.write("")
        #         filewrite.close()
        #
        self.load_services_as_thread()

    def kill_running_threads(self):
        """
        kills all running threads. used during shutdown to clean up active threads.
        """
        pass

    def shutdown(self):
        """calls sys.exit() and closes software"""
        log_event("[!] Ctrl-C Detected! Closing down.",1,None,True)
        log_event("[!] Exiting Artillery... hack the gibson.",1,None,True)
        time.sleep(5)
        #kill any threads here
        
        #self.kill_running_threads()
        sys.exit()

    def load_services_as_thread(self):
        """
        Starts load_services() in a thread.
        """
        loadid = thread.start_new_thread(self.load_services, ())
        self.running_threads.append(loadid)

    def load_services(self) -> None:
        """
            Loads all availible services depending on config returned
        all values are retrieved from config.py where all config
        checks are performed.the use of start_new_thread() in the future
        will be removed in favor of the more current Thread availible in py3.
        """
        #this function on windows is uneeded 
        # as the way the banlist is created
        # it is always present will be removed in future
        check_banlist_path()

        #if we are running posix then lets create a new iptables chain
        if is_posix():
            from src.core import create_iptables_subset
            time.sleep(2)
            log_event("[*] Creating iptables entries, hold on.",0,None,True)
            create_iptables_subset()
            log_event("[*] iptables entries created.",0,None,True)
        #update artillery
        if settings.is_config_enabled("AUTO_UPDATE") == True:
            from src.core import update
            updateid = thread.start_new_thread(update, ())
            self.running_threads.append(updateid)
        #start anti_dos
        if settings.is_config_enabled("ANTI_DOS") == True:
            from src.anti_dos import start_anti_dos
            antidosid = thread.start_new_thread(start_anti_dos, ())
            self.running_threads.append(antidosid)
        #spawn honeypot
        if settings.is_config_enabled("ENABLE_HONEYPOT") == True:
            from src.honeypot import start_honeypot
            thread.start_new_thread(start_honeypot, ())
        #start ssh monitor
        if settings.is_config_enabled("SSH_BRUTE_MONITOR") == True:
            from src.ssh_monitor import start_ssh_monitor
            thread.start_new_thread(start_ssh_monitor, ())
        #start ftp monitor
        if settings.is_config_enabled("FTP_BRUTE_MONITOR") == True:
            from src.ftp_monitor import start_ftp_monitor
            thread.start_new_thread(start_ftp_monitor, ())
        #start monitor engine
        if settings.is_config_enabled("MONITOR") == True:
            if is_posix():
                from src.monitor import start_monitor
                thread.start_new_thread(start_monitor, ())
            if is_windows():
                from src.monitor import watch_folders
                thread.start_new_thread(watch_folders, ())
        # check system hardening
        if settings.is_config_enabled("SYSTEM_HARDENING") == True:
            from src.harden import hardening_checks
            thread.start_new_thread(hardening_checks, ())
        # check to see if we are a threat server or not
        if settings.is_config_enabled("THREAT_SERVER") == True:
            from src.core import threat_server
            thread.start_new_thread(threat_server, ())
        #recycle banlist if enabled
        #honestly this function isn't even needed. 
        #the banlist is completly re-written on update
        if settings.is_config_enabled("RECYCLE_IPS") == True:
            from src.core import refresh_log
            thread.start_new_thread(refresh_log, ())
        #start apache monitor
        if settings.is_config_enabled("APACHE_MONITOR") == True:
            from src.apache_monitor import start_apache_log_monitor
            thread.start_new_thread(start_apache_log_monitor, ())
        #pull additional source feeds from external parties other than 
        if settings.is_config_enabled("SOURCE_FEEDS") == True:
            from src.core import pull_source_feeds
            thread.start_new_thread(pull_source_feeds, ())
        #
        log_event(f"[*] Artillery has started.",0,None,True)
        log_event(f"[*] Console logging enabled.",0,None,True)
        log_event(f"[*] Use Ctrl+C to exit.",0,None,True)
        #this will be moved into syslog function in future and called with log_event
        if is_windows():
            write_windows_eventlog('Artillery', 100, info, False, None)

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
                
                print("[*] You must be root to run this script!\r\n",flush=True)
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
