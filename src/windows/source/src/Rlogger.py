import datetime
import logging
import os
import sys
import time
import socket
from enum import Enum, auto                                            #this will be removed
from logging.handlers import SMTPHandler,SysLogHandler,SYSLOG_TCP_PORT,NTEventLogHandler
#
from dataclasses import dataclass,asdict
WINDOWS_EVENTS_ENABLED = False

#create some enums to handle colors if availible
class Color(Enum):
    RED = 31
    GREEN = auto()
    YELLOW = auto()
    BLUE = auto()
    MAGENTA = auto()
    CYAN = auto()
    LIGHTRED = 91
    LIGHTGREEN = auto()
    LIGHTYELLOW = auto()
    LIGHTBLUE = auto()
    LIGHTMAGENTA = auto()
    LIGHTCYAN = auto()

    _START = '\u001b['
    _BOLD = ';1'
    _BLINK = ';5'
    _END = 'm'
    _RESET = '\u001b[0m'

    @staticmethod
    def colored(color, msg, bold=False, blink=False):
        if not(isinstance(color, Color)):
            raise TypeError(f'Unknown color {color}')

        fmt_msg = Color._START.value + str(color.value)

        if bold:
            fmt_msg += Color._BOLD.value
        if blink:
            fmt_msg += Color._BLINK.value

        return fmt_msg + Color._END.value + str(msg) + Color._RESET.value


#define our class for logging
class Custom_Logger(logging.getLoggerClass()):
    """This class is responsible for logging with artillery system wide. it utilizses multiple class to 
        handle the various methods for proper logging. @ Creation it takes a list of dicts to establish what
        needs to be configured and how it should handle events. after this step it exposes a log_event() function to
        be used in the code.
            
        :param name: name for the logger
        :param log_dir: str:  the directory for the log files
        :param config: list[dict]: a list of dicts containing settings for logging options
    """
    #
    def __init__(self,name:str,log_dir:str, config:list[dict,dict,dict,dict,dict]):
        
        # Create custom logger logging all five levels
        self.name = str(name).upper()
        self.write_config_log(f"setting up logger for {self.name}",False)
        super().__init__(self.name)
        self.setLevel(logging.DEBUG)
        #this makes us the root logger
        self.propagate = False
        #setup all our config values
        self.logdir = log_dir
        #file writes will be handled within log_event() method similiar to what happens in core.py
        # the evtlvl value determines what file it goes to as of now file logs always happen flag later maybe?
        # five values
        self.file_config = config[0]
        # three values
        self.syslog_config = config[1]
        # eleven values
        self.smtp_config = config[2]
        # one value
        self.console_config = config[3]
        # unknown yet (not enabled)
        self.winevent_config = config[4]
        #do checks to see what we need to setup
        #Determine console settings
        self.console = self.console_config.get("enabled")
        if self.console == True:
            self.write_config_log("console logging enabled",False)
            # Create stream handler for logging to stdout (log all five levels)
            # self.stdout_handler = logging.StreamHandler(sys.stdout)
            # self.stdout_handler.setLevel(logging.DEBUG)
            # self.stdout_handler.setFormatter(logging.Formatter('%(message)s'))
            # self.enable_console_output()
        else:
            self.write_config_log("console logging disabled",False)
        self.file = self.file_config.get("enabled")
        if self.file == True:
            #file writes will be handled within log_event() method similiar
            # to what happens in core.py. the evtlvl value determines what file it goes to
            # as of now file logs always happen flag later maybe?
            #i do still do one more check @ runtime of method just to make sure 
            # its enabled then its written to appropriate log
            self.write_config_log("file logging enabled",False)
            self.write_config_log(f"logs are located in {self.logdir}",False)
        else:
            self.write_config_log("file logging disabled",False)
        self.syslog = self.syslog_config.get("enabled")
        if self.syslog == True:
            self.write_config_log("syslog logging enabled",False)
            # create syslog handler
            # self.syslog_handler = SysLogHandler((self.syslog_config.get("syslog_host"),self.syslog_config.get("syslog_port")),1,socktype=socket.SOCK_STREAM)
            # self.syslog_handler.setLevel(logging.DEBUG)
            # self.syslog_handler.ident = socket.gethostname()
            # syslog_fmt ='     %(message)s'
            # self.syslog_handler.setFormatter(logging.Formatter(syslog_fmt))
            # self.addHandler(self.syslog_handler)
            # self.enable_syslog_output()
            
        else:
            self.write_config_log("syslog logging disabled",False)
        self.smtp = self.smtp_config.get("enabled")
        if self.smtp == True:
            self.write_config_log("smtp logging enabled",False)
            #self.smtp_handler = SMTPHandler()
        else:
            self.write_config_log("smtp logging disabled",False)
        self.winevent = self.winevent_config.get("enabled")
        if self.winevent == True:
            self.write_config_log("windows logging enabled",False)
        else:
            self.write_config_log("windows logging disabled",False)
       
        
    
    def has_console_handler(self):
        return len([h for h in self.handlers if type(h) == logging.StreamHandler]) > 0
    def has_NTevent_handler(self):
        return len([h for h in self.handlers if type(h) == NTEventLogHandler]) > 0
    def has_file_handler(self):
        return len([h for h in self.handlers if isinstance(h, logging.FileHandler)]) > 0
    def has_smtp_handler(self):
        return len([h for h in self.handlers if type(h) == SMTPHandler]) > 0
    def has_syslog_handler(self):
        return len([h for h in self.handlers if type(h) == SysLogHandler]) > 0
    

    def disable_console_output(self):
        """
        Disables console output if its present
        """
        if not self.has_console_handler():
            return
        self.removeHandler(self.stdout_handler)
    
    def disable_file_output(self):
        """
        Disables file output if its present
        """
        if not self.has_file_handler():
            return
        self.removeHandler(self.file_handler)

    def disable_smtp_handler(self):
        """
        Disables smtp output if its present
        """
        if not self.has_smtp_handler():
            return
        self.removeHandler(self.smtp_handler)
        pass

    def disable_syslog_output(self):
        if not self.has_syslog_handler():
            return
        self.removeHandler(self.syslog_handler)
    
    def disable_NTevent_handler(self):
        if not self.has_NTevent_handler():
            return
        self.removeHandler(self.windows_handler)

    def enable_console_output(self):
        """
        Enables console output if not already present
        """
        if self.has_console_handler():
            return
        self.addHandler(self.stdout_handler)

    def enable_file_output(self):
        """
        Enables file output if not already present
        """
        if self.has_file_handler():
            return
        self.addHandler(self.file_handler)
    
    def enable_smtp_handler(self):
        """
        Enables smtp output if not already present
        """
        # if self.has_smtp_handler():
        #     return
        # self.addHandler(self.smtp_handler)
        pass

    def enable_syslog_output(self):
        if self.has_syslog_handler():
            return
        self.addHandler(self.syslog_handler)
    #this might not be needed but is here    
    def enable_NTevent_output(self):
        if self.has_NTevent_handler():
            return
        self.addHandler(self.windows_handler)
        pass
    def get_config_time(self):
        """grabs current time and returns it in %Y-%m-%d %H:%M:%S format"""
        ts = time.time()
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    def write_config_log(self, line:str, console:bool):
        """Creates a log file specifically for config generation in logs dir. """
        if 'win' in sys.platform:
            PROGRAM_FILES = os.environ["PROGRAMFILES(X86)"]
        if ('linux' or 'linux2' or 'darwin') in sys.platform:
            PROGRAM_FILES ="/var"
        LOG_FILE = os.path.join(PROGRAM_FILES, "artillery","logs","configuration.log")
        if not os.path.isfile(LOG_FILE):
            with open(file=LOG_FILE,mode='x',encoding='utf-8') as log:
                if console is True:
                    print(f"{self.get_config_time()}: [*] {line}")
                log.write("************Artillery configuration log************"+"\n")
                log.write(f"{self.get_config_time()}: [*] {line}\n")
        else:
            with open(file=LOG_FILE,mode='a',encoding='utf-8') as log:
                if console is True:
                    print(f"{self.get_config_time()}: [*] {line}")
                log.write(f"{self.get_config_time()}: [*] {line}\n")
        pass
    def framework(self, msg, *args, **kwargs):
        """Logging method for the FRAMEWORK level. The `msg` gets logged both to stdout and to file
        (if a file handler is present), irrespective of verbosity settings."""
        return super().info(msg, *args, **kwargs)
    
    def _custom_log(self, func, msg, *args, **kwargs):
        """Helper method for logging DEBUG through CRITICAL messages by calling the appropriate
        `func()` from the base class."""
        # Log normally if verbosity is on
        if self.verbose:
            return func(msg, *args, **kwargs)
        # If verbosity is off and there is no file handler, there is nothing left to do
        if not self.has_file_handler():
            return
        # If verbosity is off and a file handler is present, then disable stdout logging, log, and
        # finally reenable stdout logging
        self.disable_console_output()
        func(msg, *args, **kwargs)
        self.enable_console_output()
    #sig from core.py
    #log_event(alert: str, loglvl: int, evtid: int | None, console: bool)->None:
    def log_new_event(self,alert: str, loglvl: int, evtid: int | None, console: bool)->None:
        pass
    #old sig
    #log_event(self,src,level,msg,*args, **kwargs):
    #log_event(self, alert: str, loglvl: int, evtid: int, console: bool, *args, **kwargs):
    def log_event(self,src,level,msg,*args, **kwargs):
        """
        Main event to call when using class. No need to write .info and such after logger instance
        just pass the level through when called with event info
        """
        #just make it capital
        lvl = str(level).upper()
        match lvl:
            case "DEBUG":
                self.debug(msg, *args, **kwargs)
            case "INFO":
                self.info(msg, *args, **kwargs)
            case "WARNING":
                self.warning(msg, *args, **kwargs)
            case "ERROR":
                self.error(msg, *args, **kwargs)
            case "CRITICAL":
                self.critical(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._custom_log(super().debug, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._custom_log(super().info, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._custom_log(super().warning, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._custom_log(super().error, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._custom_log(super().critical, msg, *args, **kwargs)

        #
        #expose method to log events as needed