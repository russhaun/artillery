# all standard python imports such as sys,os and the like are in core.py no need to
# include again import from core.py. only add libraries that are not a part of std libs.aka neeed to be pip installed
# please only add to respective is_platform call when importing 3rd party or from core.py
###################################################################################################
from .core import is_posix,is_windows,log_event,settings
from .email_handler import *
__appname__ = "harden"
__vesion__ = "1.0"
__author__ = ""
__requires__ = []
__description__ = "Performs basic hardening checks depending on platform\nOn windows checks: smb,llmnr,wpad\nOn linux checks: ssh,ftp"


harden_email_logger = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())


if is_windows():
    from .core import re,os,subprocess,EnumValue,OpenKey,win32evtlog,write_windows_eventlog
    #
    def windows_harden_check():
        """
            Performs checks on windows systems to see if known vulnerable services are enabled
        and alerts if found. llmnr,wpad,smbv1. this func still needs alot of work to be effective
        at properly detecting status of components.uses the registry heavily

        Note:

                This whole routine wil be replaced at some point. i am devoloping script with
            funtions to handle registry exclusivly with no txt files. 90% finished

        """
        #loglink prints the full url to copy and paste
        #printlink is what is printed to screen
        srvlog = '[*] Service Check: SMBv1 was detected!!!. Please refer to this link and follow instructions.\n https://support.microsoft.com/en-us/help/2696547/how-to-detect-enable-and-disable-smbv1-smbv2-and-smbv3-in-windows-and'
        srvprint = '[*] Service Check: Please refer to alerts.log for more information on steps to take'
        srvwarning = '[*] Service Check: SMBv1 Server is enabled!!!. Unless absolutly neccessary please disable.\n'
        srvdisabled = '[*] Service Check: SMBv1 Server is disabled'
            #SMBv1 server check. there are 2 more keys for now i just read one of them WIP
        try:
            srvkey = r'SYSTEM\CurrentControlSet\Services\LanmanServer'
            srvkeyctr = 0
            srvkeyval = OpenKey(HKEY_LOCAL_MACHINE, srvkey)
            while True:
                    #prints out results to txt file to parse for needed strings below
                srvsubkey = EnumValue(srvkeyval, srvkeyctr)
                smbcheck = open("smbsrv_check.txt", "a",encoding='utf-8')
                smbcheck.write(str(srvsubkey))
                srvkeyctr += 1
            #catch the error when it hits end of the key
        except WindowsError:
            smbcheck.close()
            #Now open the file and search the results for values wanted.
            srvdata = open('smbsrv_check.txt', 'r',encoding='utf-8')
            srvresults = srvdata.read()
            #just look for the string Srv2 for now.
            srvmatch = re.findall('Srv2', srvresults)
            if srvmatch:
                log_event(str(srvdisabled),0,None,True)
                    # write_console(str(srvdisabled))
                    # write_log(str(srvdisabled))
            else:
                log_event(str(srvwarning) + str(srvlog),1,None,True)
                write_windows_eventlog("Artillery", 301, win32evtlog.EVENTLOG_WARNING_TYPE, False, None,msg=None)
                # write_console(str(srvwarning) + str(srvprint))
                # write_log(str(srvwarning) + str(srvlog))
        srvdata.close()
        #SMBv1 Clientside component
        #use the strings from above because why not
        cliprint = srvprint
        clilog = srvlog
        cliwarning = '[*] Service Check: SMBv1 Client is enabled!!!. Unless absolutly neccessary please disable.\n'
        clidisabled = '[*] Service Check: SMBv1 Client is disabled'
        try:
            cli = 0
            CliKey = r'SYSTEM\CurrentControlSet\Services\LanmanWorkstation'
            CliKeyValue = OpenKey(HKEY_LOCAL_MACHINE, CliKey)
            while True:
                clisubkey = EnumValue(CliKeyValue, cli)
                clicheck = open('smbcli_check.txt', 'a',encoding='utf-8')
                clicheck.write(str(clisubkey))
                cli += 1
        except WindowsError:
            clicheck.close()
            clidata = open('smbcli_check.txt', 'r',encoding='utf-8')
            cliresults = clidata.read()
            #just look for the string MRxSmb20 for now.
            climatch = re.findall('MRxSmb20', cliresults)
            if climatch:
                log_event(str(clidisabled),0,None,True)
            else:
                write_windows_eventlog("Artillery", 300, win32evtlog.EVENTLOG_WARNING_TYPE, False, None,msg=None)
                log_event(str(cliwarning) + str(clilog),1,None,True)
        clidata.close()
        #Check for WinHTTP Web Proxy Auto-Discovery Service (wpad) being disabled
        try:
            wpadctr = 0
            wpadsvckey = r'SYSTEM\CurrentControlSet\Services\WinHttpAutoProxySvc'
            wpadsvcvalue = OpenKey(HKEY_LOCAL_MACHINE, wpadsvckey)
            while True:
                wpadsubkey = EnumValue(wpadsvcvalue, wpadctr)
                wpadcheck = open('wpad_check.txt', 'a')
                wpadcheck.write(str(wpadsubkey))
                wpadctr += 1
        except WindowsError:
            wpadcheck.close()
            #
            wpaddata = open('wpad_check.txt', 'r')
            wpadresults = wpaddata.read()
            #just look for the wpadoverride string for now.
            wpadmatch = re.findall('WpadOverride', wpadresults)
            if wpadmatch:
                log_event("[*] Service Check: WPAD Override key is present",0,None,True)
            else:
                write_windows_eventlog("Artillery", 302, win32evtlog.EVENTLOG_WARNING_TYPE, False, None,msg=None)
                log_event("[*] Service Check: WPAD overide key is not present. you will be vuln to MITM attacks",1,None,True)
        wpaddata.close()
        #check for LLMNR
        try:
            llmnrctr = 0
            llmnrkey = r'SOFTWARE\Policies\Microsoft\Windows NT\DNSClient'
            #added for cases where key is not present
            try:
                llmnrkeyvalue = OpenKey(HKEY_LOCAL_MACHINE, llmnrkey)
            except FileNotFoundError:
                log_event("[*] Service Check: LLMNR key is not present skipping",0,None,True)
                return
            #if we main find key iterate through dumping all values
            while True:
                llmnrsubkey = EnumValue(llmnrkeyvalue, llmnrctr)
                llmnrcheck = open('llmnr_check.txt', 'a',encoding='utf-8')
                llmnrcheck.write(str(llmnrsubkey))
                llmnrctr += 1
        #catch error by default this key is not present which means it is enabled
        except WindowsError:
            llmnrcheck.close()
            llmnrdata = open('llmnr_check.txt', 'r',encoding='utf-8')
            llmnrresults = llmnrdata.read()
            #just look for the multicast string for now.
            llmnrmatch = re.findall('EnableMulticast', llmnrresults)
            if llmnrmatch:
                log_event("[*] Service Check: LLMNR key to disable multicast is present",0,None,True)
            else:
                write_windows_eventlog("Artillery",303, win32evtlog.EVENTLOG_WARNING_TYPE, False, None,msg=None)
                log_event("[*] Service Check: LLMNR key to disable multicast is not present. you might be vuln to MITM attacks",0,None,True)
        llmnrdata.close()
        #remove files that were created to make sure we get consistant results
        #if we don't it will forever append the file and make it bigger.
        #to see what i dump comment these lines to keep files
        path = settings.get_config('global',"APP_PATH")
        if os.path.isfile(path+"\\smbcli_check.txt"):
            subprocess.call(['cmd', '/C', 'del', path+"\\smbcli_check.txt"], shell=True)
            subprocess.call(['cmd', '/C', 'del', path+"\\smbsrv_check.txt"], shell=True)
            subprocess.call(['cmd', '/C', 'del', path+"\\llmnr_check.txt"], shell=True)
            subprocess.call(['cmd', '/C', 'del', path+"\\wpad_check.txt"], shell=True)
# flag warnings, base is nothing
warning = ""
if is_posix():
    from .core import re,os
    def linux_harden_check():
        if os.path.isfile("/etc/ssh/sshd_config"):
            fileopen = open("/etc/ssh/sshd_config", "r")
            data = fileopen.read()
            if settings.is_config_enabled("ROOT_CHECK") is True:
                match = re.search("RootLogin yes", data)
                # if we permit root logins trigger alert
                if match:
                    # trigger warning if match
                    warning = warning + \
                            "[!] Issue identified: /etc/ssh/sshd_config allows RootLogin. An attacker can gain root access to the system if password is guessed. Recommendation: Change RootLogin yes to RootLogin no\n\r\n\r"
                match = re.search(r"Port 22\b", data)
                if match:
                    if settings.is_config_enabled("SSH_DEFAULT_PORT_CHECK") is True:
                        # trigger warning if match
                        warning = warning + "[!] Issue identified: /etc/ssh/sshd_config. SSH is running on the default port 22. An attacker commonly scans for these type of ports. Recommendation: Change the port to something high that doesn't get picked up by typical port scanners.\n\r\n\r"
                # add SSH detection for password auth
                match = re.search("PasswordAuthentication yes", data)
                # if password authentication is used
                if match:
                    warning = warning + \
                        "[!] Issue identified: Password authentication enabled. An attacker may be able to brute force weak passwords.\n\r\n\r"
                    match = re.search("Protocol 1|Protocol 2,1", data)
                #
                if match:
                    # triggered
                    warning = warning + \
                        "[!] Issue identified: SSH Protocol 1 enabled which is potentially vulnerable to MiTM attacks. https://www.kb.cert.org/vuls/id/684820\n\r\n\r"
            #
            # check ftp config
            #
            if os.path.isfile("/etc/vsftpd.conf"):
                fileopen = open("/etc/vsftpd.conf", "r")
                data = fileopen.read()
                match = re.search("anonymous_enable=YES", data)
                if match:
                    # trigger warning if match
                    warning = warning + \
                        "[!] Issue identified: /etc/vsftpd.conf allows Anonymous login. An attacker can gain a foothold to the system with absolutel zero effort. Recommendation: Change anonymous_enable yes to anonymous_enable no\n\r\n\r"
            #
            # check /var/www permissions
            #
            if os.path.isdir("/var/www/"):
                for path, subdirs, files in os.walk("/var/www/"):
                    for name in files:
                        trigger_warning = 0
                        filename = os.path.join(path, name)
                        if os.path.isfile(filename):
                            # check permission
                            check_perm = os.stat(filename)
                            check_perm = str(check_perm)
                            match = re.search("st_uid=0", check_perm)
                            if not match:
                                trigger_warning = 1
                            match = re.search("st_gid=0", check_perm)
                            if not match:
                                trigger_warning = 1
                            # if we trigger on vuln
                            if trigger_warning == 1:
                                warning = warning + \
                                    "Issue identified: %s permissions are not set to root. If an attacker compromises the system and is running under the Apache user account, could view these files. Recommendation: Change the permission of %s to root:root. Command: chown root:root %s\n\n" % (
                                        filename, filename, filename)

            #
            # if we had warnings then trigger alert
            #
            if len(warning) > 1:
                subject = "[!] Insecure configuration detected on filesystem: "
                #this is where email is dealt with
                #warn_the_good_guys(subject, subject + warning)
#
def hardening_checks():
    '''
    Runs certain hardening checks based on platform
    '''
    if settings.is_config_enabled("SYSTEM_HARDENING") == True:
        log_event(f"[*] Starting {__appname__} v{__vesion__} loading service checks.....",0,None,True)
        if is_windows():
            threading.Thread(group=None,target=windows_harden_check,args=(),daemon=True).start()
        if is_posix():
            threading.Thread(group=None,target=linux_harden_check,args=(),daemon=True).start()
#
hardening_checks()
