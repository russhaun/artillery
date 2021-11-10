
################################################################################
#
#  Artillery - An active honeypotting tool and threat intelligence feed
#
# Written by Dave Kennedy (ReL1K) @HackingDave
#
# A Binary Defense Project (https://www.binarydefense.com) @Binary_Defense
#
################################################################################
import time
import sys
# needed for backwards compatibility of python2 vs 3 - need to convert to threading eventually
try:
    import thread
except ImportError:
    import _thread as thread
import os
import traceback
from src.pyuac import isUserAdmin, runAsAdmin
# import artillery global variables
#from src.windows.utils.debug.decorators import debug
#import src.globals
#from src.core import init_globals,check_config, write_console, write_log, is_posix,is_windows,check_banlist_path,is_config_enabled,update,create_iptables_subset, update, threat_server,refresh_log,pull_source_feeds
from src.core import *
from src.win_func import get_update_info, get_pid, get_title, get_os, current_version


init_globals()
#
if is_windows():#this is for launching script as admin from batchfile.
    if not isUserAdmin():# will prompt for user\pass and open in seperate window when you double click batchfile
        get_update_info()
        runAsAdmin(cmdLine=None, wait=False)
        sys.exit(1)
    if isUserAdmin():
        write_console("Artillery is running from '%s'" % globals.g_apppath)
        check_config()
        title = get_title()
        ver = current_version()
        write_console(ver)
        os_result = get_os()
        PROCID = get_pid()
        write_console(PROCID)
        from src.events import ArtilleryStartEvent
        #create temp datebase and continue
    if not os.path.isfile(str(globals.g_database)):
        filewrite = open(globals.g_database , "w")
        filewrite.write("")
        filewrite.close()

if is_posix():
    # Check to see if we are root
    try: # and delete folder
        if os.path.isdir("/var/artillery_check_root"):
            os.rmdir('/var/artillery_check_root')
            #if not thow error and quit
    except OSError as err:
        if (err.errno == errno.EACCES or err.errno == errno.EPERM):
            print("[*] You must be root to run this script!\r\n")
        sys.exit(1)
    else:
        check_config()
        if not os.path.isdir(globals.g_apppath + "/database/"):
            os.makedirs(globals.g_apppath + "/database/")
        if not os.path.isfile(globals.g_apppath + "/database/temp.database"):
            filewrite = open(globals.g_apppath + "/database/temp.database", "w")
            filewrite.write("")
            filewrite.close()




# prep everything for artillery first run
check_banlist_path()

try:
    # update artillery
    if is_config_enabled("AUTO_UPDATE"):
        thread.start_new_thread(update, ())

    # if we are running posix then lets create a new iptables chain
    if is_posix():
        time.sleep(2)
        write_console("Creating iptables entries, hold on.")
        create_iptables_subset()
        write_console("iptables entries created.")
        if is_config_enabled("ANTI_DOS"):
            write_console("Activating anti DoS.")
            # start anti_dos
            import src.anti_dos

    # spawn honeypot
    write_console("Launching honeypot.")
    import src.honeypot

    # spawn ssh monitor
    if is_config_enabled("SSH_BRUTE_MONITOR") and is_posix():
        write_console("Launching SSH Bruteforce monitor.")
        import src.ssh_monitor

    # spawn ftp monitor
    if is_config_enabled("FTP_BRUTE_MONITOR") and is_posix():
        write_console("Launching FTP Bruteforce monitor.")
        import src.ftp_monitor

    # start monitor engine
    if is_config_enabled("MONITOR"):
        if is_posix():
            from src.monitor import start_monitor
            thread.start_new_thread(start_monitor, ())
        if is_windows():
            from src.monitor import watch_folders
            thread.start_new_thread(watch_folders, ())
    #
    if is_config_enabled("SYSTEM_HARDENING"):
        # check hardening
        write_console("Check system hardening.")
        import src.harden

    # start the email handler
    if is_config_enabled("EMAIL_ALERTS") and is_posix():
        write_console("Launching email handler.")
        import src.email_handler

    # check to see if we are a threat server or not
    if is_config_enabled("THREAT_SERVER"):
        write_console("Launching threat server thread.")
        thread.start_new_thread(threat_server, ())

    # recycle IP addresses if enabled
    if is_config_enabled("RECYCLE_IPS"):
        write_console("Launching thread to recycle IP addresses.")
        thread.start_new_thread(refresh_log, ())

    # pull additional source feeds from external parties other than artillery
    write_console("Launching thread to get source feeds, if needed.")
    thread.start_new_thread(pull_source_feeds, ())
    # let the program to continue to run
    write_console("All set.")
    write_console("Artillery has started \nIf on Windows Ctrl+C to exit. \nConsole logging enabled.")
    write_log("Artillery is up and running")
    # write to windows log to let know artillery has started
    if is_windows():
        ArtilleryStartEvent()
    while 1:
        try:
            time.sleep(100000)
        except KeyboardInterrupt:
            print("\n[!] Exiting Artillery... hack the gibson.\n")
            sys.exit()

except KeyboardInterrupt:
    sys.exit()

except Exception as err:
    E_MSG = traceback.format_exc()
    print("General exception: " + format(err) + "\n" + E_MSG)
    write_log("Error launching Artillery\n%s" % (E_MSG),2)

    sys.exit()
