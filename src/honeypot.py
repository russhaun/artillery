#!/usr/bin/python
#
# this is the honeypot stuff and by no means finished . there are some things that need to be cleaned up and refined.
# this will morph and change over time as I work in features, including packet capture, whois,
# geo-ip info of attacker as well as custom responses based on server port and type:))))
###################################################################################################
from .core import sys,socket,time,os,random,datetime,traceback,threading,SocketServer,_socket,log_event,is_posix,is_windows,is_whitelisted_ip,is_already_banned,is_valid_ipv4,does_line_exist,settings
from .email_handler import *
__appname__ = "Honeypot Server"
__vesion__ = "1.0"
__author__ = ""
__requires__ = []
__description__ = "Fake server to accept requests from unsolicited sources and ban or report accordingly\nSupports Tcp\\Udp,ipv4\\ipv6(experimental)"


honeypot_email_logger = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())
#this is the delay on how often email handler will check the trigger file
delay_timer = settings.get_config('current','EMAIL_FREQUENCY')
#these are for the compiled version with systray app installed
#not applicable to raw py version(yet) so leaving it here
SYSTRAY_ENABLED = False
SYSTRAY_MSG_ACTVE = False
ALERTS_PENDING = False
#hardcoded for now
systray_port = 10080
systray_msg =""
#to prevent spamming msgs with an ongoing scan
#change to config option
systray_throttle = 90
#ports accessed on server
TOUCHED_PORTS = []
#ip seen by server
KNOWN_IPS = []
#ips banned by server
BANNED_IPS = []





class TCP6Server((SocketServer.ThreadingTCPServer)):
    """
    defines a basic tcp6 server with threading
    """
    address_family = socket.AF_INET6
    request_queue_size = 50
    max_packet_size = 4096
    timeout = 10

    def handle_error(self, request, client_address) -> None:
        return super().handle_error(request, client_address)

class TCP4Server((SocketServer.ThreadingTCPServer)):
    """
    defines a basic tcp4 server with threading
    """
    address_family = socket.AF_INET
    request_queue_size = 50
    max_packet_size = 8192
    timeout = 30
    atkaddr = ''
    atkport = ''
    
    def handle_error(self, request, client_address):
        log_event(f"client {client_address} had an error {str(request)}",2,None,True)
    
    def get_request(self):
        """
        Handles one request. if valid ip and not banned or on whitelist
        sets up a thread to handle the request
        """
        #setup our connection
        connection, address = self.socket.accept()
        #ip and responding port
        ip, resport = str(address[0]), str(address[1])
        #actual port open on server
        srv_port = self.server_address[1]
        #used to set per function values for logging/banning
        self.atkaddr = str(ip)
        self.atkport = str(srv_port)
        #this will make sense in a min
        self.reason = ""
        #only continue if valid ip
        if is_valid_ipv4(ip):
            #and not on whitelist
            if not is_whitelisted_ip(ip):
                #or already banned
                if not is_already_banned(ip):
                    self.reason = "UNKNOWN"
                else:
                    #these all will be passed down at some point as reason. potential spam are where they are at now with logging
                    log_event(f"[!] Connection from a banned ip: {ip} on tcp port: {srv_port}",1,None,True)
                    self.reason = "BANNED"
            else:
                log_event(f"[!] Connection from a whitelisted  ip: {ip} on tcp port: {srv_port}",1,None,True)
                self.reason = "WHITELISTED"
        #should never hit this
        else:
            log_event(f"[!] Connection from an invalid ip: {ip} on tcp port: {srv_port}",1,None,True)
            self.reason = "INVALID IP"
            #
        self.receive_request(self.reason,connection,self.atkaddr,self.atkport)


    
    def receive_request(self,reason,connection,ip,port):
        """Creates client thread"""
        while True:
            connection, address = self.socket.accept()
            #ip and responding port
            ip, resport = str(address[0]), str(address[1])
            try:
                threading.Thread(target=self.client_thread, args=(connection, ip, port,reason)).start()
            except:
                log_event("[*] Thread did not start.",0,None,False)
                traceback.print_exc()


    def client_thread(self,connection, ip, port,reason):
        """
        do all work here with connected client
        """
        #client data returned to view or whatever
        client_input = self.receive_input(connection, 8192)
        #only add port/ip if not already there and log the event buh bye dups
        #the reason will be used here for logging working on mechanics to make msg
        if port not in TOUCHED_PORTS:
            TOUCHED_PORTS.append(port)
            log_event(f"[!] Attack detected from address: {ip} on tcp port: {port}",1,None,True)
        if ip not in KNOWN_IPS:
            KNOWN_IPS.append(str(ip))

        #print(reason,flush=True)
        #from here we can respond accordingly
        #we have all the data we need to act how we want
        #have to build in the logic for "faking" a response
        #based on what we are server/port #.
        #the reason we pass will also have an effect on logic
        #this will turn into the trigger for Answeringmachine code eventually
        #send em garbage for now until the logic is built(old style)
        try:
            
            self.send_response(connection, self.atkaddr)
        except ConnectionError as e:
            traceback.print_exc()
        #check to see if an alert has already been set
        global SYSTRAY_MSG_ACTVE
        if SYSTRAY_MSG_ACTVE == True:
           #just pass
            pass
        else:
            global systray_msg
            #set our msg for systray
            msg = self.create_alert()
            systray_msg = msg[0]
            SYSTRAY_MSG_ACTVE = True
            #this name no longer applies willl be changed 
            self.bancheck(ip)

    
    def receive_input(self,connection, max_buffer_size)->str:
        """
        attempts to prevent overflows of created buffer for now it just alerts
        """
        try:
            client_input = connection.recv(max_buffer_size)
            client_input_size = sys.getsizeof(client_input)
        except ConnectionResetError as err:
            print('[*] Connection was lost:', err,flush=True)

        if client_input_size > max_buffer_size:
            print("[*] The input size is greater than expected {}".format(client_input_size),flush=True)
            #possible starting place for throttling maybe?
            #or is  it better to do amount of connections/requests per sec/min?
        
        decoded_input = client_input.rstrip() #strip end of line
        
        result = self.process_input(decoded_input,connection)

        return result


    def process_input(self,input_str,connection):
        """
        Cleanup data received, send our response
        and kick off logging and ban facilities
        """
       
        #if its blank just pass
        if input_str == None:
            return str("No Data")
        else:
            #else return it to do stuff with 
            return str(input_str)

    def send_response(self, connection,raddr):
        """
        sends garbage back to connected client.
        TO_DO: add random delay to response to 
        just make them wait for a min. :))

        """
        try:
            connection.send(self.gen_response())
        except ConnectionAbortedError as err:
            log_event("connection was aborted",2,evtid=None,console=False)
    
    def gen_response(self):
        '''
        generates a fake string and returns it. eventually this will be the tied
        into answeringmachine code
        '''
        length = random.randint(5, 30000)
        fake_string = os.urandom(int(length))
        return fake_string
    
    def create_alert(self):
        '''
        generates alert and returns alertmsg,ip,port for logging/processing
        '''
        
        nrvars = ''
        now = str(datetime.datetime.today())
        port = str(self.atkport)
        alert = ""
        message = settings.get_config("current","LOG_MESSAGE_ALERT")
        if settings.is_config_enabled("HONEYPOT_BAN") == True:
            message = settings.get_config("current", "LOG_MESSAGE_BAN")
        message = message.replace("%time%", now)
        message = message.replace("%ip%", self.atkaddr)
        message = message.replace("%port%", str(port))
        alert = message
        if "%" in message:
            nrvars = message.count("%")
        if nrvars == 1:
            alert = message % (now)
        elif nrvars == 2:
            alert = message % (now, self.atkaddr)
        elif nrvars == 3:
            alert = message % (now, self.atkaddr, str(port))
        return alert,self.atkaddr,port
    
    def bancheck(self,ip):
        '''
        appends ip to banlist trigger lists
        '''
        #add to banned ip list if we are set to ban
        if settings.is_config_enabled("HONEYPOT_BAN") == True:
            BANNED_IPS.append(str(ip))
        #dont think this should stay here not the right place
        global ALERTS_PENDING
        #if alerts are pending just pass
        if ALERTS_PENDING == True:
            pass
        else:
            ALERTS_PENDING = True

class TCPSocket((SocketServer.BaseRequestHandler)):
    '''creates a blank tcp socket. all actions take place on TCP4Server'''
    


class UDP6Server((SocketServer.ThreadingUDPServer)):
    """
    defines a basic udp6 server with threading
    """
    address_family = socket.AF_INET6
    socket_type = socket.SOCK_DGRAM
    request_queue_size = 10

    def handle_error(self, request, client_address):
        log_event(f"client {client_address} had an error {str(request)}",1,None,True)

    def close_request(self, request: _socket | tuple[bytes, _socket]) -> None:
        return super().close_request(request)
    
    def handle_request(self) -> None:
        return super().handle_request()


class UDP4Server((SocketServer.ThreadingUDPServer)):
    """
    defines a basic udp4 server with threading
    """
    address_family = socket.AF_INET
    socket_type = socket.SOCK_DGRAM

    def handle_error(self, request, client_address):
        log_event(f"client {client_address} had an error {str(request)}",1,None,True)

    request_queue_size = 10

class UDPSocket((SocketServer.BaseRequestHandler)):
    '''creates a udp socket. all methods run in order setup(1), handle(2), finish(3).
    '''

    def handle(self):
        '''takes data from attacker and does stuff. Then jumps to finish function'''
        #take info and do more stuff
        data = self.request[0].strip()
        skt = self.request[1]
        #write_console(f"Data recieved: {str(data)}")
        skt.sendto(self.fake_string ,self.client_address)

    def setup(self):
        '''checks to see if ip is valid and not on whitelist.
        Gets some initial info about attacker and alerts
        on connection then jumps to handle function'''
        #random number between 5 and 30,000 then os.urandom the command back
        self.random_length_number = random.randint(5, 30000)
        self.fake_string = os.urandom(int(self.random_length_number))

        ip = str(self.client_address[0])
        #only continue if is valid ip
        if is_valid_ipv4(ip):
            if not is_whitelisted_ip(ip):
                if not is_already_banned(ip):
                    srv_port = str(self.server.server_address[1])
                    log_event(f"[!] Attack detected from address: {ip} on udp port: {srv_port}",1,None,True)

    def finish(self):
        '''Maybe get even more stuff and then
        get that mofo outta here and perform cleanup'''

        pass



def open_sesame(porttype, port):
    """
    adds entries to iptables for posix platform
    """
    if settings.is_config_enabled("HONEYPOT_AUTOACCEPT") == True:
        if is_posix():
            cmd = "iptables -D ARTILLERY -p %s --dport %s -j ACCEPT -w 3" % (porttype, port)
            execOScmd(cmd)
            cmd = "iptables -A ARTILLERY -p %s --dport %s -j ACCEPT -w 3" % (porttype, port)
            execOScmd(cmd)
            log_event(f"Created iptables rule to accept incoming connection to {porttype} {port}",0,None,False)
        if is_windows():
            pass

##TO_DO add support for ip6
def check_open_port(port, port_type, bind_interface):
    '''attempts to see if ports are open on local host.
        retuns True if open. False if closed '''
    if port_type == "TCP":
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if port_type == "UDP":
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
    result = False
    try:
        sock.bind((bind_interface, int(port)))
        result = True
    except socket.error as e:
        log_event(f"{port_type} port: {port} creation failed with: {str(e)}. Please check the config file and make sure the port is not in use",2,None,False)
        result = False

    sock.close()
    return result


def listentcp_server(tcpport, bind_interface):
    '''Creates a basic TCP server based on TCP4Server and TCPSocket classes'''
    if not tcpport == "":
        port = int(tcpport)
        #this will bind to all ips. localhost/0.0./and lan
        if bind_interface == "":
            server = TCP4Server(('', port), TCPSocket)
        else:
            #this will only bind to given ip from config file
            server = TCP4Server((bind_interface, port), TCPSocket)
        open_sesame("tcp", port)
        server.serve_forever()


def listenudp_server(udpport, bind_interface):
    '''Creates a basic UDP server based on UDP4Server and UDPSocket classes'''
    if not udpport == "":
        port = int(udpport)
        #this will bind to all ips. localhost/0.0./and lan
        if bind_interface == "":
            server = UDP4Server(('', port), UDPSocket)
        else:
            #this will only bind to given ip from config file
            server = UDP4Server((bind_interface, port), UDPSocket)
        open_sesame("udp", port)
        server.serve_forever()


def main(tcpports, udpports, bind_interface):
    """
        main function that creates all servers from classes above.
        checks to see if ports are availible if not skips and
        sends alert/email after gathering all info/exceptions
        if ports were not used from config file.
    """
    open_tcp = []
    open_udp = []
    closed_tcp = []
    closed_udp = []
    tports = tcpports.split(",")
    for tport in tports:
        tport = tport.replace(" ", "")
        #if the ports not blank
        if tport != "":
            #check to see if port is in use
            port_availible = check_open_port(tport, "TCP", bind_interface)
            if port_availible is True:
                open_tcp.append(tport)
                time.sleep(.5)
                threading.Thread(group=None,target=listentcp_server,args=(tport, bind_interface),daemon=True).start()
            else:
                closed_tcp.append(tport)
    #
    # split into tuple
    uports = udpports.split(",")
    for uport in uports:
        uport = uport.replace(" ", "")
        if uport != "":
            #check to see if port is in use
            port_availible = check_open_port(uport, "UDP", bind_interface)
            if port_availible is True:
                open_udp.append(uport)
                time.sleep(.5)
                threading.Thread(group=None,target=listenudp_server,args=(uport, bind_interface),daemon=True).start()
            else:
                closed_udp.append(uport)
    #
    #check to see if some ports were open/closed
    # during startup and report if so
    tcp_bind_success = False
    udp_bind_success = False
    tcp_bind_error = False
    udp_bind_error = False
    failed_tcp = 0
    failed_udp = 0
    success_tcp = 0
    success_udp = 0
    #if there are entries
    if len(open_udp) > 0:
        #set to true
        udp_bind_success = True
        #add num of ports to list
        success_udp += len(open_udp)
    if len(open_tcp) > 0:
        #set to true
        tcp_bind_success = True
        #add num of ports to list
        success_tcp += len(open_tcp)
    if len(closed_udp) > 0:
        #set error to true
        udp_bind_error = True
        #add num of ports to list
        failed_udp += len(closed_udp)
    if len(closed_tcp) > 0:
        tcp_bind_error = True
        failed_tcp += len(closed_tcp)
    #check if bind_error is set to true and set up msg for alert
    if tcp_bind_error or udp_bind_error is True:
        subject = " Artillery error - Unable to bind to some ports"
        if tcp_bind_error and udp_bind_error is True:
            bind_error = f"Artillery was unable to bind to {str(failed_tcp)} TCP port/ports: {str(closed_tcp)}.{str(failed_udp)} UDP port/ports: {str(closed_udp)} This could be due to an active port in use."
        if tcp_bind_error is True and udp_bind_error is False:
            bind_error = f"Artillery was unable to bind to {str(failed_tcp)} TCP port/ports: {str(closed_tcp)}. This could be due to an active port in use."
        if tcp_bind_error is False and udp_bind_error is True:
            bind_error = f"Artillery was unable to bind to {str(failed_udp)} UDP port/ports: {str(closed_udp)} This could be due to an active port in use."
        log_event(f"{bind_error}", 2,None,False)
        #call email from here
        #this will only produce 1 msg at runtime to send yay!!!
    if tcp_bind_success or udp_bind_success is True:
        subject = "Set up listener on some ports"
        if tcp_bind_success and udp_bind_success is True:
            message = f"{subject} Opened {str(success_tcp)} TCP ports and {str(success_udp)} UDP Ports"
        if tcp_bind_success is True and udp_bind_success is False:
            message = f"{subject} Opened {str(success_tcp)} TCP ports."
        if tcp_bind_success is False and udp_bind_success is True:
            message = f"{subject} Opened {str(success_udp)} UDP Ports."
        log_event(f"{message}", 0,None,False)
        log_event(f"TCP ports: {str(open_tcp)}", 0,None,False)
        log_event(f"UDP ports: {str(open_udp)}", 0,None,False)

def check_for_alerts():
    """
    starts a thread to check for active alerts.
    if true processes alerts and sends msg's to 
    appropriate sources
    """
    while 1:
        #sleep for throttle period 
        time.sleep(systray_throttle)
        #create all of our copies of data we want
        ports = set(TOUCHED_PORTS)
        ips = set(KNOWN_IPS)
        bans = set(BANNED_IPS)
        global ALERTS_PENDING
        if ALERTS_PENDING == False:
            pass
        else:
            #do work we have an alert
            global systray_msg
            msg = systray_msg
            #set our values for email if enabled
            honeypot_email_ip = KNOWN_IPS[0]
            honeypot_email_port = TOUCHED_PORTS[0]
            systray_msg = ''
            #if email alerts are turned on
            if settings.is_config_enabled('EMAIL_ALERTS') == True:
                #write email trigger has its own timer
                trigger_src = settings.get_config('global','LOG_FILE')
                trigger_file = f"{trigger_src}\\junk\\hptrigger.txt"
                with open(trigger_file,"w",encoding='utf-8') as trigger:
                    trigger.write(f"{str(honeypot_email_ip)},{str(honeypot_email_port)}"+"\n")
            #only check systray on windows for now
            global SYSTRAY_ENABLED
            if is_windows():
                if SYSTRAY_ENABLED == False:
                    pass
                else:
                    systray_alert(1,msg)
            #do any other logging here
            #maybe ban here as well?
            #if we are not set to ban this will be 0
            if len(BANNED_IPS) == 0:
                pass
            else:
                #we are set to ban get the info we need and ban
                for item in BANNED_IPS:
                    #check to see if the line is already there
                    lineexists = does_line_exist(item)
                    if lineexists == True:
                        #print(f"ip {item} is already present",flush=True)
                        pass
                    else:
                        #ban from here this solves the dupe issue(windows)
                        #will probably use banlist_add_line() function
                        #as it has a check for if the line is present
                        #and re-work this section
                        ban(item)
                #
            #
            #when were finished set ALERTS_PENDING to False
            global SYSTRAY_MSG_ACTVE
            SYSTRAY_MSG_ACTVE = False
            ALERTS_PENDING = False
            #clear all of our original values to 
            # take it all out of memmory
            KNOWN_IPS.clear()
            BANNED_IPS.clear()
            TOUCHED_PORTS.clear()
            #log_event(f"touched ports value: {TOUCHED_PORTS}",0,None,True)
        


        


def start_honeypot():
    """
    starts main honeypot fuction
    """
    #write_console("[*] Starting honeypot.")
    if settings.is_config_enabled("ENABLE_HONEYPOT") == True:
        log_event(f"[*] Starting {__appname__} v{__vesion__}.", 0, None,console=True)
        threading.Thread(target=main,args=(settings.get_config("current","TCPPORTS"),settings.get_config("current","UDPPORTS"),settings.get_config("current","BIND_INTERFACE"))).start()
        threading.Thread(target=check_for_alerts,args=()).start()
        if settings.is_config_enabled('EMAIL_ALERTS') == True:
            honeypot_email_logger.set_trigger_file('hptrigger.txt')
            threading.Thread(honeypot_email_logger.check_pending_msgs, ()).start()

start_honeypot()