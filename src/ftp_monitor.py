#!/usr/bin/python
# all standard python imports such as sys,os and the like are in core.py no need to
# include again import from core.py. only add libraries that are not a part of std libs.aka neeed to be pip installed
# please only add to respective is_platform call when importing 3rd party or from core.py
###################################################################################################
#
# monitor ftp and ban
# added by e @ Nov 5th
#############################

from .core import is_posix,is_windows,settings,log_event
#
__appname__ = "Ftp Monitor"
__vesion__ = "1.0"
__author__ = ""
__requires__ = []
__description__ = "Monitors vsftpd server files"
#
#only define if posix
if is_posix():
    from .core import os,re,is_whitelisted_ip,banlist_add_line,is_valid_ipv4,threading
    from .email_handler import *
    ftp_email_logger = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())
    ftp_brute_attempts = settings.get_config("current","FTP_BRUTE_ATTEMPTS")
    #every 2 mins
    monitor_frequency = 120

    def ftp_monitor(monitor_time):
        '''
        Monitors vsftpd server files for bruteforce attempts.
        if threshold from config is breached ip is blocked.
        '''
        while 1:
            # for debian base
            if os.path.isfile("/var/log/vsftpd.log"):
                fileopen1 = open("/var/log/auth.log", "r")
            else:
                log_event("Have not found configuration file for ftp. Ftp monitor now stops.",0,None,True)
                break
            #
            try:
                # base ftp counter to see how many attempts we've had
                ftp_counter = 0
                counter = 0
                for line in fileopen1:
                    counter = 0
                    fileopen2 = open(settings.get_config('global',"BANLIST"), "r")
                    line = line.rstrip()
                    # search for bad ftp
                    match = re.search("CONNECT: Client", line)
                    if match:
                        ftp_counter = ftp_counter + 1
                        # split based on spaces
                        line = line.split('"')
                        # pull ipaddress
                        ipaddress = line[-2]
                        ip_check = is_valid_ipv4(ipaddress)
                        if ip_check != False:
                            # if its not a duplicate then ban that ass
                            if ftp_counter >= int(ftp_brute_attempts):
                                banlist = fileopen2.read()
                                match = re.search(ipaddress, banlist)
                                if match:
                                    counter = 1
                                    # reset FTP counter
                                    ftp_counter = 0
                                # if counter is equal to 0 then we know that we
                                # need to ban
                                if counter == 0:
                                    whitelist_match = is_whitelisted_ip(ipaddress)
                                    if whitelist_match is False:
                                        alert = f"[!] Artillery has banned an FTP brute force. The following IP has been blocked: {ipaddress}"
                                        #warn_the_good_guys(alert_user, alert)
                                        #
                                        log_event(alert,2,None,False)
                                        # write_log(
                                        #     "Artillery has blocked (blacklisted) the following IP for FTP brute forcing violations: " + ipaddress)

                                        # do the actual ban, this is pulled from
                                        # src.core
                                        banlist_add_line(ipaddress)
                                        ftp_counter = 0
                                        # wait one to make sure everything is
                                        # caught up
                                        time.sleep(1)
                # sleep for defined time
                time.sleep(monitor_time)
            #logs to exception log and console
            except Exception as e:
                log_event("[*] An error in ftp monitor occured. Printing it out here: " + str(e),2,None,True)


def start_ftp_monitor():
    """
    Starts ftp monitor service. Currently only availible on posix based systems
    """
    if settings.is_config_enabled("FTP_BRUTE_MONITOR") == True:
        if is_posix() :
            log_event("[*] Launching FTP Bruteforce monitor.",0,None,True)
            threading.Thread(group=None,target=ftp_monitor,args=(monitor_frequency),daemon=True).start()
        if is_windows():
            pass
start_ftp_monitor()