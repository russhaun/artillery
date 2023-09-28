'''
    Config module for configuration reading/writing/translating for Artillery. We do a read of every setting availible and store for access
for use in app elsewhere. all values grabbed from config file. if no config file exists one is created with defaults.
All values are held in memory to avoid doing reads of config file that way it is run once and we just import setting returned and use.
It generates 2 dictionaries. 1 holds current settings from config file. The other holds global system values such as app path. 
both dicts are imported to core py to be used elsewhere in app. if you plan on modifiying code to add things maybe? please import dicts from core.py not this file
direcly. this file will eventually remove globals.py and init_globals func from core.py

'''
import os
import platform
import sys
import re
import socket



CURRENT_SETTINGS = {}
GLOBAL_SETTINGS = {}


def write_console(alert) -> None:
    '''writes alerts to console window'''
    consoleenabled = CURRENT_SETTINGS.get("CONSOLE_LOGGING")
    print(consoleenabled)
    if consoleenabled == 'ON':
        alertlines = alert.split("\n")
        for alertline in alertlines:
            print("%s" % ( alertline))
    return

class global_init:
    def __init__(self) -> None:
        pass

    def set_globals(self):
        """
        Configures global system defaults that software uses based on platform
        """
        if 'win32' in sys.platform:
            programfolder = os.environ["PROGRAMFILES(x86)"]
            #print(programfolder)
            globaldefaults = GLOBAL_SETTINGS
            globaldefaults["PLATFORM"] = ["win32", ""]
            globaldefaults["APP_NAME"] = ["Artillery", ""]
            globaldefaults["APP_PATH"] = [programfolder + "\\artillery", ""]
            globalappath = self.get_value("APP_PATH")
            globaldefaults["APP_FILE"] = [globalappath + "\\artillery.exe", ""]
            globaldefaults["CONFIG_FILE"] = [globalappath + "\\config", ""]
            globaldefaults["BANLIST"] = [globalappath + "\\banlist.txt", ""]
            globaldefaults["LOCAL_BANLIST"] = [globalappath + "\\localbanlist.txt", ""]
            globaldefaults["WIN_SRC"] = [globalappath + "\\src\\windows", ""]
            winsrc = self.get_value("WIN_SRC")
            globaldefaults["EVENT_DLL"] = [winsrc + "\\ArtilleryEvents.dll", ""]
            globaldefaults["LOG_FILE"] = [globalappath + "\\logs", ""]
            log_src = self.get_value("LOG_FILE")
            globaldefaults["ALERT_LOG"] = [log_src + "\\alerts.log", ""]
            globaldefaults["PIDFILE"] = [globalappath + "\\pid.txt", ""]
            globaldefaults["BATCH_FILE"] = [globalappath + "\\artillery_start.bat", ""]
            globaldefaults["ICON_PATH"] = [globalappath + "\\src\\icons", ""]
            globaldefaults["DATABASE"] = [globalappath + "\\database\\temp.database", ""]
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
            windows_ver = platform.platform(terse=True)
            build = platform.win32_ver()
            edition = platform.win32_edition()
            GLOBAL_SETTINGS["HOST_OS"] = [f"{windows_ver} {edition}", build[1]]
            #print(f"{windows_ver} {edition} ver: {build[1]}")
        elif pf == "linux" or "darwin":
            pass


    def get_hostname(self) -> str:
        """
        returns hostname of machine
        """
        return socket.gethostname()

    def set(self):
        """
        sets up global values
        """
        self.set_globals()


class config_init:
    """
    This class is designed to configure all needed settings to handle
    creating/updating a new/existing config file to run artillery based on 
    platform with help from the class above. Once complete all 
    values are retrieved from memory during program operation in the form of a dict()
    if no config file exists one will be created. Once a config exists it will use 
    those values and update if needed with new config options
    
    """
    def __init__(self) -> None:
        # import our global class and initialize values
        global_values = global_init()
        global_values.set()
        self.default_settings = {}
        self.current_settings = {}
        self.settings_to_update = {}
        configfile = GLOBAL_SETTINGS.get("CONFIG_FILE")
        self.configpath = configfile[0]
    

    def generate_default_config(self) -> dict:
        """
        Generate sane defaults depending on platform. Returns a dict of lists
        for use in code.


         setting_header: [setting_value, setting_comment]

         Maps class dict to global dict 'CURRENT_SETTINGS' to use after this function runs.
         and to also export elsewhere in code. the goal is to do all configuration at runtime
         to eliminate issues
        """
        
        configdefaults = CURRENT_SETTINGS
        configdefaults["MONITOR"] = ["OFF", "DETERMINE IF YOU WANT TO MONITOR OR NOT"]
        #if is_posix():
         #   configdefaults["MONITOR_FOLDERS"] = ["\"/var/www\",\"/etc/\"", "THESE ARE THE FOLDERS TO MONITOR, TO ADD MORE, JUST DO \"/root\",\"/var/\", etc."]
        if 'win32' in sys.platform:
            configdefaults["MONITOR_FOLDERS"] = ["c:\\temp"", ""c:\\windows\\temp", "THESE ARE THE FOLDERS TO MONITOR, TO ADD MORE, JUST DO ""c:\\path,c:\\other\\path, etc."]
        configdefaults["MONITOR_FREQUENCY"] = ["60", "BASED ON SECONDS, 2 = 2 seconds."]
        configdefaults["SYSTEM_HARDENING"] = ["OFF", "PERFORM CERTAIN SYSTEM HARDENING CHECKS"]
        configdefaults["SSH_DEFAULT_PORT_CHECK"] = ["ON", "CHECK/WARN IF SSH IS RUNNING ON PORT 22"]
        configdefaults["EXCLUDE"] = ["", "EXCLUDE CERTAIN DIRECTORIES OR FILES. USE FOR EXAMPLE: /etc/passwd,/etc/hosts.allow"]
        configdefaults["ENABLE_HONEYPOT"] = ["OFF", "TURN ON HONEYPOT"]
        configdefaults["HONEYPOT_BAN"] = ["OFF", "DO YOU WANT TO AUTOMATICALLY BAN ON THE HONEYPOT"]
        configdefaults["HONEYPOT_BAN_CLASSC"] = ["OFF", "WHEN BANNING, DO YOU WANT TO BAN ENTIRE CLASS C AT ONCE INSTEAD OF INDIVIDUAL IP ADDRESS"]
        configdefaults["HONEYPOT_BAN_LOG_PREFIX"] = ["", "PUT A PREFIX ON ALL BANNED IP ADDRESSES. HELPFUL FOR WHEN TRYING TO PARSE OR SHOW DETECTIONS THAT YOU ARE PIPING OFF TO OTHER SYSTEMS. WHEN SET, PREFIX IPTABLES LOG ENTRIES WITH THE PROVIDED TEXT"]
        configdefaults["WHITELIST_IP"] = ["127.0.0.1,localhost", "WHITELIST IP ADDRESSES, SPECIFY BY COMMAS ON WHAT IP ADDRESSES YOU WANT TO WHITELIST"]
        configdefaults["TCPPORTS"] = ["22,1433,8080,21,5060,5061,5900,25,110,1723,1337,10000,5800,44443,16993", "TCP PORTS TO SPAWN HONEYPOT FOR"]
        configdefaults["UDPPORTS"] = ["5060,5061,3478", "UDP PORTS TO SPAWN HONEYPOT FOR"]
        configdefaults["HONEYPOT_AUTOACCEPT"] = ["ON", "SHOULD THE HONEYPOT AUTOMATICALLY ADD ACCEPT RULES TO THE ARTILLERY CHAIN FOR ANY PORTS ITS LISTENING ON"]
        configdefaults["EMAIL_ALERTS"] = ["OFF", "SHOULD EMAIL ALERTS BE SENT"]
        configdefaults["SMTP_USERNAME"] = ["", "CURRENT SUPPORT IS FOR SMTP. ENTER YOUR USERNAME AND PASSWORD HERE FOR STARTTLS AUTHENTICATION. LEAVE BLANK FOR OPEN RELAY"]
        configdefaults["SMTP_PASSWORD"] = ["", "ENTER SMTP PASSWORD HERE"]
        configdefaults["2FA_PASS"] = ["", "2-FACTOR PASSWORD GOES HERE. IF ENABLED ON YOUR EMAIL ACCT. IF NOT IT SHOULD BE. THIS ASSUMES GOOGLE EMAIL"]
        configdefaults["ENABLE_2FA"] = ["OFF", " ENABLE 2-FACTOR AUTH. MUST RETRIEVE INDIVIDUAL PASS FROM GOOGLE ACCT FOR THIS INSTANCE. "]
        configdefaults["ALERT_USER_EMAIL"] = ["enter_your_email_address_here@localhost", "THIS IS WHO TO SEND THE ALERTS TO - EMAILS WILL BE SENT FROM ARTILLERY TO THIS ADDRESS"]
        configdefaults["SMTP_FROM"] = ["Artillery_Incident@localhost", "FOR SMTP ONLY HERE, THIS IS THE MAILTO"]
        configdefaults["SMTP_ADDRESS"] = ["smtp.gmail.com", "SMTP ADDRESS FOR SENDING EMAIL, DEFAULT IS GMAIL"]
        configdefaults["SMTP_PORT"] = ["587", "SMTP PORT FOR SENDING EMAILS DEFAULT IS GMAIL WITH STARTTLS"]
        configdefaults["EMAIL_TIMER"] = ["ON", "THIS WILL SEND EMAILS OUT DURING A CERTAIN FREQUENCY. IF THIS IS SET TO OFF, ALERTS WILL BE SENT IMMEDIATELY (CAN LEAD TO A LOT OF SPAM)"]
        configdefaults["EMAIL_FREQUENCY"] = ["600", "HOW OFTEN DO YOU WANT TO SEND EMAIL ALERTS (DEFAULT 10 MINUTES) - IN SECONDS"]
        configdefaults["SSH_BRUTE_MONITOR"] = ["ON", "DO YOU WANT TO MONITOR SSH BRUTE FORCE ATTEMPTS"]
        configdefaults["SSH_BRUTE_ATTEMPTS"] = ["4", "HOW MANY ATTEMPTS BEFORE YOU BAN"]
        configdefaults["FTP_BRUTE_MONITOR"] = ["OFF", "DO YOU WANT TO MONITOR FTP BRUTE FORCE ATTEMPTS"]
        configdefaults["FTP_BRUTE_ATTEMPTS"] = ["4", "HOW MANY ATTEMPTS BEFORE YOU BAN"]
        configdefaults["AUTO_UPDATE"] = ["OFF", "DO YOU WANT TO DO AUTOMATIC UPDATES - ON OR OFF. UPDATE_LOCATION must be set on windows"]
        if 'win32' in sys.platform:
            configdefaults["UPDATE_LOCATION"] = ["path\\to\\files", "UPDATE FILES LOCATION ONLY VALID ON WINDOWS. MUST USE FULLY QUALIFIED PATH ex. c:\\path\\to\\files MUST BE READ\WRITEABLE"]
            configdefaults["UPDATE_FREQUENCY"] = ["604800", "UPDATE FREQUENCY, ONLY VALID ON WINDOWS (DEFAULT IS 7 DAYS)."]
        configdefaults["ANTI_DOS"] = ["OFF", "ANTI DOS WILL CONFIGURE MACHINE TO THROTTLE CONNECTIONS, TURN THIS OFF IF YOU DO NOT WANT TO USE"]
        configdefaults["ANTI_DOS_PORTS"] = ["80,443", "THESE ARE THE PORTS THAT WILL PROVIDE ANTI_DOS PROTECTION"]
        configdefaults["ANTI_DOS_THROTTLE_CONNECTIONS"] = ["50", "THIS WILL THROTTLE HOW MANY CONNECTIONS PER MINUTE ARE ALLOWED HOWEVER THE BUST WILL ENFORCE THIS"]
        configdefaults["ANTI_DOS_LIMIT_BURST"] = ["200", "THIS WILL ONLY ALLOW A CERTAIN BURST PER MINUTE THEN WILL ENFORCE AND NOT ALLOW ANYMORE TO CONNECT"]
        configdefaults["APACHE_MONITOR"] = ["OFF", "MONITOR LOGS ON AN APACHE SERVER"]
        configdefaults["ACCESS_LOG"] = ["/var/log/apache2/access.log", "THIS IS THE PATH FOR THE APACHE ACCESS LOG"]
        configdefaults["ERROR_LOG"] = ["/var/log/apache2/error.log", "THIS IS THE PATH FOR THE APACHE ERROR LOG"]
        configdefaults["BIND_INTERFACE"] = ["", "THIS ALLOWS YOU TO SPECIFY AN IP ADDRESS. LEAVE THIS BLANK TO BIND TO ALL INTERFACES."]
        configdefaults["THREAT_INTELLIGENCE_FEED"] = ["ON", "TURN ON INTELLIGENCE FEED, CALL TO https://www.binarydefense.com/banlist.txt IN ORDER TO GET ALREADY KNOWN MALICIOUS IP ADDRESSES. WILL PULL EVERY 24 HOURS"]
        configdefaults["THREAT_FEED"] = ["https://www.binarydefense.com/banlist.txt", "CONFIGURE THIS TO BE WHATEVER THREAT FEED YOU WANT BY DEFAULT IT WILL USE BINARY DEFENSE - NOTE YOU CAN SPECIFY MULTIPLE THREAT FEEDS BY DOING #http://urlthreatfeed1,http://urlthreadfeed2"]
        configdefaults["THREAT_SERVER"] = ["OFF", "A THREAT SERVER IS A SERVER THAT WILL COPY THE BANLIST.TXT TO A PUBLIC HTTP LOCATION TO BE PULLED BY OTHER ARTILLERY SERVER. THIS IS USED IF YOU DO NOT WANT TO USE THE STANDARD BINARY DEFENSE ONE."]
        configdefaults["THREAT_LOCATION"] = ["/var/www/", "PUBLIC LOCATION TO PULL VIA HTTP ON THE THREAT SERVER. NOTE THAT THREAT SERVER MUST BE SET TO ON"]
        configdefaults["THREAT_FILE"] = ["banlist.txt", "FILE TO COPY TO THREAT_LOCATION, TO ACT AS A THREAT_SERVER. CHANGE TO \"localbanlist.txt\" IF YOU HAVE ENABLED \"LOCAL_BANLIST\" AND WISH TO HOST YOUR LOCAL BANLIST. IF YOU WISH TO COPY BOTH FILES, SEPARATE THE FILES WITH A COMMA - f.i. \"banlist.txt,localbanlist.txt\""]
        configdefaults["LOCAL_BANLIST"] = ["OFF", "CREATE A SEPARATE LOCAL BANLIST FILE (USEFUL IF YOU'RE ALSO USING A THREAT FEED AND WANT TO HAVE A FILE THAT CONTAINS THE IPs THAT HAVE BEEN BANNED LOCALLY"]
        configdefaults["ROOT_CHECK"] = ["ON", "THIS CHECKS TO SEE WHAT PERMISSIONS ARE RUNNING AS ROOT IN A SSH SERVER DIRECTORY"]
        #if is_posix_os is True:
         #   configdefaults["SYSLOG_TYPE"] = ["LOCAL", "Specify SYSLOG TYPE to be local, file or remote. LOCAL will pipe to syslog, REMOTE will pipe to remote SYSLOG, and file will send to alerts.log in local artillery directory"]
        if 'win32' in sys.platform:
            configdefaults["SYSLOG_TYPE"] = ["FILE", "Specify SYSLOG TYPE to be local, file or remote. LOCAL will pipe to syslog, REMOTE will pipe to remote SYSLOG, and file will send to alerts.log in local artillery directory"]
        configdefaults["LOG_MESSAGE_ALERT"] = ["Artillery has detected an attack from %ip% for a connection on a honeypot port %port%", "ALERT LOG MESSAGES (You can use the following variables: %time%, %ip%, %port%)"]
        configdefaults["LOG_MESSAGE_BAN"] = ["Artillery has blocked (and blacklisted) an attack from %ip% for a connection to a honeypot restricted port %port%", "BAN LOG MESSAGES (You can use the following variables: %time%, %ip%, %port%)"]
        configdefaults["SYSLOG_REMOTE_HOST"] = ["192.168.0.1", "IF YOU SPECIFY SYSLOG TYPE TO REMOTE, SPECIFY A REMOTE SYSLOG SERVER TO SEND ALERTS TO"]
        configdefaults["SYSLOG_REMOTE_PORT"] = ["514", "IF YOU SPECIFY SYSLOG TYPE OF REMOTE, SEPCIFY A REMOTE SYSLOG PORT TO SEND ALERTS TO"]
        configdefaults["CONSOLE_LOGGING"] = ["ON", "TURN ON CONSOLE LOGGING"]
        #if is_posix():
        #    configdefaults["RECYCLE_IPS"] = ["ON", "RECYCLE banlist.txt AFTER A CERTAIN AMOUNT OF TIME - THIS WILL WIPE ALL IP ADDRESSES AND START FROM SCRATCH AFTER A CERTAIN INTERVAL"]
        if 'win32' in sys.platform:
            configdefaults["RECYCLE_IPS"] = ["OFF", "RECYCLE banlist.txt AFTER A CERTAIN AMOUNT OF TIME - THIS WILL WIPE ALL IP ADDRESSES AND START FROM SCRATCH AFTER A CERTAIN INTERVAL"]
        configdefaults["ARTILLERY_REFRESH"] = ["86370", "RECYCLE INTERVAL AFTER A CERTAIN AMOUNT OF MINUTES IT WILL OVERWRITE THE LOG WITH A BLANK ONE AND ELIMINATE THE IPS - DEFAULT IS 7 DAYS"]
        #if is_posix():
        #    configdefaults["SOURCE_FEEDS"] = ["ON", "PULL ADDITIONAL SOURCE FEEDS FOR BANNED IP LISTS FROM MULTIPLE OTHER SOURCES OTHER THAN ARTILLERY"]
        if 'win32' in sys.platform:
            configdefaults["SOURCE_FEEDS"] = ["OFF", "PULL ADDITIONAL SOURCE FEEDS FOR BANNED IP LISTS FROM MULTIPLE OTHER SOURCES OTHER THAN ARTILLERY"]

        keyorder = []
        keyorder.append("MONITOR")
        keyorder.append("MONITOR_FOLDERS")
        keyorder.append("MONITOR_FREQUENCY")
        keyorder.append("SYSTEM_HARDENING")
        keyorder.append("SSH_DEFAULT_PORT_CHECK")
        keyorder.append("EXCLUDE")
        keyorder.append("ENABLE_HONEYPOT")
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
        keyorder.append("2FA_PASS")
        keyorder.append("ENABLE_2FA")
        keyorder.append("ALERT_USER_EMAIL")
        keyorder.append("SMTP_FROM")
        keyorder.append("SMTP_ADDRESS")
        keyorder.append("SMTP_PORT")
        keyorder.append("EMAIL_TIMER")
        keyorder.append("EMAIL_FREQUENCY")
        keyorder.append("SSH_BRUTE_MONITOR")
        keyorder.append("SSH_BRUTE_ATTEMPTS")
        keyorder.append("FTP_BRUTE_MONITOR")
        keyorder.append("FTP_BRUTE_ATTEMPTS")
        keyorder.append("AUTO_UPDATE")
        if 'win32' in sys.platform:
            keyorder.append("UPDATE_LOCATION")
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
        #if the config exists check for any changes since last update
        if os.path.isfile(self.configpath):
            for configkey in configdefaults:
                #check the config file for setting header
                if self.config_exists(configkey):
                    #update our internal dict with those values
                    currentcomment = configdefaults[configkey][1]
                    currentvalue = self.read_config_file(configkey)
                    configdefaults[configkey] = [currentvalue, currentcomment]
                else:
                    #detect which keys are not present in current file and add them to a list
                    missing_keys = []
                    missing_keys.append(configkey)
                    #trigger update config flag
                    missing_values = True
                    #add all the values to our update dict
                    for item in missing_keys:
                        item = self.get_value(item)
                        comment = configdefaults[configkey][1]
                        self.settings_to_update[configkey] = [item, comment]
        else:
            #create a whole new file as no config exists
            createnew = True
            #if createnew is True:
            #generate defaults to write to new file
            for configkey in CURRENT_SETTINGS:
                currentcomment = CURRENT_SETTINGS[configkey][1]
                currentvalue = self.get_default_config(configkey)
                CURRENT_SETTINGS[configkey] = [currentvalue, currentcomment]
            #create a new file to use for settings
            self.create_default_config(self.configpath, configdefaults, keyorder)
        
        #This is to add any missing values to config file skipped if none
        if missing_values is True:
            print("there are missing values from the config file")
            self.update_existing_config()
        else:
            #pass as no conditions fired nothing to do with config
            pass

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
        confile = open(self.configpath, "a")
        with confile as update:
            #jump to end of file
            update.seek(0, os.SEEK_END)
            #add the missing values from our dict
            for key in self.settings_to_update:
                value = self.settings_to_update.get(key)
                update.write(f"\n#{value[1]}\n{key}= {value[0]}\n")

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
        pass

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
        pass

    def create_default_config(self, configpath, configdefaults, keyorder):
        """
        Writes out a default config if none present
        """
        '''builds out config file with some sane defaults
        according to platform and writes it to a file'''
        
        confile = open(configpath, "w")
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
                #current = f" comment: {config_values[1]} variable: {key} setting: {config_values[0]}"
                #print(current)
                newline_comment = f"\n#{config_values[1]}\n"
                newline_config = f"{key}= {config_values[0]}\n"
                #newline_config = "%s=\"%s\"\n" % (configkey, configdefaults[configkey][0])
                confile.write(newline_comment)
                confile.write(newline_config)
            except KeyError as e:
                print(f"keys not added: {e}")
                
        confile.close()
        print(f"[*] Config file created @ {self.configpath}")
        return

