# #################################core module for reusable / central code####################################
#
import shutil
import time
import os
import re
import subprocess
import socket
from requests import Request, Session
import logging
import logging.handlers
import datetime
import signal
from string import *

#Import new settings class. import into other files from here.
# ex from .core import settings
from . import settings

# grab the current time
def grab_time() -> str:
    '''grabs current time and returns it in %Y-%m-%d %H:%M:%S format'''
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def gethostname() -> str:
    '''grabs hostname and returns it'''
    return socket.gethostname()

def get_host_ip() ->str:
    '''
    Grabs default internet connected ip and returns it.
    '''
    return socket.gethostbyname(gethostname())

def convert_to_classc(param) ->str:
    '''converts an ipaddr to cover whole block. ex: if the attacker addr is 192.168.2.1
    the resulting entry put in banlist is 192.168.2.0/24. Therefor blocking the entire range'''
    ipparts = param.split('.')
    classc = ""
    if len(ipparts) == 4:
        classc = ipparts[0] + "." + ipparts[1] + "." + ipparts[2] + ".0/24"
    return classc

#this fuction wiil change in future
def ban(ip):
    '''checks to see if a certain ip is on the banlist already if not adds it.
    On linux will add entry to iptables. On windows adds to routing table.'''
    ip = ip.rstrip()
    ban_check = settings.get_config("current","HONEYPOT_BAN").lower()
    ban_classc = settings.get_config("current","HONEYPOT_BAN_CLASSC").lower()
    test_ip = ip
    if "/" in test_ip:
        test_ip = test_ip.split("/")[0]
    #this check can be removed in future i do this on server connect
    # might produce dupe logs
    if is_whitelisted_ip(test_ip):
        log_event(f"Not banning IP {test_ip}, whitelisted",0,None,False)
        #write_log("Not banning IP %s, whitelisted" % test_ip)
        return
    if ban_check == "on":
        #none below upto platform check is needed as 
        #ip is verified before it gets to this point
        if not ip.startswith("#"):
            if not ip.startswith("0."):
                #this can be removed as we only accept connection if valid ip
                if is_valid_ipv4(ip.strip()):
                    # if we are running nix variant then trigger ban through
                    # iptables
                    if is_posix():
                        #this can be removed as well only accept connection if is not already banned
                        if not is_already_banned(ip):
                            if ban_classc == "on":

                                ip = convert_to_classc(ip)
                                subprocess.Popen(
                                    "iptables -I ARTILLERY 1 -s %s -j DROP" % ip, shell=True).wait()
                            iptables_logprefix = settings.get_config("current","HONEYPOT_BAN_LOG_PREFIX")
                            if iptables_logprefix != "":
                                subprocess.Popen("iptables -I ARTILLERY 1 -s %s -j LOG --log-prefix \"%s\"" % (ip, iptables_logprefix), shell=True).wait()

                    # if running windows then route attacker to some bs address.
                    if is_windows():
                        from .event_log import write_windows_eventlog, warning
                        #lets try and write an event log
                        #log_event(f"Banning {ip} for connecting to a honeypot port",1,200)
                        write_windows_eventlog("Artillery", 200, warning, False, None)
                        #now lets block em or mess with em route somewhere else?
                        routecmd = "route ADD %s MASK 255.255.255.255 10.255.255.255"
                        if ban_check == 'on':
                            if ban_classc == "on":
                                ip = convert_to_classc(ip)
                                ipparts = ip.split(".")
                                routecmd = "route ADD %s.%s.%s.0 MASK 255.255.255.0 10.255.255.255" % (ipparts[0], ipparts[1], ipparts[2])
                                subprocess.Popen("%s" % (routecmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                            else:
                                # or use the old way and just ban the individual ip
                                subprocess.Popen(routecmd % (ip), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    #add check with does_line_exist here
                    # add new IP to banlist
                    fileopen = open(settings.get_config('global',"BANLIST"), "r")
                    data = fileopen.read()
                    if ip not in data:
                        filewrite = open(settings.get_config('global',"BANLIST"), "a")
                        filewrite.write(ip + "\n")
                        filewrite.close()

                    if settings.is_config_enabled("LOCAL_BANLIST") == True:
                        fileopen = open(settings.get_config('global', "LOCAL_BANLIST"), "r")
                        data = fileopen.read()
                        if ip not in data:
                            filewrite = open(settings.get_config('global', "LOCAL_BANLIST"), "a")
                            filewrite.write(ip + "\n")
                            filewrite.close()


def update():
    '''updates artillery on linux platforms'''
    if is_posix():
        log_event("Running auto update (git pull)",0,None,True)
        if os.path.isdir(settings.get_config('global', "APPPATH") + "/.svn"):
            print(
                "[!] Old installation detected that uses subversion. Fixing and moving to github.",flush=True)
            try:
                if len(settings.get_config('global', "APPPATH")) > 1:
                    shutil.rmtree(settings.get_config('global', "APPPATH"))
                subprocess.Popen(
                    "git clone https://github.com/binarydefense/artillery", shell=True).wait()
            except:
                print(
                    "[!] Something failed. Please type 'git clone https://github.com/binarydefense/artillery %s' to fix!" % settings.get_config('global', "APPPATH"),flush=True)

        #subprocess.Popen("cd %s;git pull" % settings.get_config('global', "APPPATH"),
        #                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        update_cmd = execOScmd("cd %s; git pull" % settings.get_config('global', "APPPATH"))
        errorfound = False
        abortfound = False
        errormsg = ""
        for l in update_cmd:
            errormsg += "%s\n" % l
            if "error:" in l:
                errorfound = True
            if "Aborting" in l:
                abortfound = True
        if errorfound and abortfound:
            msg = f"Error updating artillery, git pull was aborted. Error:\n{errormsg}"
            log_event(msg,2,None,True)
            msg = "I will make a copy of the config file, run git stash, and restore config file"
            log_event(msg,2,None,True)
            saveconfig = "cp '%s' '%s.old'" % (settings.get_config('global',"LOGFILE"), settings.get_config('global',"LOGFILE"))
            execOScmd(saveconfig)
            gitstash = "git stash"
            execOScmd(gitstash)
            gitpull = "git pull"
            newpull = execOScmd(gitpull)
            restoreconfig = "cp '%s.old' '%s'" % (settings.get_config('global',"LOGFILE"), settings.get_config('global',"LOGFILE"))
            execOScmd(restoreconfig)
            pullmsg = ""
            for l in newpull:
                pullmsg += "%s\n" % l
            msg = "Tried to fix git pull issue. Git pull now says:"
            log_event(msg,2,None,True)
            #
            log_event(pullmsg,2,None,True)
        else:
            msg = f"Output 'git pull':\n{errormsg}"
            log_event(msg,0,None,False)
    if is_windows():
        #call update.exe/py
        pass


def addressInNetwork(ip, net):
    """
    returns true if the ip is in a given network
    """
    try:
        ipaddr = int(''.join(['%02x' % int(x) for x in ip.split('.')]), 16)
        netstr, bits = net.split('/')
        netaddr = int(''.join(['%02x' % int(x) for x in netstr.split('.')]), 16)
        mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
        return (ipaddr & mask) == (netaddr & mask)
    except:
        return False


def is_whitelisted_ip(ip):
    '''checks to see if a certain ip is on the whitelist and returns it'''
    # grab ips
    ipaddr = str(ip)
    whitelist = settings.get_config("current","WHITELIST_IP")
    whitelist = whitelist.split(',')
    for site in whitelist:
        if site.find("/") < 0:
            if site.find(ipaddr) >= 0:
                return True
            else:
                continue
        if addressInNetwork(ipaddr, site):
            return True
    return False

def is_valid_ipv6(ip):
    """validate ipv6 address.
    """
    pattern = re.compile(r"""
        ^
        \s*                         # Leading whitespace
        (?!.*::.*::)                # Only a single whildcard allowed
        (?:(?!:)|:(?=:))            # Colon iff it would be part of a wildcard
        (?:                         # Repeat 6 times:
            [0-9a-f]{0,4}           #   A group of at most four hexadecimal digits
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
        ){6}                        #
        (?:                         # Either
            [0-9a-f]{0,4}           #   Another group
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
            [0-9a-f]{0,4}           #   Last group
            (?: (?<=::)             #   Colon iff preceeded by exacly one colon
             |  (?<!:)              #
             |  (?<=:) (?<!::) :    #
             )                      # OR
         |                          #   A v4 address with NO leading zeros 
            (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            (?: \.
                (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            ){3}
        )
        \s*                         # Trailing whitespace
        $
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL)
    return pattern.match(ip) is not None

def does_line_exist(line):
    '''
    Checks for the existence of a line in banlist.
    returns True or False
    '''
    present = False
    banlist = settings.get_config('global', "BANLIST")
    query = line.strip()
    with open(file=banlist,mode="r",encoding="utf-8") as blist:
        for l in blist:
            result = l.strip()
            if result == query:
                present = True
                break
    #
    return present

def banlist_add_line(line):
    '''
    adds a line to the banlist uses does_line_exist 
    to check if line is present
    '''
    exists = does_line_exist(line)
    
    if exists == True:
        #log the event
        log_event(f"{line} already exists in banlist, not adding again", 0, None, False)
        return
    else:
        #add the line
        with open(settings.get_config('global', "BANLIST"), "a") as blist:
            blist.write(line + "\n")
        #if local banlist is enabled then add to that as well
        if settings.is_config_enabled("LOCAL_BANLIST") == True:
            with open(settings.get_config('global', "LOCAL_BANLIST"), "a") as blist:
                blist.write(line + "\n")
        #log the addition
        log_event(f"Added {line} to banlist", 0, None, False)

def banlist_remove_line(line):
    '''
    removes a line from the banlist uses 
    does_line_exist to check if line is present
    '''
    exists = does_line_exist(line)
    
    if exists == False:
        #log the event
        log_event(f"{line} does not exist in banlist, not removing", 0, None, True)
        return
    else:
        #remove the line
        with open(settings.get_config('global', "BANLIST"), "r") as blist:
            lines = blist.readlines()
        with open(settings.get_config('global', "BANLIST"), "w") as blist:
            for l in lines:
                if l.strip() != line.strip():
                    blist.write(l)
        #if local banlist is enabled then remove from that as well
        if settings.is_config_enabled("LOCAL_BANLIST") == True:
            with open(settings.get_config('global', "LOCAL_BANLIST"), "r") as blist:
                lines = blist.readlines()
            with open(settings.get_config('global', "LOCAL_BANLIST"), "w") as blist:
                for l in lines:
                    if l.strip() != line.strip():
                        blist.write(l)
        #log the removal
        log_event(f"Removed {line} from banlist", 0, None, False)


def is_valid_ipv4(ip):
    '''validate ipv4 address.'''
    # if IP is cidr, strip net
    if "/" in ip:
        ipparts = ip.split("/")
        ip = ipparts[0]
    if not ip.startswith("#"):
        pattern = re.compile(r"""
    ^
    (?:
      # Dotted variants:
      (?:
        # Decimal 1-255 (no leading 0's)
        [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
      |
        0x0*[0-9a-f]{1,2}  # Hexadecimal 0x0 - 0xFF (possible leading 0's)
      |
        0+[1-3]?[0-7]{0,2} # Octal 0 - 0377 (possible leading 0's)
      )
      (?:                  # Repeat 0-3 times, separated by a dot
        \.
        (?:
          [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
        |
          0x0*[0-9a-f]{1,2}
        |
          0+[1-3]?[0-7]{0,2}
        )
      ){0,3}
    |
      0x0*[0-9a-f]{1,8}    # Hexadecimal notation, 0x0 - 0xffffffff
    |
      0+[0-3]?[0-7]{0,10}  # Octal notation, 0 - 037777777777
    |
      # Decimal notation, 1-4294967295:
      429496729[0-5]|42949672[0-8]\d|4294967[01]\d\d|429496[0-6]\d{3}|
      42949[0-5]\d{4}|4294[0-8]\d{5}|429[0-3]\d{6}|42[0-8]\d{7}|
      4[01]\d{8}|[1-3]\d{0,9}|[4-9]\d{0,8}
    )
    $
    """, re.VERBOSE | re.IGNORECASE)
        return pattern.match(ip) is not None


def check_banlist_path():
    '''checks for banlist.txt if not found attempts to create one with header'''
    path = ""
    if is_posix():
        if os.path.isfile(settings.get_config('global',"BANLIST")):
            path = settings.get_config('global',"BANLIST")
        # if path is blank then try making the file
        if path == "":
            if os.path.isdir(settings.get_config('global', "APPPATH")):
                filewrite = open(settings.get_config('global',"BANLIST"), "w")
                filewrite.write(
                    "#\n#\n#\n# Binary Defense Systems Artillery Threat Intelligence Feed and Banlist Feed\n# https://www.binarydefense.com\n#\n# Note that this is for public use only.\n# The ATIF feed may not be used for commercial resale or in products that are charging fees for such services.\n# Use of these feeds for commerical (having others pay for a service) use is strictly prohibited.\n#\n#\n#\n")
                filewrite.close()
                path = settings.get_config('global',"BANLIST")
    #this fuction will be removed in the future 
    #as it is not needed currently it does nothing
    #the banlist is always true
    if is_windows():
        if os.path.isfile(settings.get_config('global',"BANLIST")):
            # grab the path
            path = settings.get_config('global',"BANLIST")
    #
    return path


def is_posix():
    '''returns true platform is posix related'''
    return os.name == "posix"


def is_windows():
    '''returns true platform is Windows related'''
    return os.name == "nt"

#only used on posix
def execOScmd(cmd, logmsg=""):
    '''execute OS command and to wait until it's finished'''
    if logmsg != "":
        log_event(f"execOSCmd: {logmsg}",0,None,False)
    p = subprocess.Popen('%s' % cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    outputobj = iter(p.stdout.readline, b'')
    outputlines = []
    for l in outputobj:
        thisline = ""
        try:
            thisline = l.decode()
        except:
            try:
                thisline = l.decode('utf8')
            except:
                thisline = "<unable to decode>"
        outputlines.append(thisline.replace('\\n', '').replace("'", ""))
    return outputlines

#unused code never called?
def execOScmdAsync(cmdarray):
    '''execute OS commands Asynchronously this one takes an array
    first element is application, arguments are in additional array elements'''
    p = subprocess.Popen(cmdarray)
    return
#only used on posix
def create_empty_file(filepath):
    '''creates an empty file at the given file path'''
    filewrite = open(filepath, "w")
    filewrite.write("")
    filewrite.close()

def write_banlist_banner(filepath):
    '''writes out banlist.txt header to file'''
    filewrite = open(filepath, "w")
    banner = """#
#
#
# Binary Defense Systems Artillery Threat Intelligence Feed and Banlist Feed
# https://www.binarydefense.com
#
# Note that this is for public use only.
# The ATIF feed may not be used for commercial resale or in products that are charging fees for such services.
# Use of these feeds for commerical (having others pay for a service) use is strictly prohibited.
#
#
#
"""
    filewrite.write(banner)
    filewrite.close()
#only used on posix
def create_iptables_subset():
    '''reads in ip info from banlist and other sources and adds them to to a fresh iptables chain
    for artillery'''
    #uneeded check
    if is_posix():
        ban_check = settings.get_config("current","HONEYPOT_BAN").lower()
        if ban_check == "on":
            # remove previous entry if it already exists
            execOScmd("iptables -D INPUT -j ARTILLERY", "Deleting ARTILLERY IPTables Chain")
            # create new chain
            log_event("Flushing iptables chain, creating a new one",0,None,False)
            execOScmd("iptables -N ARTILLERY -w 3")
            execOScmd("iptables -F ARTILLERY -w 3")
            execOScmd("iptables -I INPUT -j ARTILLERY -w 3")

    bannedips = []

    if not os.path.isfile(settings.get_config('global',"BANLIST")):
        create_empty_file(settings.get_config('global',"BANLIST"))
        write_banlist_banner(settings.get_config('global',"BANLIST"))

    banfile = open(settings.get_config('global',"BANLIST"), "r").readlines()
    banlength = len(banfile)
    banlocation = settings.get_config('global',"BANLIST")
    msg = f"Read {str(banlength)} lines in {banlocation}"
    log_event(msg,0,None,False)

    for ip in banfile:
        if not ip in bannedips:
            bannedips.append(ip)
    #change to is config enabled check
    if settings.is_config_enabled("LOCAL_BANLIST") == True:
        if not os.path.isfile(settings.get_config('global', "LOCAL_BANLIST")):
            create_empty_file(settings.get_config('global', "LOCAL_BANLIST"))
            write_banlist_banner(settings.get_config('global', "LOCAL_BANLIST"))
        localbanfile = open(settings.get_config('global', "LOCAL_BANLIST"), "r").readlines()
        lbanlength = len(localbanfile)
        lbanlocation = settings.get_config('global', "LOCAL_BANLIST")
        log_event(f"Read {str(lbanlength)} lines in {lbanlocation}",0,None,False)
        #write_log("Read %d lines in '%s'" % (len(localbanfile), settings.get_config('global', "LOCAL_BANLIST")))
        for ip in localbanfile:
            if not ip in bannedips:
                bannedips.append(ip)

    # if we are banning
    banlist = []
    if settings.get_config("current","HONEYPOT_BAN").lower() == "on":
        # iterate through lines from ban file(s) and ban them if not already
        # banned
        for ip in bannedips:
            if not ip.startswith("#") and not ip.replace(" ", "") == "":
                ip = ip.strip()
                if ip != "" and not ":" in ip:
                    test_ip = ip
                if "/" in test_ip:
                    test_ip = test_ip.split("/")[0]
                if not is_whitelisted_ip(test_ip):
                    if is_posix():
                        if not ip.startswith("0."):
                            if is_valid_ipv4(ip.strip()):
                                if settings.get_config("current","HONEYPOT_BAN_CLASSC").lower() == "on":
                                    if not ip.endswith("/24"):
                                        ip = convert_to_classc(ip)
                                    banlist.append(ip)
                    #not actually sure why this is here it never runs on windows
                    #if is_windows():

                    #    ban(ip)
                else:
                    log_event(f"Not banning IP {ip}, whitelisted",0,None,False)
                        #write_log("Not banning IP %s, whitelisted" % ip)
        if settings.get_config("current","LOCAL_BANLIST").lower() == "on":

            localbanfile = open(settings.get_config('global', "LOCAL_BANLIST"), "r").readlines()

    if len(banlist) > 0:

        # convert banlist into unique list
        log_event("Filtering duplicate entries in banlist",0,None,False)
        set_banlist = set(banlist)
        unique_banlist = (list(set_banlist))
        entries_at_once = 750
        total_nr = len(unique_banlist)
        msg = f"Mass loading {str(total_nr)} unique entries from banlist(s)"
        log_event(msg,0,None,True)
        nr_of_lists = int(len(unique_banlist) / entries_at_once) + 1
        iplists = get_sublists(unique_banlist, nr_of_lists)
        listindex = 1
        logindex = 1
        logthreshold = 25
        if len(iplists) > 1000:
            logthreshold = 100
        total_added = 0
        for iplist in iplists:
            ips_to_block = ','.join(iplist)
            massloadcmd = "iptables -I ARTILLERY -s %s -j DROP -w 3" % ips_to_block
            subprocess.Popen(massloadcmd, shell=True).wait()
            iptables_logprefix = settings.get_config("current","HONEYPOT_BAN_LOG_PREFIX")
            if iptables_logprefix != "":
                massloadcmd = "iptables -I ARTILLERY -s %s -j LOG --log-prefix \"%s\" -w 3" % (ips_to_block, iptables_logprefix)
                subprocess.Popen(massloadcmd, shell=True).wait()
            total_added += len(iplist)
            #log_event(f"{str(listindex)}/{str(len(iplists))} - Added {str(total_added)}/{str(total_nr)} IP entries to iptables chain.")
            write_log("%d/%d - Added %d/%d IP entries to iptables chain." % (listindex, len(iplists), total_added, total_nr))
            if logindex >= logthreshold:
                write_console("    %d/%d : Update: Added %d/%d entries to iptables chain" % (listindex, len(iplists), total_added, total_nr))
                logindex = 0
            listindex += 1
            logindex += 1
        
        write_console("    %d/%d : Done: Added %d/%d entries to iptables chain, thank you for waiting." % (listindex-1, len(iplists), total_added, total_nr))


def get_sublists(original_list, number_of_sub_list_wanted):
    '''gets and returns x num of list based on original input'''
    sublists = list()
    for sub_list_count in range(number_of_sub_list_wanted):
        sublists.append(original_list[sub_list_count::number_of_sub_list_wanted])
    return sublists

def is_already_banned(ip):
    '''checks to see if an ip is already banned and returns True or False
    checks routing table and banlist.txt, returns true or false for each

        :param ip  the ip to check

    '''
    #assume its not in either place
    route = False
    banlist = False
    ban_check = settings.get_config("current","HONEYPOT_BAN").lower()
    ban_classc = settings.get_config("current","HONEYPOT_BAN_CLASSC").lower()
    banfile = settings.get_config('global','BANLIST')
    #only check if banning is enabled
    if ban_check == "on":
        #lets check the routing table first
        if is_posix():
            proc = subprocess.Popen("iptables -L ARTILLERY -n --line-numbers",
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if is_windows():
            proc = subprocess.Popen("route print",
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        iptablesbanlist = proc.stdout.readlines()
        #convert the ip to classc if needed
        if ban_classc == "on":
            ip = convert_to_classc(ip)
        #check if ip is in the routing table
        if ip in iptablesbanlist:
            route = True
        #then check banlist it might be in the banlist but not in routing table?
        #maybe we have not seen it before. if is is do we just add from here or notify?
        #in the future this will be replaced with does_line_exist
        with open(banfile,'r',encoding='utf-8') as bancheck:
            for line in bancheck:
                line =line.strip()
                if line == ip:
                    #its in the banlist
                    banlist = True
        # will become a tuple response in future
        #return route, banlist
        return route
    else:
        #log_event("Honeypot banning is not enabled",0,None)
        return False

def systray_alert(id: int, alert: str):
    """
    sends an alert to the systray app(only valid on windows)

        :param id ex:  int value respresenting msgid on windows
        :param alert ex: Brute force attempt from "addr"
        
    
    """
    if is_windows():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # i could use bind_address here instead from config? but what if its blank
            #so i just grab the default ip on gateway connected net
            #create flag to handle in config systray_listener and systray_port
            #host = "127.0.0.1"
            host = get_host_ip()
            port = 10080
            sock.connect((host, port))
            log_event(f"[+] Sending systray alert to {str(host)}:{str(port)}",0,None,False)
            sock.send(alert.encode('utf-8'))  
            response = sock.recv(4096)
            log_event(f"[+] Received {repr(response.decode('utf-8'))}",0,None,False)
        sock.close()
        return
    if is_posix():
        log_event("Systray alerts are not supported on this platform",0,None,False)
        return


def is_valid_ip(ip) -> bool:
    '''returns True if is a valid ip address.
    Works on Ipv4/Ipv6'''
    valid = False
    if is_valid_ipv4(ip):
        valid = True
    else:
        if is_valid_ipv6(ip):
            valid = True
    return valid


def bin2ip(b):
    '''convert a binary string into an IP address'''
    ip = ""
    for i in range(0, len(b), 8):
        ip += str(int(b[i:i + 8], 2)) + "."
    return ip[:-1]


def ip2bin(ip):
    '''convert an IP address from its dotted-quad format to its 32 binary digit representation'''
    b = ""
    inQuads = ip.split(".")
    outQuads = 4
    for q in inQuads:
        if q != "":
            b += dec2bin(int(q), 8)
            outQuads -= 1
    while outQuads > 0:
        b += "00000000"
        outQuads -= 1
    return b


def dec2bin(n, d=None):
    '''convert a decimal number to binary representation
    if d is specified, left-pad the binary number with 0s to that length'''
    s = ""
    while n > 0:
        if n & 1:
            s = "1" + s
        else:
            s = "0" + s
        n >>= 1

    if d is not None:
        while len(s) < d:
            s = "0" + s
    if s == "":
        s = "0"
    return s

#this function is never called
def printCIDR(attacker_ip):
    '''print a list of IP addresses based on the CIDR block specified'''
    trigger = 0
    whitelist = settings.get_config("current","WHITELIST_IP")
    whitelist = whitelist.split(",")
    for c in whitelist:
        match = re.search("/", c)
        if match:
            parts = c.split("/")
            baseIP = ip2bin(parts[0])
            subnet = int(parts[1])
            # Python string-slicing weirdness:
            # if a subnet of 32 was specified simply print the single IP
            if subnet == 32:
                ipaddr = bin2ip(baseIP)
            # for any other size subnet, print a list of IP addresses by concatenating
            # the prefix with each of the suffixes in the subnet
            else:
                ipPrefix = baseIP[:-(32 - subnet)]
                for i in range(2**(32 - subnet)):
                    ipaddr = bin2ip(ipPrefix + dec2bin(i, (32 - subnet)))
                    ip_check = is_valid_ip(ipaddr)
                    # if the ip isnt messed up then do this
                    if ip_check != False:
                        # compare c (whitelisted IP) to subnet IP address
                        # whitelist
                        if c == ipaddr:
                            # if we equal each other then trigger that we are
                            # whitelisted
                            trigger = 1

    # return the trigger - 1 = whitelisted 0 = not found in whitelist
    return trigger


def threat_server():
    '''
    copies files for use with hosting a threat server
    '''
    public_http = settings.get_config("current","THREAT_LOCATION")
    if os.path.isdir(public_http):
        banfiles = settings.get_config("current","THREAT_FILE")
        if banfiles == "":
            banfiles = settings.get_config('global',"BANLIST")
        banfileparts = banfiles.split(",")
        while 1:
            for banfile in banfileparts:
                thisfile = settings.get_config('global', "APPPATH") + "/" + banfile
                subprocess.Popen("cp '%s' '%s'" % (thisfile, public_http), shell=True).wait()
                #write_log("ThreatServer: Copy '%s' to '%s'" % (thisfile, public_http))
            time.sleep(300)

def syslog(message, alerttype, evtid):
    """
    Handles various logging methods availible. writes to SYSLOG, Remote SYSLOG, FILE

        :param msg ex: "alert detected from 'addr'"
        :param alerttype ex: an int describing the level of the alert
        :param evtid ex: only used on windows this is the eventid used in msg dll
    """
    logtype = settings.get_config("current","SYSLOG_TYPE")
    alertindicator = ""
    if alerttype == -1:
        alertindicator = ""
    elif alerttype == 0:
        alertindicator = "[INFO]"
    elif alerttype == 1:
        alertindicator = "[WARN]"
    elif alerttype == 2:
        alertindicator = "[ERROR]"
    # if we are sending remote syslog
    if logtype == "REMOTE":
        import socket
        FACILITY = {
            'kern': 0, 'user': 1, 'mail': 2, 'daemon': 3,
            'auth': 4, 'syslog': 5, 'lpr': 6, 'news': 7,
            'uucp': 8, 'cron': 9, 'authpriv': 10, 'ftp': 11,
            'local0': 16, 'local1': 17, 'local2': 18, 'local3': 19,
            'local4': 20, 'local5': 21, 'local6': 22, 'local7': 23,
        }
        LEVEL = {
            'emerg': 0, 'alert': 1, 'crit': 2, 'err': 3,
            'warning': 4, 'notice': 5, 'info': 6, 'debug': 7
        }
        def syslog_send(
            message, level=LEVEL['notice'], facility=FACILITY['daemon'],
                        host='localhost', port=514):
            # Send syslog UDP packet to given host and port.
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data = '<%d>%s' % (level + facility * 8, message + "\n")
            sock.sendto(data.encode("ascii"), (host, port))
            sock.close()
        # send the syslog message
        remote_syslog = settings.get_config("current","SYSLOG_REMOTE_HOST")
        remote_port = int(settings.get_config("current","SYSLOG_REMOTE_PORT"))
        syslogmsg = message
        if alertindicator != "":
            syslogmsg = "Artillery%s: %s" % (alertindicator, message)
        #syslogmsg = "%s %s Artillery: %s" % (grab_time(), alertindicator, message)
        syslog_send(syslogmsg, host=remote_syslog, port=remote_port)
    # if we are sending local syslog messages
    #not currently in use although defind on windows
    # i use a custom dll for alerts
    #am  working on a solution
    elif logtype == "LOCAL":
        my_logger = logging.getLogger('Artillery')
        my_logger.setLevel(logging.DEBUG)
        if is_posix():
            handler = logging.handlers.SysLogHandler(address='/dev/log')
        if is_windows():
            #this will probably need to be changed to use our custom dll
            #i have not tested this yet
            #i have a working solution in win_func.py that is not used here
            handler = logging.handlers.NTEventLogHandler("Artillery",settings.get_config("global","EVENT_DLL"),"Application")
        my_logger.addHandler(handler)
        for line in message.splitlines():
            if alertindicator != "":

                my_logger.critical("Artillery%s: %s\n" % (alertindicator, line))
            else:
                my_logger.critical("%s\n" % line)

    # if we don't want to use local syslog and just write to file in
    # logs/alerts.log
    # this will eventually replace write_log func
    elif logtype == "FILE":
        if not os.path.isfile(settings.get_config('global',"ALERT_LOG")):
            with open(settings.get_config('global', "ALERT_LOG"),'x',encoding='utf-8') as alertlog:
                msg = f"{grab_time()} Artillery{alertindicator}: {message}\n"
                alertlog.write(msg)
        else:
            with open(settings.get_config('global', "ALERT_LOG"),'a',encoding='utf-8') as alertlog:
                msg = f"{grab_time()} Artillery{alertindicator}: {message}\n"
                alertlog.write(msg)
    
    #check to see if there is a windows event
    #
    if evtid == None:
        pass
    else:
        #unset for now but working
        # from .win_func import write_windows_eventlog
        # write_windows_eventlog("Artillery",evtid, alertindicator,False,None)
        pass
#this is only in use on certain posix func and will be removed in future
# this will be handled in log_event func 
def write_console(alert) -> None:
    '''writes alerts to console window'''
    if settings.is_config_enabled("CONSOLE_LOGGING") == True:
        alertlines = alert.split("\n")
        for alertline in alertlines:
            print("%s: %s" % (grab_time(), alertline),flush=True)
#
def log_event(alert: str, loglvl: int, evtid: int | None, console: bool)->None:
    """
    Logs events on artillery using configured settings. Hands off to syslog function  

        :param alert ex: f"alert detected from {addr}" or (subject,alert) for emails
        :param loglvl ex: an int 0/1/2 describing the level of the alert info/warn/error
        :param evtid ex: only used on windows this is the eventid used in msg dll can be None
        :param console ex: print to active console True or False

        ex: log_event("oops something went wrong with "insert error here",2,100,True")

        result: (logs to configured syslog, sets level as error, windows event id, prints to console)

        loglvl 2 events(error) are automatically written to local exceptions.log file as well as any
        configured destinations


        This will be threaded @ some point in the near future
    """
    #check to see if alert is a tuple here?
    #
    if console == True:
        if settings.is_config_enabled("CONSOLE_LOGGING") == True:
            alertlines = alert.split("\n")
            for alertline in alertlines:
                print(f"{grab_time()}: {alertline}",flush=True)
                #print("%s: %s" % (grab_time(), alertline),flush=True)
    #
    
    if loglvl == 2:
        log = settings.get_config("global", "EXCEPTION_LOG")
        if not os.path.isfile(log):
            with open(log,'x',encoding='utf-8') as event:
                event.write(str(alert) + "\n")
        else:
            with open(log, "a",encoding='utf-8') as event:
                event.write(str(alert) + "\n")
    #do email stuff here???

    
    syslog(alert,loglvl,evtid)


#this will be removed in future
#whole func is implemented in syslog
#only used in create_iptables_subset()
def write_log(alert, alerttype=0):

    """writes a log depending on platform. On linux it uses syslog func. On windows writes to alerts.log
     """
   
    if is_posix():
        syslog(alert, alerttype,None)
    #
    if is_windows():
        program_files = os.environ["PROGRAMFILES(X86)"]
        if not os.path.isdir("%s\\logs" % settings.get_config('global', "APPPATH")):
            os.makedirs("%s\\logs" % settings.get_config('global', "APPPATH"))
        if not os.path.isfile("%s\\logs\\alerts.log" % settings.get_config('global', "APPPATH")):
            filewrite = open(
                "%s\\logs\\alerts.log" % settings.get_config('global', "APPPATH"), "w")
            filewrite.write("***** Artillery Alerts Log *****\n")
            filewrite.close()
        filewrite = open("%s\\logs\\alerts.log" % settings.get_config('global', "APPPATH"), "a")
        filewrite.write(alert + "\n")
        filewrite.close()

def kill_artillery() -> None:
    ''' kill running instances of artillery'''
    try:
        proc = subprocess.Popen(
            "ps -A x | grep artiller[y]", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        pid, err = proc.communicate()
        pid = [int(x.strip()) for line in pid.split()
               for x in line.split() if int(x.isdigit())]
        for i in pid:
            log_event("Killing the old Artillery process...",0,None,True)
            os.kill(i, signal.SIGKILL)

    except Exception as e:
        print(e,flush=True)


def cleanup_artillery() -> None:
    '''
    cleans up iptables entries related to artillery
    '''
    ban_check = settings.get_config("current","HONEYPOT_BAN").lower()
    if ban_check == "on":
        subprocess.Popen("iptables -D INPUT -j ARTILLERY",
                         stdout=subprocess.PIP, stderr=subprocess.PIPE, shell=True)
        subprocess.Popen("iptables -X ARTILLERY",
                         stdout=subprocess.PIP, stderr=subprocess.PIPE, shell=True)
        return 0


def refresh_log() -> None:
    '''overwrite artillery banlist after certain time interval
        with the value retrived from config file for artillery_refresh '''
    while 1:
        interval = settings.get_config("current","ARTILLERY_REFRESH")
        try:
            interval = int(interval)
        except:
            # if the interval was not an integer, then just pass and don't do
            # it again
            break
        # sleep until interval is up
        time.sleep(interval)
        log_event("clearing banlist.txt",0,None,True)
        # overwrite the log with nothing
        create_empty_file(settings.get_config('global',"BANLIST"))
        write_banlist_banner(settings.get_config('global',"BANLIST"))
        #update after refresh? as the file is now empty


def format_ips(urls):

    '''
    Retrieves and formats ip lists from pull_source_feeds() func.
    Only looks for "200 OK" and "404 Notfound". Only adds if 200 OK
    recieved, alerts on all others. And then writes it to banfile
    For now i only validate ipv4 addresess. ipv6 wil be added in a future update.
  
    '''
    
    ip4_lst = []
    ip6_lst = []
    count4 = 0
    count6 = 0
    #create sesion handler object
    session_handler = Session()
    #add custom headers
    headers ={'user-agent': 'Artillery Banlist Updater V1'}
    for url in urls:
        log_event(f"Grabbing feed from {url}",0,None,True)
        if url.startswith("http"):
            req = Request(method='GET',url=url, headers=headers)
            prepped = req.prepare()
            response = session_handler.send(prepped)
            status = response.status_code
            data = response.text 
            if status == 200:
                #make any backups here
                #write_log("Backing up existing banlist")
                #subprocess.call(['cmd', '/C', 'copy', ban_file, backup_dest])
                #time.sleep(1)
                #convert data to a list
                line = data.split("\n")
                #check for ip4/ip6 address ignore anything else
                for item in line:
                    if is_valid_ipv4(item) == True:
                      count4 +=1
                      ip4_lst.append(item)
                    elif is_valid_ipv6(item) == True:
                      count6 +=1
                      ip6_lst.append(item)
                    else:
                        pass
            #
            elif status == 404:
                log_event(f"HTTPError: Error 404, URL {url} not found.",1,None,True)
            else:
                #this is a catchall for things i don't know about
                msg = format(response.status_code)
                msg_to_string =  f"[!] Received URL Error trying to download feed from {url} Reason: {msg}"
                log_event(msg_to_string,1,None,True)
    
    #turn our lists into a string with just ips
    lst4 = '\n'.join(ip4_lst)
    lst6 = '\n'.join(ip6_lst)
    #send off to sort banlist
    sort_banlist(lst4, lst6)

def pull_source_feeds():
    '''update threat intelligence feed with other sources.'''
    log_event("[*] Pulling from source feeds please wait.......",0,None,True)
    while 1:
        url_list = []
        counter = 0
        # if we are using source feeds
        if f"{settings.get_config('current','SOURCE_FEEDS')}" == "ON":
            urls = ["http://rules.emergingthreats.net/blockrules/compromised-ips.txt", "http://lists.blocklist.de/lists/apache.txt", "http://lists.blocklist.de/lists/ssh.txt"]
            for url in urls:
                url_list.append(url)
            counter = 1
        # if we are using threat intelligence feeds
        if settings.get_config('current','THREAT_INTELLIGENCE_FEED') == "ON":
            threat_feed = settings.get_config('current','THREAT_FEED')
            if threat_feed != "":
                threat_feed = threat_feed.split(",")
                for threats in threat_feed:
                    url_list.append(threats)
            counter = 1
        # if we used source feeds or ATIF
        if counter == 1:
            log_event("[*] Done pulling from source feeds.",0,None,False)
            format_ips(url_list)
            time.sleep(86400)  # sleep for 24 hours


def sort_banlist(ip4,ip6) -> None:
    '''Create banlist from source_feeds list.This will wipe 
      the banlist and refresh on every run.after creating a backup
      of existing file first if exists.
    '''
    banner = """#
#
#
# Binary Defense Systems Artillery Threat Intelligence Feed and Banlist Feed
# https://www.binarydefense.com
#
# Note that this is for public use only.
# The ATIF feed may not be used for commercial resale or in products that are charging fees for such services.
# Use of these feeds for commerical (having others pay for a service) use is strictly prohibited.
#
#
#
  """
    uniquenewentries = 0
    ban_file = settings.get_config("global", "BANLIST")
    #backup_src = globalsettings.get("APP_PATH")
    #backup_dest = backup_src+"\\logs"
    cips = ip4.split("\n")
    #open the banlist
    with open(ban_file,"w",encoding="utf-8")as banlist:
        #make any backups here
        #write_log("Backing up existing banlist")
        #subprocess.call(['cmd', '/C', 'copy', ban_file, backup_dest])
        #time.sleep(1)
        #wipe the current contents and write new banner
        banlist.flush()
        banlist.write(banner + "\n")
        #and jump to last line
        banlist.seek(0, 2)
        for item in cips:
            #check to see if is valid ip or just junk
            line = is_valid_ipv4(item) 
            if line == True:
                    # if config.read_config("HONEYPOT_BAN_CLASSC").lower() == "on":
                    #     line = convert_to_classc(item)
                uniquenewentries += 1
                banlist.write(item +"\n")
    log_event("[*] Done creating new banlist from source feeds.",0,None,True)
    #get current line count of banfile
    ban_file_len = open(ban_file,"r",encoding="utf-8").readlines()
    #subtract lines fron banlist header
    final_count = len(ban_file_len) - 13
    log_event(f"[*] Added {str(final_count)} entries to banlist",0,None,True)
