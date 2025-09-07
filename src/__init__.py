
#this will load all availible options 
#to be used elsewhere in app before main app loads
##THIS FILE WILL HOLD MOST GLOBAL SETTINGS AND CONFIGURATION OPTIONS FOR ARTILLERY
##VALUES ARE STORED AS A DICTIONARY AND CAN BE ACCESSED VIA settings.get_config('section', 'option') OR settings.is_config_enabled('option')
##THIS WILL ALLOW FOR EASIER CONFIGURATION AND MANAGEMENT OF ARTILLERY SETTINGS
##THIS FILE WILL FUNCTION AS GLOBALS.PY DID IN PREVIOUS VERSIONS WITHOUT THE NEED FOR A SEPARATE FILE
##OR THE USE OF THE GLOBAL KEYWORD ,THESE SETTINGS WILL BE USED THROUGHOUT THE APPLICATION
##for now this will be used to load the config file and get the values
import os
from .config import *
settings = ConfigMgr()

#
__VERSION__ = "3.0.0"
__AUTHOR__ = "Dave Kennedy (ReL1K) @HackingDave"
__EMAIL__ = ""
__DESCRIPTION__ = "An active honeypotting tool and threat intelligence feed"
__COPYRIGHT__ = "Copyright (c) 2025 Artillery Team"
__LICENSE__ = "BSD"
__URL__ = "https://www.binarydefense.com"


