##!/usr/bin/python
#
# simple remove banned ip
#
#
import re
import sys
import subprocess
from src.core import is_valid_ipv4, check_banlist_path, settings, is_valid_ip, log_event
if 'win32' in sys.platform:
    from src.pyuac import isUserAdmin,runAsAdmin
##THIS ENTIRE SCRIPT WILL BE REPLACED IN FUTURE VERSIONS
##WITH A MORE ROBUST CMDLINE UTILITY IN PROGRESS WHICH WILL CONSOLIDATE
##ALL ARTILLERY CMDLINE TOOLS INTO ONE UTILITY DEALING WITH FIREWALL AND BANLIST MANAGEMENT
##THIS INCLUDES THE ABILITY TO ADD, DELETE,UPDATE,CHECK AND LIST BANLIST ENTRIES AND FIREWALL RULES
##check_banlist_path will be replaced with settings.get_config('global', 'BANLIST') in future version
##is valid_ipv4 will be replaced with is_valid_ip which has ipv4\ipv6 support from core.py
##does_line _exist will be added from core.py to check if line exists in banlist

def linux_route():
    """
    removes given ip addr from iptables and also banlist
    """
    try:
        ipaddress = sys.argv[1]
        #read banlist path
        path = check_banlist_path()
        if is_valid_ipv4(ipaddress):
            log_event(f"Searching iptables chain looking for {ipaddress}... If there is a massive amount of blocked IP's this could take a few minutes..", 0, None, True)
            proc = subprocess.Popen("iptables -L ARTILLERY -n -v --line-numbers | grep %s" % (
                ipaddress), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            #
            for line in proc.stdout.readlines():
                line = str(line)
                match = re.search(ipaddress, line)
                if match:
                    line = line.split(" ")
                    #this is the rule number
                    line = line[0]
                    log_event(f"[*] Deleting entry {line} from iptables chain", 0, None, True)
                    # delete entry from iptables chain
                    subprocess.Popen("iptables -D ARTILLERY %s" % (line), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                    #remove entry from banlist
                    fileopen = open(path, "r")
                    data = fileopen.read()
                    data = data.replace(ipaddress + "\n", "")
                    filewrite = open(path, "w")
                    filewrite.write(data)
                    filewrite.close()
        # if not valid then flag
        else:
            log_event("[!] Not a valid IP Address. Exiting.", 1, None, True)
            sys.exit()
    except IndexError:
        log_event("Description: Simple removal of IP address from banned sites.", 0, None, True)
        log_event("[!] Usage: remove_ban.py <ip_address_to_ban>", 0, None, True)

def windows_route():

    """
    this will attempt to delete given ip from windows routing table using built in commands
    """
    #this admin check will be moved in future versions
    #and placed elsewhere
    if not isUserAdmin():
        # runAsAdmin(cmdLine=None, wait=False)
        # sys.exit(1)
        log_event("[!] This script requires admin. Please relaunch from an elevated command prompt.",1,None,True)
        pause = input("[*] Press any key to continue")
        sys.exit()
    if isUserAdmin():
        def delete_route(ip):
            '''
            deletes given ip from windows routing table.
            will probably be removed in future in favor of 
            firewall options availible in utils/fwutils.py
            Will be incorporated into docker functions 
            if config is enabled  :)))'''
            try:
                log_event(f"[*] Trying to delete entry {ip} from routing table", 0, None, True)
                cmd = subprocess.run(['cmd', '/C', 'route', 'delete', ip], shell=True, check=True)
            except subprocess.CalledProcessError as err:
                log_event(f"[!] Error deleting route: {err}", 1, None, True)
        #
        try:
            ipaddress = sys.argv[1]
            #remove entry from banlist
            if is_valid_ip(ipaddress):
                path = settings.get_config('global', 'BANLIST')
                #path = check_banlist_path()
                fileopen = open(path, "r")
                data = fileopen.read()
                data = data.replace(ipaddress + "\n", "")
                filewrite = open(path, "w")
                filewrite.write(data)
                filewrite.close()
                fileopen.close()
                #remove entry from routing table
                delete_route(ipaddress)
            else:
                log_event("[!] Not a valid IP Address. Exiting.", 1, None, True)
                sys.exit()
        #
        except IndexError:
            log_event("Description: Simple removal of IP address from banned sites.", 0, None, True)
            log_event("[!] Usage: remove_ban.py <ip_address_to_ban>", 0, None, True)
            


if __name__ == "__main__":
    if 'win32' in sys.platform:
        windows_route()
    #
    if ('linux' or 'linux2' or 'darwin') in sys.platform:
        linux_route()
