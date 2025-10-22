'''
    Config module for configuration reading/writing/translating for Artillery. We do a read of every setting availible and store for access
for use in app elsewhere. all values grabbed from config file. if no config file exists one is created with defaults.
All values are held in memory to avoid doing reads of config file that way it is run once and we just import setting returned and use.
It generates 2 dictionaries. 1 holds current settings from config file. The other holds global system values such as app path. 
both dicts are imported to core py to be used elsewhere in app.
direcly.

'''
import os
import platform
import sys
import re
import socket
import time
import datetime

#WARNING turning this on of puts out a lot of info
#only use to see if values are being set properly
DEBUG = False
def grab_config_time() -> str:
    '''grabs current time and returns it in %Y-%m-%d %H:%M:%S format'''
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
#   Create log file as soon as possible independent of system
# as we dont have acces to the function yet in core.py
# but this can be pulled in to init.py
# and then be imported in core.py and be used elsewhere:)
def write_configuration_log(line:str, console:bool):
        """Creates a log file specifically for config generation in logs dir. """
        if 'win' in sys.platform:
            PROGRAM_FILES = os.environ["PROGRAMFILES(X86)"]
        if ('linux' or 'linux2' or 'darwin') in sys.platform:
            PROGRAM_FILES ="/var"
        LOG_FILE = os.path.join(PROGRAM_FILES, "artillery","logs","configuration.log")
        if not os.path.isfile(LOG_FILE):
            with open(file=LOG_FILE,mode='x',encoding='utf-8') as log:
                if console is True:
                    print(f"{grab_config_time()}: [*] {line}")
                log.write("************Artillery configuration log************"+"\n")
                log.write(f"{grab_config_time()}: [*] {line}\n")
        else:
            with open(file=LOG_FILE,mode='a',encoding='utf-8') as log:
                if console is True:
                    print(f"{grab_config_time()}: [*] {line}")
                log.write(f"{grab_config_time()}: [*] {line}\n")
    #

CURRENT_SETTINGS = {}
GLOBAL_SETTINGS = {}
ENABLED_SERVICES = {}
DISABLED_SERVICES = {}
AVAILIBLE_SERVICES = {}
CONFIGURATION_SETTINGS = {}





class ConfigMgr:
    """
    Used to retrive values from dictionaries generated during startup

    ex:

        from .config import Config_MGR\n
        #retrieve a setting for apppath from global dict\n
        apppath = settings.get_config(global,"APP_PATH")\n
        #retrieve a setting from config dict\n
        alertemail = settings.get(current, "ALERT_USER_EMAIL")\n
    """
    def __init__(self) -> None:
        write_configuration_log("Starting Config mgr",False)
        # self.current = CURRENT_SETTINGS
        # self.globals = GLOBAL_SETTINGS
        #self.get_enabled_services()
        pass

    
    def is_config_enabled(self,value):
            '''
            Checks CURRENT_SETTINGS dict to see if 
            the desired value is on or off
            returns True if on and False if off
            '''
            data = CURRENT_SETTINGS.get(value)[0]
            if data == "ON":
                return True
            else:
                return False
    #
    def get_config(self, setting, value):
        '''
        returns config value from global dicts
        CURRENT_SETTINGS and GLOBAL_SETTINGS.
        '''
        if setting == "current":
            data = CURRENT_SETTINGS.get(value)[0]
        elif setting == "global":
            data = GLOBAL_SETTINGS.get(value)[0]
        return data
    
    def get_enabled_services(self):
        """
        reads current service settings and appends to enabled_services/disabled_services
        if value is on/off.
        """
        for x, y in CURRENT_SETTINGS.items():
            # If the value is ON or OFF
            #get everything
            AVAILIBLE_SERVICES[x]=[y[0]]
            #add it to our dicts accordingly
            if y[0] == 'ON':
                ENABLED_SERVICES[x]=[y[0]]
            elif y[0] == 'OFF':
                DISABLED_SERVICES[x]=[y[0]]
                #AVAILIBLE_SERVICES[x]=[y[0],""]
            # add all config settings such as "LOG_MESSAGE_ALERT" value
            else:  
                CONFIGURATION_SETTINGS[x]=[y[0]]
        # return it all and let god sort em out
        return AVAILIBLE_SERVICES,ENABLED_SERVICES,DISABLED_SERVICES,CONFIGURATION_SETTINGS

class global_init:
    def __init__(self) -> None:
        if DEBUG is True:
            write_configuration_log("Global check starting",True)
        else:
            write_configuration_log("Global check starting",False)


    def set_globals(self):
        """
        Configures global system defaults that software uses based on platform
        """
        if 'win32' in sys.platform:
            if DEBUG is True:
                write_configuration_log("Window detected setting appropriate values",True)
            else:
                write_configuration_log("Window detected setting appropriate values",False)
            programfolder = os.environ["PROGRAMFILES(x86)"]
            globaldefaults = GLOBAL_SETTINGS
            globaldefaults["PLATFORM"] = ["win32",""]
            globaldefaults["APP_NAME"] = ["Artillery", ""]
            globaldefaults["APP_PATH"] = [os.path.join(programfolder, "artillery"), ""]
            globalappath = self.get_value("APP_PATH")
            globaldefaults["APP_FILE"] = [os.path.join(globalappath, "artillery.py"), ""]
            globaldefaults["CONFIG_FILE"] = [os.path.join(globalappath, "config"), ""]
            globaldefaults["BANLIST"] = [os.path.join(globalappath, "banlist.txt"), ""]
            globaldefaults["LOCAL_BANLIST"] = [os.path.join(globalappath, "localbanlist.txt"), ""]
            globaldefaults["WIN_SRC"] = [os.path.join(globalappath, "src", "windows"), ""]
            winsrc = self.get_value("WIN_SRC")
            globaldefaults["EVENT_DLL"] = [os.path.join(winsrc, "ArtilleryEvents.dll"), ""]
            globaldefaults["LOG_FILE"] = [os.path.join(globalappath, "logs"), ""]
            log_src = self.get_value("LOG_FILE")
            globaldefaults["ALERT_LOG"] = [os.path.join(log_src, "alerts.log"), ""]
            globaldefaults["EMAIL_ALERTS_TRIGGER"] = [os.path.join(log_src, "junk", "email_trigger.log"), ""]
            globaldefaults["EMAIL_ALERTS_LOG"] = [os.path.join(log_src, "email_log.log"), ""]
            globaldefaults["EXCEPTION_LOG"] = [os.path.join(log_src, "exceptions.log"), ""]
            globaldefaults["RUNTIME_LOG"] = [os.path.join(log_src, "runtime.log"), ""]
            globaldefaults["PIDFILE"] = [os.path.join(globalappath, "pid.txt"), ""]
            globaldefaults["BATCH_FILE"] = [os.path.join(globalappath, "artillery_start.bat"), ""]
            globaldefaults["ICON_PATH"] = [os.path.join(globalappath, "src", "icons"), ""]
            globaldefaults["DATABASE"] = [os.path.join(globalappath, "database", "temp.database"), ""]
            hostname = self.get_hostname()
            globaldefaults["HOSTNAME"] = [hostname]
            getplatform = self.get_value("PLATFORM")
            self.get_host_OS(getplatform)
        if ('linux' or 'linux2' or 'darwin') in sys.platform:
            programfolder = "/var"
            globaldefaults = GLOBAL_SETTINGS
            globaldefaults["PLATFORM"] = ["posix", ""]
            globaldefaults["APP_NAME"] = ["Artillery", ""]
            globaldefaults["APP_PATH"] = [os.path.join(programfolder, "artillery"), ""]
            globalappath = self.get_value("APP_PATH")
            globaldefaults["APP_FILE"] = [os.path.join(globalappath, "artillery.py"), ""]
            globaldefaults["CONFIG_FILE"] = [os.path.join(globalappath, "config"), ""]
            globaldefaults["BANLIST"] = [os.path.join(globalappath, "banlist.txt"), ""]
            globaldefaults["LOCAL_BANLIST"] = [os.path.join(globalappath, "localbanlist.txt"), ""]
            globaldefaults["LOG_FILE"] = [os.path.join(globalappath, "logs"), ""]
            log_src = self.get_value("LOG_FILE")
            globaldefaults["ALERT_LOG"] = [os.path.join(log_src, "alerts.log"), ""]
            globaldefaults["EMAIL_ALERTS_TRIGGER"] = [os.path.join(log_src, "junk", "email_trigger.log"), ""]
            globaldefaults["EMAIL_ALERTS_LOG"] = [os.path.join(log_src, "email_log.log"), ""]
            globaldefaults["EXCEPTION_LOG"] = [os.path.join(log_src, "exceptions.log"), ""]
            globaldefaults["RUNTIME_LOG"] = [os.path.join(log_src, "runtime.log"), ""]
            globaldefaults["ICON_PATH"] = [os.path.join(globalappath, "src", "icons"), ""]
            globaldefaults["DATABASE"] = [os.path.join(globalappath, "database", "temp.database"), ""]
            hostname = self.get_hostname()
            globaldefaults["HOSTNAME"] = [hostname]
            getplatform = self.get_value("PLATFORM")
            self.get_host_OS(getplatform)

    def get_value(self, config):
        """
        returns a value from global config
        """
        value = GLOBAL_SETTINGS.get(config)
        return value[0]

    def get_host_OS(self, pf):
        """
        set host os values in GLOBAL_SETTINGS  dict
        """
        if pf == "win32":
            ver = platform.platform(terse=True)
            build = platform.win32_ver()
            edition = platform.win32_edition()
            if DEBUG is True:
                write_configuration_log(f"Running: {ver} {edition} {build[1]}")
            GLOBAL_SETTINGS["HOST_OS"] = [f"{ver} {edition}", build[1]]
        elif pf == "posix":
            ver = ""
            build = ""
            edition = ""
            #GLOBAL_SETTINGS["HOST_OS"] = [f"{ver} {edition}", build[1]]
            pass
            


    def get_hostname(self) -> str:
        """
        returns hostname of machine
        """
        if DEBUG is True:
            name = socket.gethostname()
            write_configuration_log(f"returned hostname: {name}")
        return socket.gethostname()

    def set(self):
        """
        sets up global values
        """
        self.set_globals()


class config_init:
    """
    This class is designed to configure all needed settings to handle
    creating/updating a new/existing config file to run Artillery based on 
    platform with help from the class above. Once complete all 
    values are retrieved from memory during program operation in the form of a dict()
    if no config file exists one will be created. Once a config exists it will use 
    those values and update if needed with new config options
    
    """
    def __init__(self) -> None:
        # import our global class and initialize values
        if DEBUG is True:
            write_configuration_log("Configuration check starting",True)
            write_configuration_log("Getting log default values",False)
        else:
            write_configuration_log("Configuration check starting",False)
            
        global_values = global_init()
        global_values.set()
        self.default_settings = {}
        self.current_settings = {}
        self.settings_to_update = {}
        configfile = GLOBAL_SETTINGS.get("CONFIG_FILE")[0]
        self.configpath = configfile
        banlist = GLOBAL_SETTINGS.get("BANLIST")[0]
        self.banlist = banlist
        localbanlist = GLOBAL_SETTINGS.get("LOCAL_BANLIST")[0]
        self.localbanlist = localbanlist
        alertlog = GLOBAL_SETTINGS.get("ALERT_LOG")[0]
        self.alertlog = alertlog
        runtimelog = GLOBAL_SETTINGS.get("RUNTIME_LOG")[0]
        self.runtimelog = runtimelog
        exceptionlog = GLOBAL_SETTINGS.get("EXCEPTION_LOG")[0]
        self.exceptionlog = exceptionlog
        database = GLOBAL_SETTINGS.get("DATABASE")[0]
        self.database = database
        if DEBUG is True:
            write_configuration_log("Done generating default values",True)
        #generate all of the files needed for operation
        #create config/banlist with header only here for first runs so it is always present
        #this will do away with most checks to see if a file exists in project 
        if not os.path.isfile(self.configpath):
            if DEBUG is True:
                write_configuration_log("Creating config file",True)
            else:
                write_configuration_log("Creating config file",False)
            banner = "#############################################################################################\n"
            banner += "#\n"
            banner += "# This is the Artillery configuration file. Change these variables and flags to change how\n"
            banner += "# this behaves.\n"
            banner += "#\n"
            banner += "# Artillery written by: Dave Kennedy (ReL1K)\n"
            banner += "# Website: https://www.binarydefense.com\n"
            banner += "# Email: info [at] binarydefense.com\n"
            banner += "# Download: git clone https://github.com/binarydefense/artillery artillery/\n"
            banner += "# Install: python setup.py\n"
            banner += "#\n"
            banner += "#############################################################################################\n"
            banner += "#\n"
            with open(file=self.configpath,mode='x',encoding='utf-8') as config:
                config.write(banner)
        #same thing with the banlist
        if not os.path.isfile(self.banlist):
            if DEBUG is True:
                write_configuration_log("Creating banlist",True)
            else:
                write_configuration_log("Creating banlist",False)
            banner = "#\n"
            banner +="#\n"
            banner +="# Binary Defense Systems Artillery Threat Intelligence Feed and Banlist Feed\n"
            banner +="# https://www.binarydefense.com\n"
            banner +="#\n"
            banner +="# Note that this is for public use only.\n"
            banner +="# The ATIF feed may not be used for commercial resale or in products that are charging fees for such services.\n"
            banner +="# Use of these feeds for commerical (having others pay for a service) use is strictly prohibited.\n"
            banner +="#\n"
            banner +="#\n"
            banner +="#\n"
            with open(file=self.banlist,mode='x',encoding='utf-8') as banfile:
                banfile.write(banner)
        #and localbanlist
        if not os.path.isfile(self.localbanlist):
            if DEBUG is True:
                write_configuration_log("Creating localbanlist",True)
            else:
                write_configuration_log("Creating localbanlist",False)
            with open(file=self.localbanlist,mode='x',encoding='utf-8') as localbanfile:
                localbanfile.write("********** local banlist **********"+ "\n")
        #create all logfiles as well
        #alerts.log ##handles alerts from modules
        #runtime.log ##handles alerts from startup/shutdown or other operational info
        #exceptions.log ## Handles exceptons where they are caught ex: try/except blocks
        #temp.database ## holds hashes of files used with monitoring 
        if not os.path.isfile(self.alertlog):
            if DEBUG is True:
                write_configuration_log("Creating alerts.log",True)
            else:
                write_configuration_log("Creating alerts.log",False)
            with open(file=self.alertlog,mode='x',encoding='utf-8') as alertfile:
                alertfile.write("********** Alerts Log **********"+ "\n")
        if not os.path.isfile(self.runtimelog):
            if DEBUG is True:
                write_configuration_log("Creating runtime.log",True)
            else:
                write_configuration_log("Creating runtime.log",False)
            with open(file=self.runtimelog,mode='x',encoding='utf-8') as runtimefile:
                runtimefile.write("********** Runtime logs **********"+ "\n")
        if not os.path.isfile(self.exceptionlog):
            if DEBUG is True:
                write_configuration_log("Creating exceptions.log",True)
            else:
                write_configuration_log("Creating exceptions.log",False)
            with open(file=self.exceptionlog,mode='x',encoding='utf-8') as exceptionfile:
                exceptionfile.write("********** Exceptions logs **********"+ "\n")
        if not os.path.isfile(self.database):
            if DEBUG is True:
                write_configuration_log("Creating database file",True)
            else:
                write_configuration_log("Creating database file",False)
            with open(file=self.database,mode='x',encoding='utf-8') as databasefile:
                databasefile.write("")

    def check_config(self) -> dict:
        """
        Generate sane defaults depending on platform. Returns a dict of lists
        for use in code.


         setting_header: [setting_value, setting_comment]

         Maps class dict to global dict 'CURRENT_SETTINGS' to use after this function runs.
         and to also export elsewhere in code. the goal is to do all configuration at runtime
         to eliminate issues
        """
        #
        if DEBUG is True:
            write_configuration_log("Generating default settings",True)
        configdefaults = CURRENT_SETTINGS
        configdefaults["MONITOR"] = ["OFF", "DETERMINE IF YOU WANT TO MONITOR OR NOT"]
        if ('linux' or 'linux2' or 'darwin') in sys.platform:
            configdefaults["MONITOR_FOLDERS"] = ["\"/var/www\",\"/etc/\"", "THESE ARE THE FOLDERS TO MONITOR, TO ADD MORE, JUST DO \"/root\",\"/var/\", etc."]
        if 'win32' in sys.platform:
            tempdir = os.environ["TEMP"]
            configdefaults["MONITOR_FOLDERS"] = [f"{tempdir}", "THESE ARE THE FOLDERS TO MONITOR, TO ADD MORE, JUST DO ""c:\\path,c:\\other\\path, etc."]
        configdefaults["MONITOR_FREQUENCY"] = ["60", "BASED ON SECONDS, 2 = 2 seconds."]
        configdefaults["SYSTEM_HARDENING"] = ["OFF", "PERFORM CERTAIN SYSTEM HARDENING CHECKS"]
        configdefaults["ENABLE_FIREWALL"] = ["OFF","ALLOWS CREATING/DELETING WINDOWS FIREWALL RULES. DISABLES ROUTING TABLE METHOD(Experimental)"]
        configdefaults["SSH_DEFAULT_PORT_CHECK"] = ["OFF", "CHECK/WARN IF SSH IS RUNNING ON PORT 22"]
        configdefaults["EXCLUDE"] = ["", "EXCLUDE CERTAIN DIRECTORIES OR FILES. USE FOR EXAMPLE: /etc/passwd,/etc/hosts.allow"]
        configdefaults["ENABLE_HONEYPOT"] = ["OFF", "TURN ON HONEYPOT"]
        configdefaults["BLOCKING_MODE"] = ["LEGACY", "METHOD TO USE WHEN BANNING OFFENDERS.ACCEPTS 'LEGACY' OR 'MODERN' WHICH MAPS TO ROUTINGTABLE\\FIREWALL RESPECTIVELY"]
        configdefaults["HONEYPOT_BAN"] = ["ON", "DO YOU WANT TO AUTOMATICALLY BAN ON THE HONEYPOT"]
        configdefaults["HONEYPOT_BAN_CLASSC"] = ["OFF", "WHEN BANNING, DO YOU WANT TO BAN ENTIRE CLASS C AT ONCE INSTEAD OF INDIVIDUAL IP ADDRESS"]
        configdefaults["HONEYPOT_BAN_LOG_PREFIX"] = ["", "PUT A PREFIX ON ALL BANNED IP ADDRESSES. HELPFUL FOR WHEN TRYING TO PARSE OR SHOW DETECTIONS THAT YOU ARE PIPING OFF TO OTHER SYSTEMS. WHEN SET, PREFIX IPTABLES LOG ENTRIES WITH THE PROVIDED TEXT"]
        configdefaults["WHITELIST_IP"] = ["127.0.0.1,localhost", "WHITELIST IP ADDRESSES, SPECIFY BY COMMAS ON WHAT IP ADDRESSES YOU WANT TO WHITELIST"]
        configdefaults["TCPPORTS"] = ["22,1433,8080,21,5060,5061,5900,25,110,1723,1337,10000,5800,44443,16993", "TCP PORTS TO SPAWN HONEYPOT FOR"]
        configdefaults["UDPPORTS"] = ["5060,5061,3478", "UDP PORTS TO SPAWN HONEYPOT FOR"]
        configdefaults["HONEYPOT_AUTOACCEPT"] = ["OFF", "SHOULD THE HONEYPOT AUTOMATICALLY ADD ACCEPT RULES TO THE ARTILLERY CHAIN FOR ANY PORTS ITS LISTENING ON"]
        configdefaults["EMAIL_ALERTS"] = ["OFF", "SHOULD EMAIL ALERTS BE SENT"]
        configdefaults["SMTP_USERNAME"] = ["", "CURRENT SUPPORT IS FOR SMTP. ENTER YOUR USERNAME AND PASSWORD HERE FOR STARTTLS AUTHENTICATION. LEAVE BLANK FOR OPEN RELAY"]
        configdefaults["SMTP_PASSWORD"] = ["", "ENTER SMTP PASSWORD HERE"]
        configdefaults["ALERT_USER_EMAIL"] = ["enter_your_email_address_here@localhost", "THIS IS WHO TO SEND THE ALERTS TO - EMAILS WILL BE SENT FROM ARTILLERY TO THIS ADDRESS"]
        configdefaults["SMTP_FROM"] = ["Artillery_Incident@localhost", "FOR SMTP ONLY HERE, THIS IS THE MAILTO"]
        configdefaults["SMTP_ADDRESS"] = ["your.smtp.server.com", "SMTP ADDRESS FOR SENDING EMAIL, "]
        configdefaults["SMTP_PORT"] = ["587", "SMTP PORT FOR SENDING EMAILS DEFAULT IS WITH STARTTLS"]
        configdefaults["EMAIL_TIMER"] = ["ON", "THIS WILL SEND EMAILS OUT DURING A CERTAIN FREQUENCY. IF THIS IS SET TO OFF, ALERTS WILL BE SENT IMMEDIATELY (CAN LEAD TO A LOT OF SPAM)"]
        configdefaults["EMAIL_FREQUENCY"] = ["600", "HOW OFTEN DO YOU WANT TO SEND EMAIL ALERTS (DEFAULT 10 MIN) - IN SECONDS"]
        configdefaults["SSH_MONITOR_FREQUENCY"] = ["600", "HOW OFTEN TO CHECK BRUTFORCE ATTEMPTS (DEFAULT 10 MIN)"]
        configdefaults["SSH_BRUTE_MONITOR"] = ["OFF", "DO YOU WANT TO MONITOR SSH BRUTE FORCE ATTEMPTS"]
        configdefaults["SSH_BRUTE_ATTEMPTS"] = ["4", "HOW MANY ATTEMPTS BEFORE YOU BAN"]
        configdefaults["FTP_MONITOR_FREQUENCY"] = ["600", "HOW OFTEN TO CHECK BRUTFORCE ATTEMPTS (DEFAULT 10 MIN)"]
        configdefaults["FTP_BRUTE_MONITOR"] = ["OFF", "DO YOU WANT TO MONITOR FTP BRUTE FORCE ATTEMPTS"]
        configdefaults["FTP_BRUTE_ATTEMPTS"] = ["4", "HOW MANY ATTEMPTS BEFORE YOU BAN"]
        configdefaults["AUTO_UPDATE"] = ["OFF", "DO YOU WANT TO DO AUTOMATIC UPDATES - ON OR OFF."]
        if 'win32' in sys.platform:
            configdefaults["UPDATE_FREQUENCY"] = ["604800", "UPDATE FREQUENCY, ONLY VALID ON WINDOWS (DEFAULT IS 7 DAYS)."]
        configdefaults["ANTI_DOS"] = ["OFF", "ANTI DOS WILL CONFIGURE MACHINE TO THROTTLE CONNECTIONS, TURN THIS OFF IF YOU DO NOT WANT TO USE"]
        configdefaults["ANTI_DOS_PORTS"] = ["80,443", "THESE ARE THE PORTS THAT WILL PROVIDE ANTI_DOS PROTECTION"]
        configdefaults["ANTI_DOS_THROTTLE_CONNECTIONS"] = ["50", "THIS WILL THROTTLE HOW MANY CONNECTIONS PER MINUTE ARE ALLOWED HOWEVER THE BUST WILL ENFORCE THIS"]
        configdefaults["ANTI_DOS_LIMIT_BURST"] = ["200", "THIS WILL ONLY ALLOW A CERTAIN BURST PER MINUTE THEN WILL ENFORCE AND NOT ALLOW ANYMORE TO CONNECT"]
        configdefaults["APACHE_MONITOR"] = ["OFF", "MONITOR LOGS ON AN APACHE SERVER"]
        configdefaults["ACCESS_LOG"] = ["/var/log/apache2/access.log", "THIS IS THE PATH FOR THE APACHE ACCESS LOG"]
        configdefaults["ERROR_LOG"] = ["/var/log/apache2/error.log", "THIS IS THE PATH FOR THE APACHE ERROR LOG"]
        if 'win32' in sys.platform:
            configdefaults["BIND_INTERFACE"] = ["127.0.0.1", "THIS ALLOWS YOU TO SPECIFY AN IP ADDRESS FOR THE HONEYPOT."]
        if ('linux' or 'linux2' or 'darwin') in sys.platform:
            configdefaults["BIND_INTERFACE"] = ["", "THIS ALLOWS YOU TO SPECIFY AN IP ADDRESS FOR THE HONEYPOT."]
        configdefaults["THREAT_INTELLIGENCE_FEED"] = ["OFF", "TURN ON INTELLIGENCE FEED, CALL TO https://www.binarydefense.com/banlist.txt IN ORDER TO GET ALREADY KNOWN MALICIOUS IP ADDRESSES. WILL PULL EVERY 24 HOURS"]
        configdefaults["THREAT_FEED"] = ["https://www.binarydefense.com/banlist.txt", "CONFIGURE THIS TO BE WHATEVER THREAT FEED YOU WANT BY DEFAULT IT WILL USE BINARY DEFENSE - NOTE YOU CAN SPECIFY MULTIPLE THREAT FEEDS BY DOING #http://urlthreatfeed1,http://urlthreadfeed2"]
        configdefaults["THREAT_SERVER"] = ["OFF", "A THREAT SERVER IS A SERVER THAT WILL COPY THE BANLIST.TXT TO A PUBLIC HTTP LOCATION TO BE PULLED BY OTHER ARTILLERY SERVER. THIS IS USED IF YOU DO NOT WANT TO USE THE STANDARD BINARY DEFENSE ONE."]
        configdefaults["THREAT_LOCATION"] = ["/var/www/", "PUBLIC LOCATION TO PULL VIA HTTP ON THE THREAT SERVER. NOTE THAT THREAT SERVER MUST BE SET TO ON"]
        configdefaults["THREAT_FILE"] = ["banlist.txt", "FILE TO COPY TO THREAT_LOCATION, TO ACT AS A THREAT_SERVER. CHANGE TO \"localbanlist.txt\" IF YOU HAVE ENABLED \"LOCAL_BANLIST\" AND WISH TO HOST YOUR LOCAL BANLIST. IF YOU WISH TO COPY BOTH FILES, SEPARATE THE FILES WITH A COMMA - f.i. \"banlist.txt,localbanlist.txt\""]
        configdefaults["LOCAL_BANLIST"] = ["OFF", "CREATE A SEPARATE LOCAL BANLIST FILE USEFUL IF YOURE ALSO USING A THREAT FEED AND WANT TO HAVE A FILE THAT CONTAINS THE IPs THAT HAVE BEEN BANNED LOCALLY"]
        configdefaults["ROOT_CHECK"] = ["OFF", "THIS CHECKS TO SEE WHAT PERMISSIONS ARE RUNNING AS ROOT IN A SSH SERVER DIRECTORY"]
        if 'win32' in sys.platform:
            configdefaults["SYSLOG_TYPE"] = ["FILE", "Specify SYSLOG TYPE to be local, file or remote. LOCAL will pipe to syslog, REMOTE will pipe to remote SYSLOG, and file will send to alerts.log in local artillery directory"]
        if ('linux' or 'linux2' or 'darwin') in sys.platform:
            configdefaults["SYSLOG_TYPE"] = ["LOCAL", "Specify SYSLOG TYPE to be local, file or remote. LOCAL will pipe to syslog, REMOTE will pipe to remote SYSLOG, and file will send to alerts.log in local artillery directory"]
        configdefaults["LOG_MESSAGE_ALERT"] = ["Artillery has detected an attack from %ip% for a connection on a honeypot port %port%", "ALERT LOG MESSAGES (You can use the following variables: %time%, %ip%, %port%)"]
        configdefaults["LOG_MESSAGE_BAN"] = ["Artillery has blocked (and blacklisted) an attack from %ip% for a connection to a honeypot restricted port %port%", "BAN LOG MESSAGES (You can use the following variables: %time%, %ip%, %port%)"]
        configdefaults["SYSLOG_REMOTE_HOST"] = ["192.168.0.1", "IF YOU SPECIFY SYSLOG TYPE TO REMOTE, SPECIFY A REMOTE SYSLOG SERVER TO SEND ALERTS TO"]
        configdefaults["SYSLOG_REMOTE_PORT"] = ["514", "IF YOU SPECIFY SYSLOG TYPE OF REMOTE, SEPCIFY A REMOTE SYSLOG PORT TO SEND ALERTS TO"]
        configdefaults["CONSOLE_LOGGING"] = ["ON", "TURN ON CONSOLE LOGGING"]
        configdefaults["RECYCLE_IPS"] = ["OFF", "RECYCLE banlist.txt AFTER A CERTAIN AMOUNT OF TIME - THIS WILL WIPE ALL IP ADDRESSES AND START FROM SCRATCH AFTER A CERTAIN INTERVAL"]
        configdefaults["ARTILLERY_REFRESH"] = ["86370", "RECYCLE INTERVAL AFTER A CERTAIN AMOUNT OF MINUTES IT WILL OVERWRITE THE LOG WITH A BLANK ONE AND ELIMINATE THE IPS - DEFAULT IS 7 DAYS"]
        configdefaults["SOURCE_FEEDS"] = ["ON", "PULL ADDITIONAL SOURCE FEEDS FOR BANNED IP LISTS FROM MULTIPLE OTHER SOURCES OTHER THAN ARTILLERY"]
        if DEBUG is True:
            write_configuration_log("Done creating defaults",True)
        keyorder = []
        keyorder.append("MONITOR")
        keyorder.append("MONITOR_FOLDERS")
        keyorder.append("MONITOR_FREQUENCY")
        keyorder.append("SYSTEM_HARDENING")
        keyorder.append("ENABLE_FIREWALL")
        keyorder.append("SSH_DEFAULT_PORT_CHECK")
        keyorder.append("EXCLUDE")
        keyorder.append("ENABLE_HONEYPOT")
        keyorder.append("BLOCKING_MODE")
        keyorder.append("HONEYPOT_BAN")
        keyorder.append("HONEYPOT_BAN_CLASSC")
        keyorder.append("HONEYPOT_BAN_LOG_PREFIX")
        keyorder.append("WHITELIST_IP")
        keyorder.append("TCPPORTS")
        keyorder.append("UDPPORTS")
        keyorder.append("HONEYPOT_AUTOACCEPT")
        keyorder.append("EMAIL_ALERTS")
        keyorder.append("SMTP_USERNAME")
        keyorder.append("SMTP_PASSWORD")
        keyorder.append("ALERT_USER_EMAIL")
        keyorder.append("SMTP_FROM")
        keyorder.append("SMTP_ADDRESS")
        keyorder.append("SMTP_PORT")
        keyorder.append("EMAIL_TIMER")
        keyorder.append("EMAIL_FREQUENCY")
        keyorder.append("SSH_MONITOR_FREQUENCY")
        keyorder.append("SSH_BRUTE_MONITOR")
        keyorder.append("SSH_BRUTE_ATTEMPTS")
        keyorder.append("FTP_BRUTE_MONITOR")
        keyorder.append("FTP_BRUTE_ATTEMPTS")
        keyorder.append("AUTO_UPDATE")
        if 'win32' in sys.platform:
            keyorder.append("UPDATE_FREQUENCY")
        keyorder.append("ANTI_DOS")
        keyorder.append("ANTI_DOS_PORTS")
        keyorder.append("ANTI_DOS_THROTTLE_CONNECTIONS")
        keyorder.append("ANTI_DOS_LIMIT_BURST")
        keyorder.append("APACHE_MONITOR")
        keyorder.append("ACCESS_LOG")
        keyorder.append("ERROR_LOG")
        keyorder.append("BIND_INTERFACE")
        keyorder.append("THREAT_INTELLIGENCE_FEED")
        keyorder.append("THREAT_FEED")
        keyorder.append("THREAT_SERVER")
        keyorder.append("THREAT_LOCATION")
        keyorder.append("THREAT_FILE")
        keyorder.append("LOCAL_BANLIST")
        keyorder.append("ROOT_CHECK")
        keyorder.append("SYSLOG_TYPE")
        keyorder.append("LOG_MESSAGE_ALERT")
        keyorder.append("LOG_MESSAGE_BAN")
        keyorder.append("SYSLOG_REMOTE_HOST")
        keyorder.append("SYSLOG_REMOTE_PORT")
        keyorder.append("CONSOLE_LOGGING")
        keyorder.append("RECYCLE_IPS")
        keyorder.append("ARTILLERY_REFRESH")
        keyorder.append("SOURCE_FEEDS")
        for key in configdefaults:
            if key not in keyorder:
                keyorder.append(key)
        #check for missing values in existing config flag
        #check for existence of config file flag
        missing_values = False
        createnew = False
        #if the config exists check for any changes since last run
        #and add the item to our internal dict
        
        if os.path.isfile(self.configpath):
            if DEBUG is True:
                write_configuration_log("Checking config file",True)
            for configkey in configdefaults:
                #check the config file for setting header
                if self.config_exists(configkey):
                    if DEBUG is True:
                        write_configuration_log(f"{configkey} found in config updating it",True)
                    #update our internal dict with those values
                    currentcomment = configdefaults[configkey][1]
                    currentvalue = self.read_config_file(configkey)
                    configdefaults[configkey] = [currentvalue, currentcomment]
                else:
                    #detect which keys are not present in current file and add them to a list
                    #this will be everything on first run
                    if DEBUG is True:
                        write_configuration_log(f"{configkey} not found in config prepping to add",True)
                    missing_keys = []
                    missing_keys.append(configkey)
                    #trigger update config flag
                    missing_values = True
                    #add all the values to our update dict
                    if DEBUG is True:
                        write_configuration_log(f"Adding {configkey} to config",True)
                    for item in missing_keys:
                        item = self.get_value(item)
                        comment = configdefaults[configkey][1]
                        self.settings_to_update[configkey] = [item, comment]
        else:
            #this wil be removed as its not accessed anymore
            #because i create the file above always if not found
            #create a whole new file as no config exists
            #generate defaults to write to new file
            for configkey in CURRENT_SETTINGS:
                currentcomment = CURRENT_SETTINGS[configkey][1]
                currentvalue = self.get_default_config(configkey)
                CURRENT_SETTINGS[configkey] = [currentvalue, currentcomment]
            #create a new file to use for settings
            self.create_default_config(self.configpath, configdefaults, keyorder)
        #this replaces above code as file is created with just a header in class init
        #on first run this is what populates config file even though its blank at this point
        #as far as artillery itself is concerned this file is always present no need to check for a config file
        #it will use the values from internal dict to start
        if missing_values is True:
            self.update_existing_config()
        
        #Base Dictionary has been created/updated for global use

    def get_value(self, config):
        """
        returns a value from global config
        """
        value = CURRENT_SETTINGS.get(config)
        return value[0]

    def get_default_config(self, config):
        """
        grabs value from master dictionary to use when creating a brand new config file
        """
        value = CURRENT_SETTINGS.get(config)
        return value

    def update_existing_config(self):
        """
        updates existing config file if changes are detected
        """
        if DEBUG is True:
            write_configuration_log(f"updating existing config",True)
        confile = open(self.configpath, "a")
        with confile as update:
            #jump to end of file
            update.seek(0, os.SEEK_END)
            #add the missing values from our dict
            for key in self.settings_to_update:
                value = self.settings_to_update.get(key)
                if DEBUG is True:
                    setting = f"{key}={value[0]}"
                    write_configuration_log(f"Adding {setting} to the config file",True)
                update.write(f"\n#{value[1]}\n{key}=\"{value[0]}\"\n")

    def read_config_file(self, setting):
        """
        Checks for config setting in config file
        returns value
        """
        fileopen = open(self.configpath, "r")
        for line in fileopen:
            if not line.startswith("#"):
                match = re.search(setting + "=", line)
                if match:
                    line = line.rstrip()
                    line = line.replace('"', "")
                    line = line.split("=")
                    return line[1]

    def config_exists(self, setting):
        """
        Checks for existence of config setting in config file
        returns True or False

        """
        fileopen = open(self.configpath, "r")
        paramfound = False
        for line in fileopen:
            if not line.startswith("#"):
                match = re.search(setting + "=", line)
                if match:
                    paramfound = True
        return paramfound
        #pass
        #this code is never reached as all files are generated way earlier
        #in init method will be removed in future
    def create_default_config(self, configpath, configdefaults, keyorder):
        """
        Writes out a default config if none present. 
        This function will be removed as it's no longer accessed
        """
        
        confile = open(file=configpath, mode="w")
        banner = "#############################################################################################\n"
        banner += "#\n"
        banner += "# This is the Artillery configuration file. Change these variables and flags to change how\n"
        banner += "# this behaves.\n"
        banner += "#\n"
        banner += "# Artillery written by: Dave Kennedy (ReL1K)\n"
        banner += "# Website: https://www.binarydefense.com\n"
        banner += "# Email: info [at] binarydefense.com\n"
        banner += "# Download: git clone https://github.com/binarydefense/artillery artillery/\n"
        banner += "# Install: python setup.py\n"
        banner += "#\n"
        banner += "#############################################################################################\n"
        banner += "#\n"
        confile.write(banner)
        for configkey in keyorder:
            try:
                comment_values = CURRENT_SETTINGS.get(configkey)
                config_values = comment_values[0]
                key = configkey
                setting = f"\n#{config_values[1]}\n{key}=\"{config_values[0]}\"\n"
                confile.write(setting)
            except KeyError as e:
                print(f"keys not added: {e}",flush=True)
               
        confile.close()
        print(f"[*] Config file created @ {self.configpath}",flush=True)
        
#load all config options availible to software
core_config = config_init()
core_config.check_config()
