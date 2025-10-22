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
        self.icon_path = settings.get_config('global','ICON_PATH')

    #
    
    def run(self):
        """runs final class object with configured settings"""
        FILE_PATH = freeze_check()
        log_event(f"[*] {self.appname} is running from {FILE_PATH}",0,None,False)
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
        cleanup_iptables_artillery()
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
            Loads all availible services depending on config. 
            Checks are performed in individual files with settings from config file
            Each file starts its own thread if enabled.
        """
        from src.core import refresh_banlist, threat_server, pull_source_feeds, update, create_pipe
        
        #start the named srvcpipe for inter service communications windows only
        create_pipe()
        
        #changed the order of imports to reflect ordering in config file
        #all config checks are in the individual files/functions now
        #everything is per platform the function that runs each script
        #is invoked in said script @ the bottom no need to check here
        #start monitor engine
        import src.monitor
        # check system hardening
        import src.harden
        #spawn honeypot
        import src.honeypot
         #start ssh monitor
        import src.ssh_monitor
        #start ftp monitor
        import src.ftp_monitor
        #update artillery
        update()
        #start anti_dos
        import src.anti_dos
        #start apache monitor
        import src.apache_monitor
        # check to see if we are a threat server or not
        threat_server()
        #recycle banlist if enabled
        #honestly this function isn't even needed. 
        #the banlist is completly re-written @ runtime and on update
        #and that time is every 24 hrs
        refresh_banlist()
        #pull additional source feeds from external parties other than artillery
        pull_source_feeds()
        #
        time.sleep(2)
        #create iptables rules
        #put this here because pull source feeds updates the banlist
        # to make sure i get current banlist ips
        create_firewall_rules()
        log_event(f"[*] Artillery has started.\n[*] Console logging enabled.\n[*] Use Ctrl+C to exit.",0,None,True)
        #this will be moved in future and called with log_event
        if is_windows():
            write_windows_eventlog('Artillery', 100, win32evtlog.EVENTLOG_INFORMATION_TYPE, False, None,msg=None)

def master_timer():
    """This function sleeps for the max that time.sleep() allows in a loop
    that calculates out to around a little over 1yr.

    the math is this:

           1yr = 31536000 secs.
           py3 max = 4294967 secs.

           4294967 x 8 = 34359736 secs

    so i added 1 to the total count to give me the yr i wanted at 9 it quits

    """
    count_max = 9
    current_count = 0
    #4294967
    timer = [4294967]
    while current_count is not count_max:
        current_count += 1
        time.sleep(timer[0])



if __name__ == "__main__":
    RUNNING = True
    import ctypes, sys, os
if 'win' in sys.platform:
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()    
        except:
            return False
    if is_admin() == False:
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)  
    else:
    #only import if admin
        from src.core import threading,os,sys,time,signal,argparse,errno,win32evtlog,is_windows,is_posix,settings,log_event,set_console_title, set_console_icon, current_version, freeze_check,get_pid,get_os,create_firewall_rules,write_windows_eventlog,create_pipe
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
            app.run()
            #sleep for a long f-ing time approx 4.2 mil secs about 49.7 days in a loop
            #for a yr
            master_timer()
#cleaner soluton to see if we are root we actually use uid
if ('linux' or 'linux2' or 'darwin') in sys.platform:
    import os
    def is_root():
        """
            Checks if the current user is root on a Linux system.
            """
        return os.getuid() == 0
    if not is_root():
        print("The current user is not root")
        #debian 13 base
        os.execv(sys.executable, ['python3']+ sys.argv)
    else:
        #rint("The current user is root.")
        from src.core import threading,os,sys,time,signal,argparse,errno,is_windows,is_posix,settings,log_event,set_console_title, set_console_icon, current_version, freeze_check,get_pid,get_os,create_firewall_rules,cleanup_iptables_artillery
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
            app.run()
            #sleep for a long f-ing time approx 4.2 mil secs about 49.7 days in a loop
            #for a yr
            master_timer()
            
    
    
