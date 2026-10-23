import datetime
import logging
import os
import sys
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
# Create a custom logger with the specified `name`. When `log_dir` is None, a simple
        # console logger is created. Otherwise, a file logger is created in addition to the console
        # logger.

        # This custom logger class adds an extra logging level FRAMEWORK (at INFO priority), with the
        # aim of logging messages irrespective of any verbosity settings.

        # By default, the five standard logging levels (DEBUG through CRITICAL) only display
        # information in the log file if a file handler is added to the logger, but **not** to the
        # console.

class CustomLogger(logging.getLoggerClass()):
    #current Class sig 
    # self, name, verbose, log_dir=None,timestamp=None,propagate=False
    #proposed sig this will be the root logger
    #all of these values will be generated @ runtime and passed through
    #self,name,[{file_config},{syslog_config},{smtp_config},{console_config},{winevent_config}]
    #log_dir is passed through as well
    #
    # def __init__(self,name:str,log_dir:str, config:list[dict,dict,dict,dict,dict]):
    #     # Create custom logger logging all five levels
    #     self.name = str(name).upper()
    #     super().__init__(self.name)
    #     self.setLevel(logging.DEBUG)
    #     this makes us the root logger
    #     self.propagate = False
    #     #setup all our config values
    #     self.logdir = log_dir
    #     #file writes will be handled within log_event() method similiar to what happens in core.py
    #     # the evtlvl value determines what file it goes to as of now file logs always happen flag later maybe?
    #     # five values
    #     self.file_config = config[0]
    #     # two values
    #     self.syslog_config = config[1]
    #     # eleven values
    #     self.smtp_config = config[2]
    #     # one value
    #     self.console_config = config[3]
    #     # unknown yet (not enabled)
    #     self.winevent_config = config[4]
    #     #do checks to see what we need to setup
        # Determine console settings
        # self.console = self.console_config.get("enabled")
        #if self.console == True:
        # # Create stream handler for logging to stdout (log all five levels)
        # self.stdout_handler = logging.StreamHandler(sys.stdout)
        # self.stdout_handler.setLevel(logging.DEBUG)
        # self.stdout_handler.setFormatter(logging.Formatter('%(message)s'))
        # self.syslog = self.syslog_config.get("enabled")
        # if self.sysylog == True:
        # # create syslog handler
        # self.syslog_handler = SysLogHandler((self.syslog_config.get("syslog_host"),self.syslog_config.get("syslog_port")),1,socktype=socket.SOCK_STREAM)
        # self.syslog_handler.setLevel(logging.DEBUG)
        # self.syslog_handler.ident = socket.gethostname()
        # syslog_fmt ='     %(message)s'
        # self.syslog_handler.setFormatter(logging.Formatter(syslog_fmt))
        # self.addHandler(self.syslog_handler)
    #     #do console setup first
    #     #do syslog setup
    #     #do email setup
    #     #do file setup (handled seperatly @ runtime of log_event() method)
    #     #
    #     #expose method to log events as needed
    #     pass
    def __init__(self, name, verbose, log_dir=None,timestamp=None,propagate=False):
        """This class is responsible for logging with artillery system wide. it utilizses multiple class to 
        handle the various methods for proper logging. @ Creation it takes a list of dicts to establish what
        needs to be configured and how it should handle events. after this step it exposes a log_event() function to
        be used in the code.
        
        :param name: name for the logger this is used as the file name of log
        :param verbose: bool: whether the logging should be verbose; if True, then all messages get
            logged both to stdout and to the log file (if `log_dir` is specified); if False, then
            messages only get logged to the log file (if `log_dir` is specified), with the exception
            of FRAMEWORK level messages which get logged either way
        :param log_dir: str: (optional) the directory for the log file; if not present, no log file
            is created
        :param timestamp: bool: (optional) can be None.add timestamps to end of logs. Useful for targeting events
        :param propagate: bool: do we want to propagate logs up the chain of loggers
        """
        # Create custom logger logging all five levels
        self.name = str(name).upper()
        super().__init__(self.name)
        self.setLevel(logging.DEBUG)

        # Add new logging level
        #not sure where framework is this just ignores any settings set
        #every event gets logged with 'FRAMEWORK' as the source basically
        # removing info//warning//error as src of event this would be better for 
        #maybe using that level as a router so to speak as to what gets called?
        #

        #logging.addLevelName(logging.INFO, 'FRAMEWORK')
        #do we want to propogate logs up the chain of loggers?
        #by default self.propagate = True on setting up class meaning
        #events travel up the chain through each logger
        #
        if propagate == True:
            #just pass the default value is true
            pass
        else:
            self.propagate = propagate
        # Determine verbosity settings
        self.verbose = verbose
        #do we want timestamped log files?
        self.timestamp = timestamp
        # Create stream handler for logging to stdout (log all five levels)
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.stdout_handler.setLevel(logging.DEBUG)
        self.stdout_handler.setFormatter(logging.Formatter('%(message)s'))
        # create syslog handler
        self.syslog_handler = SysLogHandler(("192.168.2.11",SYSLOG_TCP_PORT),1,socktype=socket.SOCK_STREAM)
        self.syslog_handler.setLevel(logging.DEBUG)
        self.syslog_handler.ident = socket.gethostname()
        syslog_fmt ='     %(message)s'
        self.syslog_handler.setFormatter(logging.Formatter(syslog_fmt))
        self.addHandler(self.syslog_handler)
        #create window event handler dont really like this handler to much
        #my func replaces this as just calling the event i already add all the relevant info
        #maybe can be incorperated in here but we'll see
        if WINDOWS_EVENTS_ENABLED == True:
            self.windows_handler = NTEventLogHandler(appname="test_handler",dllname="core.dll",logtype="Application")
            self.windows_handler.setLevel(logging.DEBUG)
            self.addHandler(self.windows_handler)
        #create smtp handler this is our custom email class this will
        #also need to be researched as the email_handler is its own custom class

        self.enable_console_output()
        self.enable_syslog_output()
        
        self.file_handler = None
        if log_dir:
            self.add_file_handler(name, log_dir)

    def add_file_handler(self, name, log_dir):
        """Add a file handler for this logger with the specified `name` (and store the log file
        under `log_dir`)."""
        # Format for file log
        #maybe would like to change format based on src or have it passed through? possibly
        #set at Class creation so that log format can be unique IDK? you wont always need the line # in the logs
        #of where the func was called from flags maybe?
        fmt = '%(asctime)9s | %(name)s | %(levelname)s : %(message)s'
        #fmt = '%(asctime)s | %(levelname)9s | %(filename)s:%(lineno)d | %(message)s'
        formatter = logging.Formatter(fmt)

        # Determine log path and file name; change to include filename in construction
        #if used, use that name instead useful for static logs. like the idea of verbose\quiet naming convention
        #just not for my use case
        if self.timestamp == True:
            now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            log_name = f'{str(name).replace(" ", "_")}_{now}'
        else:
            log_name = f'{str(name)}'
        #create log path if it does not exist
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except:
                print(f'{self.__class__.__name__}: Cannot create directory {log_dir}. ',
                        end='', file=sys.stderr)
                log_dir = '/tmp' if sys.platform.startswith('linux') else '.'
                print(f'Defaulting to {log_dir}.', file=sys.stderr)

        log_file = os.path.join(log_dir, log_name) + '.log'

        # Create file handler for logging to a file (log all five levels)
        # self.alertlog =""
        # self.infolog =""
        # self.warnlog =""
        # self.errlog =""
        # self.critlog =""
        self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(formatter)
        self.addHandler(self.file_handler)
    #not implemented yet
    def default_log_record(self) -> logging.LogRecord:
        """
        Creates a default blank log record for use in creating events
        and returns it
        """
        record = logging.LogRecord(name="",
                                   level=1,
                                   pathname="",
                                   lineno=1,
                                   msg="",
                                   args=None,
                                   exc_info=None
                                   ,func=None,
                                   sinfo=None)
        return record

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

def test_colors():
    print('*' * 80 + '\nColor Pallette\n' + '*' * 80)
    for item in Color:
        if item.name.startswith('_'):
            continue
        print(Color.colored(item, item.name))
        if item.name.startswith('LIGHT'):
            print(Color.colored(item, f'{item.name[5:]} bold == {item.name} bold', bold=True))

def log_by_name_and_level(name:str,level:int,msg:str):
    print('*' * 80 + '\nLog event by passing "name" of log and "level" ex INFO//Warning(stdout + file)\n' + '*' * 80)
    logs = f'logs\\'
    named_log = CustomLogger(name, verbose=True, log_dir=logs,timestamp=None)
    named_log.log_event(src=name,level=level,msg=f"{name.upper()} {msg}")
    #named_log.warning(msg=message)

    #named_log.log_event(src=name,level=level,msg="after renabling file output")
    #named_log.info("hey again 2 from my func this time writing to the file")
    # verbose_log.warning('We now log to both stdout and a file log')

    # verbose_log.disable_file_output()
    # msg = 'Use color in a true TTY'
    # if sys.stdout.isatty():
    #     verbose_log.info(Color.colored(Color.LIGHTYELLOW, msg))
    # else:
    #     verbose_log.info(msg + ', but not here')
    # verbose_log.enable_file_output()

    # verbose_log.framework('We now log everywhere irrespective of verbosity')


    pass


# def test_verbose():
#     print('*' * 80 + '\nVerbose logging (stdout + file)\n' + '*' * 80)
#     verbose_log = CustomLogger('verbose', verbose=True, log_dir='logs\\testing',timestamp=None)

#     verbose_log.warning('We now log to both stdout and a file log')

#     verbose_log.disable_file_output()
#     msg = 'Use color in a true TTY'
#     if sys.stdout.isatty():
#         verbose_log.info(Color.colored(Color.LIGHTYELLOW, msg))
#     else:
#         verbose_log.info(msg + ', but not here')
#     verbose_log.enable_file_output()

#     verbose_log.framework('We now log everywhere irrespective of verbosity')


# def test_quiet():
#     print('*' * 80 + '\nQuiet logging (stdout: only FRAMEWORK + file: all levels)\n' + '*' * 80)
#     quiet_log = CustomLogger('quiet', verbose=False, log_dir='logs\\testing',timestamp=None)
#     quiet_log.warning('We now log only to a file log')
#     quiet_log.framework('We now log everywhere irrespective of verbosity')

# def artillery_quiet():
#     print('*' * 80 + '\nArtillery logging (stdout: only FRAMEWORK + file: all levels)\n' + '*' * 80)
#     quiet_log = CustomLogger('quiet', verbose=False, log_dir='logs\\artillery')
#     quiet_log.warning('We now log only to a file log')
#     quiet_log.framework('We now log everywhere irrespective of verbosity')

# def artillery_verbose():
#     print('*' * 80 + '\nVerbose logging (stdout + file)\n' + '*' * 80)
#     verbose_log = CustomLogger('verbose', verbose=True, log_dir='logs\\artillery')

#     #verbose_log.warning('We now log to both stdout and a file log')

#     verbose_log.disable_file_output()
#     msg = 'Use color in a true TTY'
#     if sys.stdout.isatty():
#         verbose_log.info(Color.colored(Color.LIGHTYELLOW, msg))
#     else:
#         verbose_log.info(msg + ', but not here')
#     verbose_log.enable_file_output()

#     verbose_log.framework('We now log everywhere irrespective of verbosity')

def test_colors():
    print('*' * 80 + '\nColor Pallette\n' + '*' * 80)
    for item in Color:
        if item.name.startswith('_'):
            continue
        print(Color.colored(item, item.name))
        if item.name.startswith('LIGHT'):
            print(Color.colored(item, f'{item.name[5:]} bold == {item.name} bold', bold=True))

if __name__ == '__main__':
    log_by_name_and_level(name="ssh",level="WARNING",msg="hey from my function")
    # test_verbose()
    # test_quiet()
    #test_colors()
