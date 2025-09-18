if __name__ == "__main__":
    """
        Setup file for artillery
    """
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
            import subprocess,time,platform,shutil,datetime
    #
    elif ('linux' or 'linux2' or 'darwin') in sys.platform:
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
            import subprocess,time,platform,shutil,datetime
########################################################################################################################
    class Setup():
        def __init__(self):
            self.installed = False
            #self.args = parser.parse_args()
            self.logfile = "setuplog.txt"
            self.win32 = self.is_windows()
            self.posix = self.is_posix()
            self.log_location = ""
            self.tempdir = ""
            self.program_home = ""
            if self.win32:
                self.tempdir = os.environ["TEMP"]
                self.log_location = os.path.join(self.tempdir,self.logfile)
            if self.posix:
                self.tempdir = os.environ["/var"]
                self.log_location = os.path.join(self.tempdir,self.logfile)
            if self.win32:
                self.program_home = os.environ["PROGRAMFILES(X86)"]
            if self.posix:
                self.program_home = os.environ["/var"]
            self.install_path = os.path.join(self.program_home, "Artillery")
            self.main_file = os.path.join(self.program_home,"artillery","artillery.py")
            self.interactive = True
            self.installed_state()
            pass
        def get_time(self):
            '''grabs current time and returns it in %Y-%m-%d %H:%M:%S format'''
            ts = time.time()
            return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            
        def banner(self):
            banner = "################################################################\n"
            banner +="#               Welcome to the Artillery installer.            #\n"
            banner +="#                                                              #\n"
            banner +="#    Artillery is a honeypot, file monitoring, and security    #\n"
            banner +="#      tool used to protect your nix and windows systems       #\n"
            banner +="#                     using various methods.                   #\n"
            banner +="#                                                              #\n"
            banner +="#                 Written by: Dave Kennedy (ReL1K)             #\n"
            banner +="################################################################\n"
            return banner
        def is_windows(self):
            '''returns true platform is Windows related'''
            return os.name == "nt"
        #
        def is_posix(self):
            '''returns true platform is posix related'''
            return os.name == "posix"
        #
        def pause_console(self):
            pause = input("Press return to continue")

        def write_log(self,line:str,console:bool):
            """Creates a log file specifically for setup in %TEMP% dir. 
            file is copied at end of setup to artillery log dir on install, 
            desktop on uninstall. Windows only for now will be updated in next release"""
            timenow = self.get_time()
            if not os.path.isfile(self.log_location):
                with open(file=self.log_location,mode='x',encoding='utf-8') as log:
                    if console == True:
                        print(line)
                    log.write("************Artillery setup log************"+"\n")
                    log.write(f"{timenow}: setup[INFO] {line}" + "\n")
            else:
                with open(file=self.log_location,mode='a',encoding='utf-8') as log:
                    if console == True:
                        print(line)
                    log.write(f"{timenow}: setup[INFO] {line}" + "\n")
        #
        def check_depedencies(self):
            """
                This check is for the existence of some needed libraries for the install as well
            as artillery runtime itself. It will get the latest version for the python version running on host.
            specifically pywin32 and requests on Windows.This will breakout for both platforms at a point. 
            This can probably be done better it works with no issue with fresh install of python 3.13.0 
            windows. I am assuming a completly fresh install of python on host
            """
            from importlib.metadata import version
            import importlib.util
            args = parser.parse_args()
            if args.y == True:
                self.interactive = False
                print("silent install")
            else:
                print("normal install")
            try:
                if self.interactive == True:
                    self.write_log(line="Checking for needed libraries",console=True)
                else:
                    self.write_log(line="Checking for needed libraries",console=False)
            except Exception as e:
                print(e)
            #for some reason importlib.util.find_spec("pywin32") fails to find if installed??
            #so i use version and it does what i want? thanks python :((
            pywin32 = ""
            requests = ""
            installed = False
            if self.win32 == True:
                try:
                    import win32com
                except ImportError as e:
                    if self.interactive == True:
                        self.write_log(line="pywin32 is not present installing",console=True)
                        installed = True
                    else:
                        self.write_log(line="pywin32 is not present installing",console=False)
                        installed = True
                    subprocess.check_call([sys.executable,'-m','pip','install','pywin32'],shell=True)
            try:
                import requests
            except ImportError as e:
                if self.interactive == True:
                    self.write_log(line=f"{e}",console=True)
                    installed = True
                else:
                    self.write_log(line="requests is not present installing",console=False)
                    installed = True
                subprocess.check_call([sys.executable,'-m','pip','install','requests'],shell=True)
            #added to avoid import issues if we installed libs restart setup
            if installed == True:
                self.write_log(line="Libraries were installed restarting to avoid issues",console=True)
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit()
            pywin32 = version('pywin32')
            if pywin32 is not None:
                #get the version
                pywin32_ver = version('pywin32')
                if self.interactive == True:
                    self.write_log(f"pywin32 {pywin32_ver} is installed",True)
            requests = importlib.util.find_spec("requests")
            if requests is not None:
                requests_ver = version("requests")
                if self.interactive == True:
                    self.write_log(f"requests {requests_ver} is installed",True)
            
        def installed_state(self):
            if os.path.isfile(self.main_file):
                self.installed = True
            else:
                pass
            
            
        def check_setup(self):
            if self.installed == True:
                #must want to uninstall
                self.do_uninstall()
            else:
                #its not here install it
                self.do_install()

        def do_install(self):
            #check the platform
            args = parser.parse_args()
            if self.win32 == True:
                if args.y == True:
                    self.interactive = False
                #hard limit on version moving forward
                #will work in better logic to avoid issue
                if self.interactive == True:
                    self.write_log(line="Checking python version",console=True)
                else:
                    self.write_log(line="Checking python version",console=False)
                py_ver = platform.python_version_tuple()
                if py_ver[0] == "3":
                    if py_ver[1] >= "10":
                        if py_ver[2] >= "0":
                            if self.interactive == True:
                                self.write_log(line=f"Running python {platform.python_version()}",console=True)
                            else:
                                self.write_log(line=f"Running python {platform.python_version()}",console=False)
                else:
                    #this should never be hit but,
                    if self.interactive == True:
                        self.write_log(line=f"@ least python 3.10.0 required\nYour version: {platform.python_version()} exiting",console=True)
                    else:
                        self.write_log(line=f"@ least python 3.10.0 required\nYour version: {platform.python_version()} exiting",console=False)
                    sys.exit()
                try:
                    import win32com
                    import requests
                    import win32com.client
                except ImportError as e:
                    print(e)
                SRC_PATH = os.getcwd()
                PROGRAM_DATA = os.environ["PROGRAMDATA"]
                PROGRAM_FILES = os.environ["PROGRAMFILES(X86)"]
                INSTALL_PATH = os.path.join(PROGRAM_FILES, "Artillery")
                answer = ""
                if self.interactive == True:
                    self.write_log(line="Running in interactive install mode ",console=True)
                    answer = input("Do you want to install Artillery and have it automatically run when you restart [y/n]: ")
                else:
                    self.write_log(line="Running in non interactive install mode with automatic \'yes\' selection",console=True)
                    answer = 'y'
                if answer == 'y':
                    if self.interactive == True:
                        self.write_log(line=f"Copying files over to {self.install_path}",console=True)
                    else:
                        self.write_log(line=f"Copying files over to {self.install_path}",console=False)
                shutil.copytree(SRC_PATH, self.install_path)
                if self.interactive == True:
                    self.write_log(line="Creating additional dirs",console=True)
                else:
                    self.write_log(line="Creating additional dirs",console=False)
                os.makedirs(os.path.join(self.install_path, "logs"))
                os.makedirs(os.path.join(self.install_path,"database"))
                os.makedirs(os.path.join(self.install_path,"src","program_junk"))
                if self.interactive:
                    self.write_log(line="Copy Complete",console=True)
                else:
                    self.write_log(line="Copy Complete",console=False)
                #create artillery desktop shortcut
                if self.interactive == True:
                    self.write_log(line="Creating Artillery desktop shortcut",console=True)
                else:
                    self.write_log(line="Creating Artillery desktop shortcut",console=False)
                self.create_shortcuts(targetpath='python',
                            shortcutname="artillery.lnk",
                            icon=os.path.join(INSTALL_PATH,"src","icons","bd_icon.ico"),
                            description="Artillery startup",
                            args="Artillery.py",
                            destination='desktop')
                #create logon shorcut
                if self.interactive == True:
                    self.write_log(line="Creating startup shortcut",console=True)
                else:
                    self.write_log(line="Creating startup shortcut",console=False)
                self.create_shortcuts(targetpath='python',
                            shortcutname="artillery.lnk",
                            icon=os.path.join(INSTALL_PATH,"src","icons","bd_icon.ico"),
                            description="Logon start",
                            args="Artillery.py",
                            destination='startup')
                #create firewall rules if flag present
                #will probably put a check here for the rule even if flag is not passed at runtime
                #to prevent uneeded work
                #rules are automatically created by windows on launch but it says python in windows firewall
                #here it can be the same rule i just have control of the name i see
                if args.fw == True:
                    #artillery is installed at this point so make the rule
                    if self.interactive == True:
                        self.write_log(line="Simulating creating incoming allow rule for artillery",console=True)
                    else:
                        self.write_log(line="Simulating creating incoming allow rule for artillery",console=True)
                if self.interactive == True:
                    choice = input("Would you like to start Artillery now? [y/n]: ")
                else:
                    choice = 'y'
                if choice =="y":
                    #these will all be re-worked
                    os.chdir("src\\windows")
                    #register dll
                    if self.interactive == True:
                        self.write_log(line="Registering dll with system",console=True)
                    else:
                        self.write_log(line="Registering dll with system",console=False)
                    self.add_dll()
                    time.sleep(1)
                    if self.interactive == True:
                        self.write_log(line="Artillery has been installed",console=True)
                    else:
                        self.write_log(line="Artillery has been installed",console=False)
                    time.sleep(1)
                    #launch from install dir
                    if self.interactive == True:
                        self.write_log(line="Launching artillery from install dir",console=True)
                    else:
                        self.write_log(line="Launching artillery from install dir",console=False)
                    try:
                        #launches artillery in a new process
                        subprocess.call(['cmd', '/C', 'python', f"{self.install_path}\\Artillery.py"],shell=True,creationflags=subprocess.DETACHED_PROCESS,timeout=3)
                    except subprocess.TimeoutExpired:
                        #will do a check to see if running for now i just pass
                        pass
                    #copy over the setup log and delete the original for future runs   
                    if os.path.isfile(self.log_location):
                        logdest = os.path.join(self.install_path,"logs")
                        #always say where the logs are regardless of mode
                        self.write_log(line=f"Setup complete copying logs to {logdest}",console=True)
                        subprocess.call(['cmd', '/C', 'copy',self.log_location, logdest],shell=True)
                        time.sleep(1)
                        subprocess.call(['cmd', '/C', 'del', self.log_location],shell=True)
                        self.pause_console()
                #setup complete
                else:
                    # n was pressed
                    if self.win32:
                        os.chdir("src\\windows")
                        #register dll
                        if self.interactive == True:
                            self.write_log(line="Registering dll with system",console=True)
                        else:
                            self.write_log(line="Registering dll with system",console=False)
                        time.sleep(1)
                        self.add_dll()
                        if self.interactive == True:
                            self.write_log(line="Artillery has been installed",console=True)
                        else:
                            self.write_log(line="Artillery has been installed",console=False)
                        if os.path.isfile(self.log_location):
                            logdest = os.path.join(self.install_path,"logs")
                            #always say where the logs are regardless of mode
                            self.write_log(line=f"Setup complete copying logs to {logdest}",console=True)
                            subprocess.call(['cmd', '/C', 'copy', self.log_location, logdest],shell=True)
                            time.sleep(1)
                            subprocess.call(['cmd', '/C', 'del', self.log_location],shell=True)
                        self.pause_console()
            #setup complete
            if self.posix == True:
                if args.y == True:
                    self.interactive = False
                #hard limit on version moving forward
                #will work in better logic to avoid issue
                if self.interactive == True:
                    self.write_log(line="Checking python version",console=True)
                else:
                    self.write_log(line="Checking python version",console=False)
                py_ver = platform.python_version_tuple()
                if py_ver[0] == "3":
                    if py_ver[1] >= "10":
                        if py_ver[2] >= "0":
                            if self.interactive == True:
                                self.write_log(line=f"Running python {platform.python_version()}",console=True)
                            else:
                                self.write_log(line=f"Running python {platform.python_version()}",console=False)
                else:
                    #this should never be hit but,
                    if self.interactive == True:
                        self.write_log(line=f"@ least python 3.10.0 required\nYour version: {platform.python_version()} exiting",console=True)
                    else:
                        self.write_log(line=f"@ least python 3.10.0 required\nYour version: {platform.python_version()} exiting",console=False)
                    sys.exit()
                SRC_PATH = os.getcwd()
                answer = ""
                if self.interactive == True:
                    self.write_log(line="Running in interactive install mode ",console=True)
                    answer = input("Do you want to install Artillery and have it automatically run when you restart [y/n]: ")
                else:
                    self.write_log(line="Running in non interactive install mode with automatic \'yes\' selection",console=True)
                    answer = 'y'
                if answer == 'y':
                    if self.interactive == True:
                        self.write_log(line=f"Copying files over to {self.install_path}",console=True)
                    else:
                        self.write_log(line=f"Copying files over to {self.install_path}",console=False)
                #just copy files as with windows to be consistant
                shutil.copytree(SRC_PATH, self.install_path)
                if self.interactive == True:
                    self.write_log(line="Creating additional dirs",console=True)
                else:
                    self.write_log(line="Creating additional dirs",console=False)
                os.makedirs(os.path.join(self.install_path, "logs"))
                os.makedirs(os.path.join(self.install_path,"database"))
                os.makedirs(os.path.join(self.install_path,"src","program_junk"))
                if self.interactive:
                    self.write_log(line="Copy Complete",console=True)
                else:
                    self.write_log(line="Copy Complete",console=False)
                if self.interactive == True:
                    self.write_log(line="Adding artillery into startup through init scripts..",console=True)
                else:
                    self.write_log(line="Adding artillery into startup through init scripts..",console=False)
                if os.path.isdir("/etc/init.d"):
                    if not os.path.isfile("/etc/init.d/artillery"):
                        fileopen = open("src/startup_artillery", "r")
                        config = fileopen.read()
                        filewrite = open("/etc/init.d/artillery", "w")
                        filewrite.write(config)
                        filewrite.close()
                        if self.interactive == True:
                            self.write_log(line="Triggering update-rc.d on artillery to automatic start...",console=True)
                        else:
                            self.write_log(line="Triggering update-rc.d on artillery to automatic start...",console=False)
                        subprocess.Popen(
                            "chmod +x /etc/init.d/artillery", shell=True).wait()
                        subprocess.Popen(
                            "update-rc.d artillery defaults", shell=True).wait()
                # remove old method if installed previously
                if os.path.isfile("/etc/init.d/rc.local"):
                    fileopen = open("/etc/init.d/rc.local", "r")
                    data = fileopen.read()
                    data = data.replace(
                        "sudo python /var/artillery/artillery.py &", "")
                    filewrite = open("/etc/init.d/rc.local", "w")
                    filewrite.write(data)
                    filewrite.close()
                if os.path.isdir("/Library/LaunchDaemons"):
                    # check if file is already in place
                    if not os.path.isfile("/Library/LaunchDaemons/com.artillery.plist"):
                        if self.interactive == True:
                            self.write_log(line="Creating com.artillery.plist in your Daemons directory",console=True)
                        else:
                            self.write_log(line="Creating com.artillery.plist in your Daemons directory",console=False)
                        filewrite = open(
                            "/Library/LaunchDaemons/com.artillery.plist", "w")
                        filewrite.write('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0">\n<dict>\n<key>Disabled</key>\n<false/>\n<key>ProgramArguments</key>\n<array>\n<string>/usr/bin/python</string>\n<string>/var/artillery/artillery.py</string>\n</array>\n<key>KeepAlive</key>\n<true/>\n<key>RunAtLoad</key>\n<true/>\n<key>Label</key>\n<string>com.artillery</string>\n<key>Debug</key>\n<true/>\n</dict>\n</plist>')
                        if self.interactive == True:
                           self.write_log(line="Adding right permissions",console=True)
                        else:
                            self.write_log(line="Adding right permissions",console=False)
                        subprocess.Popen(
                            "chown root:wheel /Library/LaunchDaemons/com.artillery.plist", shell=True).wait()
                if self.interactive == True:
                    choice = input("[*] Would you like to start Artillery now? [y/n]: ")
                else:
                    choice = 'y'
                if choice in ["yes", "y"]:  
                    subprocess.Popen("/etc/init.d/artillery start", shell=True).wait()
                if self.interactive == True:
                    self.write_log(line="Installation complete. Edit /var/artillery/config in order to config artillery to your liking",console=True)
                else:
                    self.write_log(line="Installation complete. Edit /var/artillery/config in order to config artillery to your liking",console=False)
            #setup complete
        def do_uninstall(self):
            args = parser.parse_args()
            if self.win32 == True:
                if args.y == True:
                    self.interactive = False
                answer = ""
                if self.interactive == True:
                    self.write_log(line="Running in interactive uninstall mode ",console=True)
                    answer = input("Artillery detected. Do you want to uninstall [y/n:] ")
                else:
                    self.write_log(line="Running in non interactive uninstall mode with automatic \'yes\' selection",console=True)
                    answer = 'y'
                if answer == "y":
                    users_desktop = os.path.join(os.path.expanduser("~"), "Desktop")  # Path to the user's desktop
                    desktop_path = os.path.join(users_desktop)
                    desktop_link = os.path.join(desktop_path,"artillery.lnk")
                    if os.path.isfile(desktop_link):
                        if self.interactive == True:
                            self.write_log("Removing desktop shortcut",True)
                        else:
                            self.write_log("Removing desktop shortcut",False)
                        subprocess.call(['cmd', '/C', 'del', desktop_link])
                    #samething for startup
                    program_data = os.environ["ProgramData"]
                    full_path = os.path.join(program_data, "Microsoft","Windows","Start Menu","Programs","Startup")
                    startup_link = os.path.join(full_path,"artillery.lnk")
                    if os.path.isfile(startup_link):
                        if self.interactive == True:
                            self.write_log("Removing startup shortcut",False)  
                        else:
                            self.write_log("Removing startup shortcut",True)
                        subprocess.call(['cmd', '/C', 'del', startup_link])
                    
                    #delete firewall rules
                    #will probably put a check here for the rule even if flag is not passed at runtime
                    if args.fw == True:
                        
                        if self.interactive == True:
                            self.write_log("Simulating deleting firewall rules",True)
                        else:
                            self.write_log("Simulating deleting firewall rules",False)
                    #remove artillery files
                    if self.interactive == True:
                        self.write_log(f"Removing artillery files located in {self.install_path}",True)
                    else:
                        self.write_log(f"Removing artillery files located in {self.install_path}",False)
                    subprocess.call(['cmd', '/C', 'rmdir', '/S', '/Q', self.install_path])
                    #remove dll entries
                    self.remove_dll()
                    if os.path.isfile(self.log_location):
                        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")  # Path to the user's desktop
                        logdest = os.path.join(desktop_path)
                        if self.interactive == True:                                                          #this line will be removed as we will check and kill in future
                            self.write_log("Artillery has been uninstalled.\nManually kill the process if it is still running.",True)
                        else:
                            self.write_log("Artillery has been uninstalled.\nManually kill the process if it is still running.",False)
                        #always say where the logs are regardless of mode
                        self.write_log(f"Uninstall complete copying logs to {logdest}",True)
                        t = subprocess.check_output(['cmd', '/C', 'copy', self.log_location, logdest],shell=True)
                        time.sleep(1)
                        subprocess.call(['cmd', '/C', 'del', self.log_location],shell=True)
                        pause = input("press any key to continue")
                else:
                    # n was pressed
                    self.write_log("Uninstall was aborted",True)
                #uninstall complete
            if self.posix == True:
                if args.y == True:
                    self.interactive = False
                answer = ""
                if self.interactive == True:
                    self.write_log(line="Running in interactive uninstall mode ",console=True)
                    answer = input("Artillery detected. Do you want to uninstall [y/n:] ")
                else:
                    self.write_log(line="Running in non interactive uninstall mode with automatic \'yes\' selection",console=True)
                    answer = 'y'
                if answer == "y":
                    os.remove("/etc/init.d/artillery")
                    subprocess.Popen("rm -rf /var/artillery", shell=True)
                    subprocess.Popen("rm -rf /etc/init.d/artillery", shell=True)
                if self.interactive == True:
                    self.write_log(line="Artillery has been uninstalled. Manually kill the process if it is still running.",console=True)
                else:
                    self.write_log(line="Artillery has been uninstalled. Manually kill the process if it is still running.",console=False)
            #uninstall done


            
        def add_dll(self):
            subprocess.run(['cmd', '/C', 'reg', 'import', 'ArtilleryEvents.reg'],shell=True)
        #
        def remove_dll(self):
            """Removes artillery event dll settings from the registry."""
            from win32evtlogutil import RemoveSourceFromRegistry
            RemoveSourceFromRegistry(appName ="Artillery", eventLogType = "Application")
            if self.interactive == True:
                self.write_log("Removed event dll entries from registry",True)
            else:
                self.write_log("Removed event dll entries from registry",False)
        #
        def create_shortcuts(self,targetpath:str,shortcutname:str, icon ,description:str, args:str|None, destination:str|None):

            """
                Creates windows shorcuts for artillery given the path to exe, name, icon, description
                this will be used primarily in setup.py as with the msi installer this is done automagically.


                    :param targetpath ex: "c:\\windows\\system32\\notepad.exe"
                    :param shortcutname ex: "notepad.lnk"
                    :param icon ex: "c:\\windows\\system32\\notepad.exe"
                    :param description ex: "python created shorcut"
                    :param args ex: "none"
                    :param destination ex: "'desktop' where to place final shortcut. desktop//systray//artillery//startup"
            """
            import win32com.client
            import os
            program_files = os.environ["PROGRAMFILES(x86)"]
            program_data = os.environ["ProgramData"]
            if destination == 'desktop':
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")  # Path to the user's desktop
                full_path = os.path.join(desktop_path)
                workingdir = os.path.join(program_files,'Artillery')
                #added for future inclusion of raw systray app
            elif destination == "systray":
                #program_data = os.environ["ProgramData"]
                full_path = os.path.join(program_data, "Artillery","systray")
                workingdir = full_path
            elif destination == "artillery":
                #program_files = os.environ["PROGRAMFILES(x86)"]
                full_path = os.path.join(program_files,"Artillery")
                workingdir = os.path.join(full_path)
            elif destination == "startup":
                #program_data = os.environ["ProgramData"]
                full_path = os.path.join(program_data, "Microsoft","Windows","Start Menu","Programs","Startup")
                workingdir = os.path.join(program_files,"Artillery")
                #create final shortcut save path
            shortcut_path = os.path.join(full_path, shortcutname)
            shell = win32com.client.Dispatch("WScript.Shell")
                # Create the shortcut object
            shortcut = shell.CreateShortCut(shortcut_path)
                # Set shortcut properties
            shortcut.TargetPath = targetpath
            shortcut.WorkingDirectory = workingdir#os.path.dirname(targetpath)#workingdir
            # else:
            #     os.path.dirname(targetpath)#Set the working directory      #os.path.dirname(targetpath)#Set the working directory
            shortcut.Description = description
                #check for any arguments
            if args is None:
                pass
            else:
                shortcut.Arguments = args
            if icon == "" or None:
                pass
            else:
                shortcut.IconLocation = icon# Optional: Set a custom icon
                # Save the shortcut
            shortcut.save()
    ###################################################################################################################################
    install = Setup()
    parser = argparse.ArgumentParser(prog='setup',usage='%(prog)s [options]',description='Artillery installer',add_help=True)
    parser.add_argument('-y', action='store_true', help='Installs artillery silently.')
    parser.add_argument('-fw',action='store_true', help='Adds or removes firewall rules during setup on windows')
    #parser.add_argument('-su',action='store_true', help='Adds startup shortcut on windows systems')
    parser.set_defaults(function=install.check_setup)
    args = parser.parse_args()
    #silent install
    if args.y == True:
        pass
    else:
        print(install.banner())
    #checks and installs pywin32,requests on windows
    install.check_depedencies()
    try:
        if hasattr(args, 'function'):
            args.function()
    except Exception as e:
        #if error print help
        #print(e)
        #log_event("[!] No valid command provided. Use 'start', 'stop', or 'restart'.", 1, None, True)
        parser.print_help()
