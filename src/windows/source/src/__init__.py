
#this will load all availible options 
#to be used elsewhere in app before main app loads
##THIS FILE WILL HOLD MOST GLOBAL SETTINGS AND CONFIGURATION OPTIONS FOR ARTILLERY
##VALUES ARE STORED AS A DICTIONARY AND CAN BE ACCESSED VIA settings.get_config('section', 'option') OR settings.is_config_enabled('option')
##THIS WILL ALLOW FOR EASIER CONFIGURATION AND MANAGEMENT OF ARTILLERY SETTINGS
##THIS FILE WILL FUNCTION AS GLOBALS.PY DID IN PREVIOUS VERSIONS WITHOUT THE NEED FOR A SEPARATE FILE
##OR THE USE OF THE GLOBAL KEYWORD ,THESE SETTINGS WILL BE USED THROUGHOUT THE APPLICATION
import warnings
import functools
import time
from .config import *
from .Rlogger import *
settings = ConfigMgr()
version = settings.get_config("global","VERSION")
#returns [AVAILIBLE_SERVICES,ENABLED_SERVICES,DISABLED_SERVICES,CONFIGURATION_SETTINGS]
enabled_services = settings.get_enabled_services()
write_configuration_log(f"Running Artillery version: {version}",False)
write_configuration_log("Checking services",False)
write_configuration_log(f"Enabled services: {enabled_services[1]}",False)
write_configuration_log(f"Disabled services: {enabled_services[2]}",False)
write_configuration_log("generating logging info",False)
#returns [file,syslog,smtp,console,winevt] settings
log_info = settings.generate_logging_configs()
write_configuration_log(f"file log settings: {log_info[0]}",False)
write_configuration_log(f"syslog settings: {log_info[1]}",False)
write_configuration_log(f"smtp settings: {log_info[2]}",False)
write_configuration_log(f"console settings: {log_info[3]}",False)
write_configuration_log(f"windows event settings: {log_info[4]}",False)
#from here pass thru to logging class
#proposed sig for new logger
#(name:str,log_dir:str, config:list[dict,dict,dict,dict,dict],propogate=bool):
log=Custom_Logger(name="Artillery",log_dir=settings.get_config("global","LOG_FILE"),config=log_info)
#once finished will expose method for rest of software to use. log variable will be passed down to core.py
# method will look like this in code:  log.log_event(alert="my alert",loglvl=1,evtid=0,console=true)
#sig from core.py has been merged into custom logger
#log_event(alert: str, loglvl: int, evtid: int | None, console: bool)->None:
#this results in minimal changes to existing codebase
#while combining logging sources into one place to modify in future to add capabiities
__VERSION__ = version
__AUTHOR__ = "Dave Kennedy (ReL1K) @HackingDave"
__EMAIL__ = ""
__DESCRIPTION__ = "An active honeypotting tool and threat intelligence feed"
__COPYRIGHT__ = "Copyright (c) 2025 Artillery Team"
__LICENSE__ = "BSD"
__URL__ = "https://www.binarydefense.com"

#these are decorators to use throughout code
#descriptions are self explanatory
def deprecated(reason: str):
    """A custom decorator to mark functions as deprecated."""
    def decorator(func):
        @functools.wraps(func)  # Preserves the original function's name and docstring
        def wrapper(*args, **kwargs):
            # Construct a clear, descriptive warning message
            msg = f"Call to deprecated function '{func.__name__}'."
            if reason:
                msg += f" {reason}"
            
            #write an entry to the configuration log
            write_configuration_log(f"{msg}",False)
            #dont know if i realy need this here but it is for now
            # this will pollute the screen with warnings on posix
            # warnings.simplefilter("always",DeprecationWarning)
            # warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def timer(func):
    """Print the runtime of the decorated function"""

    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f"Finished {func.__name__!r} in {run_time:.4f} secs")
        return value

    return wrapper_timer


def debug(func):
    """Print the function signature and return value"""

    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}")
        return value

    return wrapper_debug

def count_calls(func):
    """Count the number of calls made to the decorated function"""

    @functools.wraps(func)
    def wrapper_count_calls(*args, **kwargs):
        wrapper_count_calls.num_calls += 1
        print(f"Call {wrapper_count_calls.num_calls} of {func.__name__!r}")
        return func(*args, **kwargs)

    wrapper_count_calls.num_calls = 0
    return wrapper_count_calls

def slow_down(_func=None, *, rate=1):
    """Sleep given amount of seconds before calling the function"""

    def decorator_slow_down(func):
        @functools.wraps(func)
        def wrapper_slow_down(*args, **kwargs):
            time.sleep(rate)
            return func(*args, **kwargs)

        return wrapper_slow_down

    if _func is None:
        return decorator_slow_down
    else:
        return decorator_slow_down(_func)

def cache(func):
    """Keep a cache of previous function calls"""

    @functools.wraps(func)
    def wrapper_cache(*args, **kwargs):
        cache_key = args + tuple(kwargs.items())
        if cache_key not in wrapper_cache.cache:
            wrapper_cache.cache[cache_key] = func(*args, **kwargs)
        return wrapper_cache.cache[cache_key]

    wrapper_cache.cache = dict()
    return wrapper_cache


