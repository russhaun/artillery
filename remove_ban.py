##removeban.py responsible for Adding/removing entries to artillery banlist/routingtable/firewall/iptables
# this will be modified more as features are included in project
###############################################################
if __name__ == "__main__":
    import argparse
    import sys, os
    if 'win' in sys.platform:
        import ctypes
        def is_admin():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()    
            except:
                return False
        if is_admin() == False:
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)  
            sys.exit()
        else:
            #only import if admin
            from src.core import *
    #
    elif ('linux' or 'linux2' or 'darwin') in sys.platform:
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
            sys.exit()
        else:
            #print("The current user is root.")
            from src.core import *
    #########################################################
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
            #this is for when launching as standard user on windows it will fail here
            #because this is not imported as regular user i catch it so you don't see it
            #its meaningless
            try:
                if is_windows():
                    self.pid = win32process.GetCurrentProcessId()
            except NameError:
                sys.exit()
            if is_posix():
                self.pid = os.getpid()
            log_event(f"[*] Artillery Banmanager starting with pid of: {str(self.pid)}",0,None,True)
        #
        def pause_console(self):
            """
            Pauses console strategically used mostly because of when launched as a standard user
            """
            pause = input("[*] Press return to continue")
        #
        def add_route(self,destination:str, gateway=None, dev=None):
            """
                Adds ip address to routing table

                Args:
                    destination (str): The destination network or host (e.g., '192.168.1.0/24' or '10.0.0.1').
                    gateway (str, optional): The gateway IP address. Required for deleting a route via a specific gateway.
                    dev (str, optional): The network interface associated with the route.
            """
            if is_windows():
                log_event(f"Adding {destination} to the routing table",0,None,True)
                routecmd = "route ADD %s MASK 255.255.255.255 10.255.255.255"
                subprocess.Popen(routecmd % (destination), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            if is_posix():
                success = False
                command = ["ip", "route", "add", f"{destination}"]       
                if gateway:
                    command.extend(['via', gateway])
                if dev:
                    command.extend(['dev', dev])
                try:
                    subprocess.run(command, check=True)
                    print(f"Route to {destination} successfully added.")
                    success = True
                except subprocess.CalledProcessError as e:
                    print(f"Error deleting route: {e}")
                    print(f"Stdout: {e.stdout}")
                    print(f"Stderr: {e.stderr}")
                return success
        #
        def delete_route(self,destination:str, gateway=None, dev=None):
            """
                Deletes a route from the routing table.

                Args:
                    destination (str): The destination network or host (e.g., '192.168.1.0/24' or '10.0.0.1').
                    gateway (str, optional): The gateway IP address. Required for deleting a route via a specific gateway.
                    dev (str, optional): The network interface associated with the route.
            """
            if is_windows():
                try:
                    #log_event(f"[*] Trying to delete entry {ip} from routing table", 0, None, True)
                    cmd = subprocess.run(['cmd', '/C', 'route', 'delete', destination], shell=True, check=True)
                    return True
                except subprocess.CalledProcessError as err:
                    log_event(f"[!] Error deleting route: {err}", 2, None, True)
                    return False
            if is_posix():
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
        #
        def add_firewall_rule(self,ipaddress:str, port=str|None, protocol=str|None):
            """
                Adds a Windows Firewall/Linux Iptables rule by its ipaddress.

                Args:
                    ipaddress (str): The name of the firewall rule to add.
                    port (int, optional): The port number to apply the rule to. Defaults to None.
                    protocol (str, optional): The protocol to apply the rule to. Can be 'TCP" or 'UDP'. Defaults to None.
            """
            args = parser.parse_args()
            print(args)
            if is_windows():
                name = self.prep_firewall_rule_name(ipaddress=ipaddress)
                #check for the rule first
                exists = self.check_firewall_rule(ip=ipaddress)
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
                    log_event(f"[!] Error adding firewall rule '{new_rule.Name}': {e}",1,None,True)
                    traceback.print_exc()
            if is_posix():
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
        def delete_firewall_rule(self,ipaddress:str):
            """
                Deletes a Windows Firewall/Linux Iptables rule by its ipaddress if not already there.

                Args:
                    ipaddr (str): The ip in the firewall to delete.
            """
            if is_windows():
                doesexist = self.check_firewall_rule(ip=ipaddress)
                if doesexist is False:
                    #just return
                    return
                else:
                    name =f"Artillery_Block_{ipaddress}"
                    try:
                        net_fw_policy2 = win32comclient.Dispatch("HNetCfg.FwPolicy2")
                        net_fw_policy2.Rules.Remove(name)
                        log_event(f"[*] Firewall rule '{name}' deleted successfully.",0,None,True)
                    except Exception as e:
                        import traceback
                        log_event(f"[*] Error deleting firewall rule '{name}': {e}",2,None,True)
                        traceback.print_exc()
            if is_posix():
                ip = ipaddress.strip()
                #only continue if valid ip
                is_valid = is_valid_ip(ip)
                if is_valid == False:
                    #just return and give a warning
                    log_event(f"[*] Provided ip: {ip} is not valid please check the address",0,None,True)
                    return
                else: 
                    exists = self.check_firewall_rule(ip)
                    if exists == False:
                        log_event(f"[*] Rule for {ip} not present nothing to do",0,None,True)
                        return
                    else:
                        log_event(f"[*] Deleting entry {ip} from iptables chain", 0, None, True)
                            # delete entry from iptables chain
                        subprocess.Popen("iptables -D ARTILLERY %s" % (ip), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        #      
        def check_firewall_rule(self,ip:str)->bool:
            """
                Checks if a Firewall/Iptables rule with the given name exists.
                If it exists returns true else returns false.
                
                Args:
                    ip (str): The ip_address in the firewall rule to check for. 
                    On windows platforms "Artillery_Block_"
                    will be prefixed on ip
            """
            if is_windows():
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
            if is_posix():
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

        def prep_firewall_rule_name(self,ipaddress:str)->str:
            """
                returns a firewall rulename by appending a prefix to the ip_address.
                passed in at runtime only used on windows platforms (for now)

                Args:
                    ip (str): The IP address to be used in the rule name.
            """
            if is_windows():
                if ipaddress is not None:
                    rule_prefix = "Artillery_Block_"
                    return f"{rule_prefix}{ipaddress}"
                else:
                    raise ValueError("IP address cannot be empty.")
            if is_posix():
                pass

        def remove_ban(self):
            """
            Handles checks and functions to remove artillery bans
            depending on config
            """
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
                self.pause_console()
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
                    self.pause_console()
                    return    
            else:
                #Must be in 'LEGACY' mode
                pass         
        
            if remove_from_firewall == True:
                if is_windows():
                        # Placeholder for actual firewall removal logic
                    log_event(f"[*] Attempting to remove {ipaddress} from Windows Firewall",0,None,True)
                        # Call the function to remove the rule from the firewall
                    self.delete_firewall_rule(ipaddress)
                    if remove_from_banlist == True:
                        banlist_remove_line(ipaddress)
                    self.pause_console()
                if is_posix():
                    log_event(f"[*] Removing {ipaddress} from iptables",0,None,True)
                    # remove the rule from iptables
                    self.delete_firewall_rule(ip)
                    if remove_from_banlist == True:
                        #remove fron banlist
                        banlist_remove_line(ipaddress)
            if blocking_mode == "LEGACY":
                #we are running in legacy mode add it to routing table
                log_event(f"[*] Running in 'LEGACY' ban mode adding {ipaddress} to routing table",0,None,False)
                if is_whitelisted_ip(ipaddress) == True:
                    log_event(f"[*] Not banning IP {ipaddress}, whitelisted",0,None,True)
                    self.pause_console()
                    return
                if is_windows():
                    #write_windows_eventlog("Artillery", 200, win32evtlog.EVENTLOG_WARNING_TYPE, False, None,msg=None)
                    #remove from the routing table
                    log_event(f"[*] Attempting to remove {ipaddress} from Windows routing table",0,None,True)
                    self.delete_route(destination=ipaddress)
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
                    #removeban complete
                    self.pause_console()
                if is_posix():
                    #remove from routing table
                    self.delete_route(ipaddress)
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
            """
            Handles checks and functions to add artillery bans
            depending on config
            """
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
                if is_whitelisted_ip(ip) == True:
                    log_event(f"[*] Not banning IP {ip}, whitelisted",0,None,True)
                    self.pause_console()
                    return
                #check to see if line is not present
                if does_line_exist(ip) == False:
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
                    self.pause_console()
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
                    self.add_firewall_rule(ipaddress=ipaddress,port=port,protocol=protocol)
                    if add_to_banlist == True:
                        log_event(f"[*] Attempting to add {ipaddress} to banlist.txt",0,None,True)
                        banlist_add_line(ipaddress)
                    else:
                        log_event(f"[*] {ipaddress} already present in banlist.txt",0,None,True)
                    self.pause_console()
            
                if is_posix():
                    # Placeholder for actual iptables addition logic
                    log_event(f"[*] Attempting to add {ipaddress} to iptables",0,None,True)
                    # Call the function to add the rule to iptables
                    self.add_firewall_rule(ipaddress=ipaddress,port=port,protocol=protocol)
                    if add_to_banlist == True:
                        log_event(f"[*] Attempting to add {ipaddress} to banlist.txt",0,None,True)
                        banlist_add_line(ipaddress)
            #
            if blocking_mode == "LEGACY":
                #we are running in legacy mode add it to routing table
                log_event(f"[*] Running in 'LEGACY' ban mode adding {ipaddress} to routing table",0,None,False)
                if is_whitelisted_ip(ipaddress) == True:
                    log_event(f"[*] Not banning IP {ipaddress}, whitelisted",0,None,True)
                    self.pause_console()
                    return
                if is_windows():
                    #write_windows_eventlog("Artillery", 200, win32evtlog.EVENTLOG_WARNING_TYPE, False, None,msg=None)
                    #add em to the routing table
                    log_event(f"[*] Attempting to add {ipaddress} to Windows routing table",0,None,True)
                    self.add_route(ipaddress,None,None)
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
                    # add ban complete
                    self.pause_console()
                if is_posix():
                    #add to linux routing table
                    self.add_route(ipaddress,None,None)
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