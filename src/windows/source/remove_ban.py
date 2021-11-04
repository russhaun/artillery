##!/usr/bin/python
#
# simple remove banned ip
#
#
import re
import sys
import subprocess
#only import what we need from core files
from src.core import check_banlist_path, is_valid_ipv4, init_globals, is_posix, is_windows, write_console
import src.globals
if is_windows():
    from src.pyuac import isUserAdmin

#establish global values
init_globals()

if is_posix():
    try:
        ipaddress = sys.argv[1]
        if is_valid_ipv4(ipaddress):
            path = check_banlist_path()
            fileopen = open(path, "r")
            data = fileopen.read()
            data = data.replace(ipaddress + "\n", "")
            filewrite = open(path, "w")
            filewrite.write(data)
            filewrite.close()

            write_console("Listing all iptables looking for a match... if there is a massive amount of blocked IP's this could take a few minutes..")
            proc = subprocess.Popen("iptables -L ARTILLERY -n -v --line-numbers | grep %s" % (
                ipaddress), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

            for line in proc.stdout.readlines():
                line = str(line)
                match = re.search(ipaddress, line)
                if match:
                    # this is the rule number
                    line = line.split(" ")
                    line = line[0]
                    write_console(line)
                    # delete it
                    subprocess.Popen("iptables -D ARTILLERY %s" % (line),
                                    stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

        # if not valid then flag
        else:
            write_console("[!] Not a valid IP Address. Exiting.")
            sys.exit()

    except IndexError:
        write_console("Description: Simple removal of IP address from banned sites.")
        write_console("[!] Usage: remove_ban.py <ip_address_to_ban>")
#
#
if is_windows():
    #admin is required to delete route entries on windows
    if not isUserAdmin():
        write_console("[!] This script requires admin. Please relaunch from an elevated command prompt.")
        pause = input("[*] Press any key to continue")
        sys.exit()
    if isUserAdmin():
        def delete_route(ip):
            '''this will attempt to delete given ip from windows routing table using
            built in commands'''
            try:
                write_console("[*] Trying to delete entry.....")
                cmd = subprocess.run(['cmd', '/C', 'route', 'delete', ip], shell=True, check=True)
            except subprocess.CalledProcessError as err:
                write_console("[*] "+ err)
        #
        try:
            ipaddress = sys.argv[1]
            #remove entry from banlist
            #write_console("banlist path: "+ globals.g_banlist)
            if is_valid_ipv4(ipaddress):
                path = check_banlist_path()
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
                write_console("[!] Not a valid IP Address. Exiting.")
                sys.exit()
        #
        except IndexError:
            write_console("Description: Simple removal of IP address from banned sites.")
            write_console("[!] Usage: remove_ban.py <ip_address_to_ban>")
    