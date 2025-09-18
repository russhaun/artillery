#!/usr/bin/python
# all standard python imports such as sys,os and the like are in core.py no need to
# include again import from core.py. only add libraries that are not a part of std libs.aka neeed to be pip installed
#please only add to respective is_platform call when importing 3rd party
###################################################################################################
from .core import is_posix,is_windows,log_event,settings
__appname__ = "SSH Bruteforce monitor"
__vesion__ = "1.0"
__author__ = ""
__requires__ = []
__description__ = "Monitors ssh logs from various *nix distros for brute force attempts"


#only define function if posix and setup values
if is_posix():
    from .core import os,re,time,is_valid_ipv4,is_whitelisted_ip,ban,threading
    from .email_handler import *
    ssh_email_logger = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())
    banlist = settings.get_config("current","BANLIST")
    ssh_brute_attempts = settings.get_config("current", "SSH_BRUTE_ATTEMPTS")

    def ssh_monitor(monitor_frequency: int) -> None:
        counter = 0
        while 1:
            # for debian base
            if os.path.isfile("/var/log/auth.log"):
                fileopen1 = open("/var/log/auth.log", "r")
                counter = 1

                # for OS X
                if os.path.isfile("/var/log/secure.log"):
                    if counter == 0:
                        fileopen1 = open("/var/log/secure.log", "r")
                        counter = 1

            # for centOS
            if os.path.isfile("/var/log/secure"):
                if counter == 0:
                    fileopen1 = open("/var/log/secure", "r")
                    counter = 1

            # for Debian
            if os.path.isfile("/var/log/faillog"):
                if counter == 0:
                    fileopen1 = open("/var/log/faillog", "r")
                    counter = 1
            # if we have not found any logs then we stop
            if counter == 0:
                log_event("[*] No SSH logs found. SSH monitor now stops.", 2, None, False)
                break
            
            try:
                # base ssh counter to see how many attempts we've had
                ssh_counter = 0
                counter = 0
                for line in fileopen1:
                    counter = 0
                    fileopen2 = open(banlist, "r")
                    line = line.rstrip()
                    # search for bad ssh
                    match = re.search("Failed password for", line)
                    if match:
                        ssh_counter = ssh_counter + 1
                        line = line.split(" ")
                        # pull ipaddress
                        ipaddress = line[-4]
                        if is_valid_ipv4(ipaddress):

                            # if its not a duplicate then ban that ass
                            if ssh_counter >= int(ssh_brute_attempts):
                                ban_list = fileopen2.read()
                                match = re.search(ipaddress, ban_list)
                                if match:
                                    counter = 1
                                    # reset SSH counter
                                    ssh_counter = 0

                                # if counter is equal to 0 then we know that we
                                # need to ban
                                if counter == 0:
                                    whitelist_match = is_whitelisted_ip(ipaddress)
                                    if whitelist_match == 0:
                                        subject = "[!] Artillery has banned an SSH brute force. [!]"
                                        alert = "Artillery has blocked (blacklisted) the following IP for SSH brute forcing violations: " + ipaddress
                                        #setup the email here with our class
                                        #set the subject 
                                        #set the alert
                                        #write to the trigger file
                                        # do the actual ban, this is pulled from
                                        ban(ipaddress)
                                        ssh_counter = 0
                                        # wait one to make sure everything is caught up
                                        time.sleep(1)
                # sleep for defined time
                time.sleep(monitor_frequency)

            except Exception as e:
                log_event(f"[*] An error in ssh monitor occured. Printing it out here: {str(e)}",2,None,False)


def start_ssh_monitor():
    if is_posix():
        monitor_frequency = settings.get_config("current", "SSH_MONITOR_FREQUENCY")
        log_event(f"[*] Launching {__appname__} v{__vesion__}.",0,None,True)
        threading.Thread(group=None,target=ssh_monitor,args=(int(monitor_frequency)),daemon=True).start()
    if is_windows():
        pass
start_ssh_monitor()