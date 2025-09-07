##removeban.py responsible for Adding/removing entries to artillery banlist/routingtable/firewall/iptables
# this will be modified more as features are included in project


from src.core import argparse,re,sys,subprocess,os,errno,is_windows, is_posix, settings, log_event, banlist_add_line ,banlist_remove_line,is_whitelisted_ip,is_valid_ipv4,is_already_banned,convert_to_classc,is_valid_ip,does_line_exist

if is_posix():
    def add_iptables_rule(ipaddress:str):
        ip = ipaddress.rstrip()
        #only continue if valid ip
        is_valid = is_valid_ip(ip)
        if is_valid == False:
            #just return and give a warning
            log_event(f"Provided ip: {ip} is not valid please check the address",0,None,True)
            return
        else:
            #ip is good we can continue
            ban_check = settings.is_config_enabled("HONEYPOT_BAN")
            ban_classc = settings.is_config_enabled("HONEYPOT_BAN_CLASSC")
            if is_whitelisted_ip(ip):
                log_event(f"[*] Not banning IP {ip}, whitelisted",0,None,False)
                return
            if ban_check == True:
                if not is_already_banned(ip):
                    if ban_classc == True:
                        ip = convert_to_classc(ip)
                    subprocess.Popen("iptables -I ARTILLERY 1 -s %s -j DROP" % ip, shell=True).wait()
                    iptables_logprefix = settings.get_config("current","HONEYPOT_BAN_LOG_PREFIX")
                    if iptables_logprefix != "":
                        subprocess.Popen("iptables -I ARTILLERY 1 -s %s -j LOG --log-prefix \"%s\"" % (ip, iptables_logprefix), shell=True).wait()
    #
    def delete_iptables_rule(ipaddress:str):
        ip = ipaddress.strip()
        #only continue if valid ip
        is_valid = is_valid_ip(ip)
        if is_valid == False:
            #just return and give a warning
            log_event(f"Provided ip: {ip} is not valid please check the address",0,None,True)
            return
        else: 
            exists = check_for_iptables_rule(ip)
            if exists == False:
                log_event(f"[*] Rule for {ip} not present nothing to do",0,None,True)
                return
            else:
                log_event(f"[*] Deleting entry {ip} from iptables chain", 0, None, True)
                     # delete entry from iptables chain
                subprocess.Popen("iptables -D ARTILLERY %s" % (ip), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    #
    def check_for_iptables_rule(ip:str)->bool:
        """
        Checks to see if ip address is in iptables chain
        """
        exists = False
        #this could be very noisy watch this event
        log_event(f"Searching iptables chain looking for {ip}... If there is a massive amount of blocked IP's this could take a few minutes..", 0, None, True)
        proc = subprocess.Popen("iptables -L ARTILLERY -n -v --line-numbers | grep %s" % (ip), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        for line in proc.stdout.readlines():
            line = str(line)
            match = re.search(ip, line)
            if match:
                exists = True
                break
        return exists

    def add_linux_route(destination:str, gateway=None, dev=None)->bool:
        """
        Adds ip address from routing table

        Args:
            destination (str): The destination network or host (e.g., '192.168.1.0/24' or '10.0.0.1').
            gateway (str, optional): The gateway IP address. Required for deleting a route via a specific gateway.
            dev (str, optional): The network interface associated with the route.
        """
        success = False
        command = ["ip", "route", "add", f"{destination}"]
        
        if gateway:
            command.extend(['via', gateway])
        if dev:
            command.extend(['dev', dev])
        try:
            subprocess.run(command, check=True)
            print(f"Route to {ip} successfully added.")
            success = True
        except subprocess.CalledProcessError as e:
            print(f"Error deleting route: {e}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
        return success
    
    def delete_linux_route(destination, gateway=None, dev=None):
        """
        Deletes a route from the Linux routing table.

        Args:
            destination (str): The destination network or host (e.g., '192.168.1.0/24' or '10.0.0.1').
            gateway (str, optional): The gateway IP address. Required for deleting a route via a specific gateway.
            dev (str, optional): The network interface associated with the route.
        """
        command = ['ip', 'route', 'del', destination]

        if gateway:
            command.extend(['via', gateway])
        if dev:
            command.extend(['dev', dev])

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Route to {destination} successfully deleted.")
        except subprocess.CalledProcessError as e:
            print(f"Error deleting route: {e}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")

if is_windows():
    #import win32process
    #import win32com.client
    from src.core import isUserAdmin,runAsAdmin,write_windows_eventlog,log_event,win32process,traceback,win32comclient,win32evtlog

    def prepare_firewall_rule_name(ip:str) -> str:
        """
        returns a firewall rulename by appending a prefix to the ip_address.
        passed in at runtime 

        Args:
            ip (str): The IP address to be used in the rule name.
        """
        if ip is not None:
            rule_prefix = "Artillery_Block_"
            return f"{rule_prefix}{ip}"
        else:
            raise ValueError("IP address cannot be empty.")
        

    def add_firewall_rule(ipaddress:str, port=str|None, protocol=str|None):
        """
        Adds a Windows Firewall rule by its name.

        Args:
            ipaddress (str): The name of the firewall rule to add.
            port (int, optional): The port number to apply the rule to. Defaults to None.
            protocol (str, optional): The protocol to apply the rule to. Can be 'TCP" or 'UDP'. Defaults to None.
        """
        name = prepare_firewall_rule_name(ip=ipaddress)
        #check for the rule first
        exists = check_for_firewall_rule(ipaddress)
        if exists == True:
            log_event(f"[*] Rule {name} exists. Not adding",0,None,True)
            return
        #
        try:
            net_fw_policy2 = win32comclient.Dispatch("HNetCfg.FwPolicy2")
            new_rule = win32comclient.Dispatch("HNetCfg.FwRule")
            new_rule.Name = name
            new_rule.Description = "Rule created by Artillery"
            new_rule.Action = 0  # Allow (0 for Block)
            new_rule.Direction = 1  # Inbound (0 for Outbound)
            if protocol is not None:
                if protocol == "TCP":
                    new_rule.Protocol = 6  # TCP
                elif protocol == "UDP":
                    new_rule.Protocol = 17  # UDP
                else:
                    raise ValueError("Protocol must be 'TCP' or 'UDP'")
            else:
                # Default to TCP if no protocol is specified
                log_event("[*] No protocol specified, defaulting to TCP.",0,None,True)
                new_rule.Protocol = 6  # TCP (17 for UDP)
            if port is not None:
                #
                new_rule.LocalPorts = str(port)
            new_rule.RemoteAddresses = ipaddress
            new_rule.Enabled = True
            log_event(f"[*] Adding firewall rule: {new_rule.Name}, port: {new_rule.LocalPorts}, protocol: {new_rule.Protocol}",0,None,True)
            net_fw_policy2.Rules.Add(new_rule)
            log_event(f"[*] Firewall rule '{new_rule.Name}' added successfully.",0,None,True)
        except Exception as e:
            #import traceback
            log_event(f"Error adding firewall rule '{new_rule.Name}': {e}",1,None,True)
            traceback.print_exc()
    

    def delete_firewall_rule(ipaddress:str):
        """
        Deletes a Windows Firewall rule by its ipaddress if not already there.

        Args:
            ipaddr (str): The ip in the firewall to delete.
        """
        doesexist = check_for_firewall_rule(ip=ipaddress)
        if doesexist is False:
            #just return
            return
        else:

            name =f"Artillery_Block_{ipaddress}"
            try:
                net_fw_policy2 = win32comclient.Dispatch("HNetCfg.FwPolicy2")
                net_fw_policy2.Rules.Remove(name)
                log_event(f"Firewall rule '{name}' deleted successfully.",0,None,True)
            except Exception as e:
                import traceback
                log_event(f"Error deleting firewall rule '{name}': {e}",2,None,True)
                traceback.print_exc()
            

    def check_for_firewall_rule(ip:str)->bool:
        
        """
        Checks if a Windows Firewall rule with the given name exists.
        If it exists returns true else returns false.
        
        Args:
            ip (str): The ip_address in the firewall rule to check for. "Artillery_Block_"
            will be prefixed on ip
        """
        name =f"Artillery_Block_{ip}"
        try:
            # Connect to the Windows Firewall with Advanced Security COM object
            net_fwall = win32comclient.Dispatch("HNetCfg.FwPolicy2")
            # Iterate through all inbound rules
            for rule in net_fwall.Rules:
                if rule.Name == name:
                    #used to get the right values for testing
                    # print(f"Firewall rule '{name}' found.")
                    # print(f"  Enabled: {rule.Enabled}")
                    # print(f"  Direction: {'Inbound' if rule.Direction == 1 else 'Outbound'}")
                    # print(f"  Action: {'Allow' if rule.Action == 1 else 'Block'}")
                    # print(f"  Local Ports: {rule.LocalPorts}")
                    # print(f"  Remote Ports: {rule.RemotePorts}")
                    # print(f"  Local Addresses: {rule.LocalAddresses}")
                    #this paticuler setting below will be used in future to create "Groups to block"
                    # print(f"  Remote Addresses: {rule.RemoteAddresses}")
                    return True
            
            log_event(f"[*]Firewall rule '{name}' not found.",0,None,True)
            return False

        except Exception as e:
            print(f"An error occurred: {e}")
            return False
    #
    def add_windows_route(ip:str)->bool:
        """
        Adds an entry to windows routing table
        """
        log_event(f"Adding {ip} to the routing table",0,None,True)
        routecmd = "route ADD %s MASK 255.255.255.255 10.255.255.255"
        subprocess.Popen(routecmd % (ip), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
    def delete_windows_route(ip:str)->bool:
        '''
        Deletes given ip from windows routing table.
        '''
        try:
            #log_event(f"[*] Trying to delete entry {ip} from routing table", 0, None, True)
            cmd = subprocess.run(['cmd', '/C', 'route', 'delete', ip], shell=True, check=True)
            return True
        except subprocess.CalledProcessError as err:
            log_event(f"[!] Error deleting route: {err}", 2, None, True)
            return False
#
class BanMgr:
    """
        Handles mgmt of banlist and firewall for windows\linux.
    will only add to file if not found, also only remove if found.
    Same thing with firewall rules.

        A new "BLOCKING_MODE" flag has been added to Artillery config.
    This flag has two values "LEGACY" and "MODERN". These flags will determine
    how to block an attacker @ runtime.

    "LEGACY" mode uses the routing table method of blocking.

    "MODERN" mode uses firewall/iptables method of blocking

    on windows "MODERN" mode will create a rule called "Artillery_Block_'ipaddress'" entries
    in firewall for offenders. on linux nothing changed its the same.
    """
    def __init__(self):
        if is_windows():
            self.pid = win32process.GetCurrentProcessId()
        if is_posix():
            self.pid = os.getpid()

        log_event(f"[*] Artillery Banmanager starting with pid of: {str(self.pid)}",0,None,True)
        pass

    def remove_ban(self):
        remove_from_firewall = False
        remove_from_banlist = False
        remove_ban = parser.parse_args()
        ban_check = settings.is_config_enabled("HONEYPOT_BAN")
        ban_classc = settings.is_config_enabled("HONEYPOT_BAN_CLASSC")
        blocking_mode = settings.get_config('current', "BLOCKING_MODE")
        #Check to see if we are even banning
        ip = remove_ban.ip_address
        if ban_check == True:
            ip = remove_ban.ip_address
            if does_line_exist(ip) == True:
                #only set to remove it if its there
                ip = remove_ban.ip_address
            if ban_classc == True:
                #set to class c only if configured
                ip = convert_to_classc(remove_ban.ip_address)
            else:
                #print("class c banning not enabled")
                pass
            #check again it might have already been convertedd
            if does_line_exist(ip) == True:
                remove_from_banlist = True
            else:
                #line is not found
                pass
                
        else:
            log_event("[*] We are not set to ban please check config.",0,None,True)
            return
        ipaddress = ip
        #print("checking firewall")
        if blocking_mode == "MODERN":
            log_event(f"[*] Running in 'MODERN' ban mode removing {ipaddress} from windows firewall",0,None,False)
            if settings.is_config_enabled('ENABLE_FIREWALL') == True:
                    #we are using firewall
                    remove_from_firewall = True
            else:
                log_event("[!] ENABLE_FIREWALL must be set to 'ON' in config",0,None,True)
                return    
        else:
            #Must be in 'LEGACY' mode
            pass         
      
        if remove_from_firewall == True:
            if is_windows():
                    # Placeholder for actual firewall removal logic
                log_event(f"[*] Attempting to remove {ipaddress} from Windows Firewall",0,None,True)
                    # Call the function to remove the rule from the firewall
                delete_firewall_rule(ipaddress)
                if remove_from_banlist == True:
                    banlist_remove_line(ipaddress)
            if is_posix():
                log_event(f"[*] Removing {ipaddress} from iptables",0,None,True)
                # remove the rule from iptables
                delete_iptables_rule(ip)
                if remove_from_banlist == True:
                    #remove fron banlist
                    banlist_remove_line(ipaddress)
        if blocking_mode == "LEGACY":
            #we are running in legacy mode add it to routing table
            log_event(f"[*] Running in 'LEGACY' ban mode adding {ipaddress} to routing table",0,None,False)
            if is_whitelisted_ip(ipaddress) == True:
                log_event(f"[*] Not banning IP {ipaddress}, whitelisted",0,None,True)
                return
            if is_windows():
                #write_windows_eventlog("Artillery", 200, win32evtlog.EVENTLOG_WARNING_TYPE, False, None,msg=None)
                #remove from the routing table
                log_event(f"[*] Attempting to remove {ipaddress} from Windows routing table",0,None,True)
                delete_windows_route(ipaddress)
                #remove it from banlist if found
                if remove_from_banlist == True:
                    log_event(f"[*] Attempting to remove {ipaddress} from banlist.txt",0,None,True)
                    banlist_remove_line(ipaddress)
                else:
                    pass
                #remove it from localbanlist if enabled
                if settings.is_config_enabled("LOCAL_BANLIST") == True:
                    log_event(f"[*] Attempting to remove {ipaddress} from localbanlist.txt",0,None,True)
                    fileflush = open(file=settings.get_config('global', "LOCAL_BANLIST"), mode="w",encoding='utf-8')
                    fileread = open(file=settings.get_config('global', "LOCAL_BANLIST"), mode="r",encoding='utf-8')
                    data = fileread.read()
                    new_file = []
                    for line in data:
                        if ipaddress == line:
                            pass
                        else:
                            new_file.append(line)
                    #clear the file
                    fileflush.flush()
                    #write out the changes minus ip
                    filewrite = open(file=settings.get_config('global', "LOCAL_BANLIST"),mode="a",encoding="utf-8")
                    for item in new_file:
                        filewrite.write(item + "\n")
                        filewrite.close()
            if is_posix():
                #remove from routing table
                delete_linux_route(ipaddress)
                #remove from banlist if there
                if remove_from_banlist == True:
                    log_event(f"[*] Removing from {ipaddress} to banlist",0,None,True)
                    banlist_remove_line(ipaddress)
                #remove from local banlist if enabled
                if settings.is_config_enabled("LOCAL_BANLIST") == True:
                    fileopen = open(file=settings.get_config('global', "LOCAL_BANLIST"), mode="r",encoding='utf-8')
                    data = fileopen.read()
                    if ip not in data:
                        filewrite = open(file=settings.get_config('global', "LOCAL_BANLIST"),mode="a",encoding="utf-8")
                        filewrite.write(ip + "\n")
                        filewrite.close()

    def add_ban(self):
        add_to_firewall = False
        add_to_banlist = False
        add_to_routing_table = False
        add_ban = parser.parse_args()
        ban_check = settings.is_config_enabled("HONEYPOT_BAN")
        ban_classc = settings.is_config_enabled("HONEYPOT_BAN_CLASSC")
        blocking_mode = settings.get_config('current', "BLOCKING_MODE")
        #if we are banning
        ip = add_ban.ip_address
        if ban_check == True:
            #check to see if ip is whitelisted
            if is_whitelisted_ip(add_ban.ip_address) == True:
                log_event(f"[*] Not banning IP {add_ban.ip_address}, whitelisted",0,None,True)
                return
            #check to see if line is not present
            if does_line_exist(add_ban.ip_address) == False:
                ip = add_ban.ip_address
            #check to see if it was added as class c already
            if ban_classc == True:
                ip = convert_to_classc(add_ban.ip_address)
            #check again it might have already been converted
            if does_line_exist(ip) == False:
                #add it its not present
                add_to_banlist = True
            else:
                #else line is present
                pass
        ipaddress = ip
        #figure out the mode we are banning in
        if blocking_mode == "MODERN":
            add_to_firewall = True
            log_event(f"[*] Running in 'MODERN' ban mode adding {ipaddress} to windows firewall",0,None,False)
            if settings.is_config_enabled('ENABLE_FIREWALL') == True:
                    #we are using firewall
                    pass
            else:
                log_event("ENABLE_FIREWALL must be set to 'ON' in config",0,None,True)
                return    
        else:
            #Must be in 'LEGACY' mode
            pass         

        if add_to_firewall == True:
            if is_windows():
                port = None
                protocol = None
                if add_ban.port:
                    port = add_ban.port
                if add_ban.protocol:
                    protocol = add_ban.protocol
                log_event(f"[*] Attempting to add {ipaddress} to Windows Firewall",0,None,True)
                add_firewall_rule(ipaddress=ipaddress,port=port,protocol=protocol)
                if add_to_banlist == True:
                    log_event(f"[*] Attempting to add {ipaddress} to banlist.txt",0,None,True)
                    banlist_add_line(ipaddress)
                else:
                    log_event(f"[*] {ipaddress} already present in banlist.txt",0,None,True)
        
            if is_posix():
                # Placeholder for actual iptables addition logic
                log_event(f"[*] Attempting to add {ipaddress} to iptables",0,None,True)
                # Call the function to add the rule to iptables
                add_iptables_rule(ipaddress=ipaddress)
                if add_to_banlist == True:
                    log_event(f"[*] Attempting to add {ipaddress} to banlist.txt",0,None,True)
                    banlist_add_line(ipaddress)
        #
        if blocking_mode == "LEGACY":
            #we are running in legacy mode add it to routing table
            log_event(f"[*] Running in 'LEGACY' ban mode adding {ipaddress} to routing table",0,None,False)
            if is_whitelisted_ip(ipaddress) == True:
                log_event(f"[*] Not banning IP {ipaddress}, whitelisted",0,None,True)
                return
            if is_windows():
                #write_windows_eventlog("Artillery", 200, win32evtlog.EVENTLOG_WARNING_TYPE, False, None,msg=None)
                #add em to the routing table
                log_event(f"[*] Attempting to add {ipaddress} to Windows routing table",0,None,True)
                add_windows_route(ipaddress)
                #add it to banlist if not found
                if add_to_banlist == True:
                    log_event(f"[*] Attempting to add {ipaddress} to banlist.txt",0,None,True)
                    banlist_add_line(ipaddress)
                else:
                    log_event(f"[*] {ipaddress} already present in banlist.txt",0,None,True)
                #add it to local banlist if enabled
                if settings.is_config_enabled("LOCAL_BANLIST") == True:
                    log_event(f"[*] Attempting to add {ipaddress} to localbanlist.txt",0,None,True)
                    fileopen = open(file=settings.get_config('global', "LOCAL_BANLIST"), mode="r",encoding='utf-8')
                    data = fileopen.read()
                    if ip not in data:
                        filewrite = open(file=settings.get_config('global', "LOCAL_BANLIST"),mode="a",encoding="utf-8")
                        filewrite.write(ip + "\n")
                        filewrite.close()
            if is_posix():
                #add to linux routing table
                add_linux_route(ipaddress)
                #add it to banlist if not there
                if add_to_banlist == True:
                        print(f"Adding {ipaddress} to banlist")
                        banlist_add_line(ipaddress)
                #add it to local banlist if enabled
                if settings.is_config_enabled("LOCAL_BANLIST") == True:
                    fileopen = open(file=settings.get_config('global', "LOCAL_BANLIST"), mode="r",encoding='utf-8')
                    data = fileopen.read()
                    if ip not in data:
                        filewrite = open(file=settings.get_config('global', "LOCAL_BANLIST"),mode="a",encoding="utf-8")
                        filewrite.write(ip + "\n")
                        filewrite.close()

if __name__ == "__main__":
    if is_windows():
        if not isUserAdmin():
            runAsAdmin()
            sys.exit(1)
        if isUserAdmin():
            pass
    if is_posix():
        try:   # and delete folder
            if os.path.isdir("/var/artillery_check_root"):
                os.rmdir('/var/artillery_check_root')
                #if not thow error and quit
        except OSError as e:
            if (e.errno == errno.EACCES or e.errno == errno.EPERM):
                log_event("You must be root to run this script!\r\n",0,None,True)
                sys.exit(1)
        #if we got this far re-create root_check folder
        if not os.path.isdir("/var/artillery_check_root"):
            os.mkdir("/var/artillery_check_root")
            #set permisions to 700
            os.chmod("/var/artillery_check_root", 0o700)
    #setup our parser to accept cmd line options.
    #for now it is basic more options wil be added over time.
    banlist = BanMgr()
    parser = argparse.ArgumentParser(prog='remove_ban',usage='%(prog)s [options] <ipadress>',description='Banlist manager for Artillery',add_help=True)
    subparser = parser.add_subparsers()
    unban_parser = subparser.add_parser(name='unban', help='removes an ip from banlist and routing table')
    unban_parser.add_argument("ip_address",action='store', help='IP address to unban')
    unban_parser.set_defaults(function=banlist.remove_ban)
    ban_parser = subparser.add_parser(name='ban', help='adds an ip to the banlist and routing table/iptables')
    ban_parser.add_argument("ip_address",action='store', help='IP address to ban')
    ban_parser.add_argument("-port",action='store', help='Specific port to block defaults to all')
    ban_parser.add_argument("-protocol",action='store', help='Protocol to use Defaults to Tcp')
    ban_parser.set_defaults(function=banlist.add_ban)
    args = parser.parse_args()    
    try:
        if hasattr(args, 'function'):
            args.function()
    except Exception as e:
        #if error print help
        log_event("[!] No valid command provided. Use 'ban', 'unban'.", 1, None, True)
        parser.print_help()
        sys.exit(1)