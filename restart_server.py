##restart_server.py responsible for handling stop/start/restart abilities for artillery
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
        else:
            #print("The current user is root.")
            from src.core import *
    #########################################################
    class SVCMgr():
        def __init__(self):
            #this is for when launching as standard user on windows it will fail here
            #because this is not imported as regular user i catch it so you don't see it
            #its meaningless
            
            if is_posix():
                self.pid = os.getpid()
            log_event(f"[*] Artillery Service controller starting with pid: {str(self.pid)}", 0, None, True)
        #
        def pause_console(self):
            """
            Pauses console strategically used mostly because of when launched as a standard user
            """
            pause = input("[*] Press return to continue")        
        #
        def is_service_active(self)->tuple[bool,str,str]:
            '''
            checks to see if process is running already using wmi or subprocess.Returns a tuple of bool,pid,msg
            '''
            if is_windows():
                try: #some times this is wrong and returns incorrect pid causing fuction to fail
                    #it finds pythons pid instead. i use this to find window
                    if win32gui.FindWindow('ConsoleWindowClass', 'Artillery - Advanced Threat Detection'):
                        hwnd = win32gui.FindWindow('ConsoleWindowClass', 'Artillery - Advanced Threat Detection')
                        threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
                        #i compare the values from this function and pid.txt if diiferent use pid.txt
                        txt_id = []
                        with open(file=settings.get_config('global',"PIDFILE"),mode='r',encoding='utf-8') as pidtxt:
                            for line in pidtxt:
                                txt_id.append(line)
                        if pid == int(txt_id[0]):
                            #use pid
                            pass
                        else:
                            #use pid.txt
                            pid = str(txt_id[0])
                        #return a string to use with taskkill
                        return (True,str(pid),f"[*] Service is running with pid of: {str(pid)}")
                    else:
                        return (False,"0","[*] Service is not running.")
                except win32gui.error as err:
                    pass     
            if is_posix():
                try:
                    proc = subprocess.Popen(
                        "ps -A x | grep artillery", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    pid, err = proc.communicate()
                    pid = [int(x.strip()) for line in pid.split()
                        for x in line.split() if int(x.isdigit())]
                    if len(pid) > 0:
                        return (True, str(pid[0]), "[*] Service is running")
                    else:
                        return (False, "0", "[*] Service is not running")
                except Exception as e:
                    log_event(f"[*] Error occurred while checking status: {str(e)}", 2, None, True)
                    return (False, "0", "[*] Error occurred while checking status")
        #
        def start(self):
            """
            Starts artillery binary
            """
            if is_windows():
                log_event("[*] Trying to start Artillery.", 0, None, True)
                #check to see if we are already running if so
                #exit and do not try to start a new instance
                is_runninig = self.status()
                service_running = is_runninig[0]
                service_msg = is_runninig[1]
                if service_running is True:
                    #if we are already running then just exit
                    log_event(service_msg, 0, None, True)
                    sys.exit()
                else:
                    #if not running then start it
                    INSTALL_PATH = settings.get_config('global','APP_PATH')
                    try:
                        executable = os.path.join(INSTALL_PATH, "Artillery.py")
                        subprocess.call(['cmd', '/C', 'python', executable],shell=True,creationflags=subprocess.DETACHED_PROCESS,timeout=3)
                    except subprocess.TimeoutExpired as a:
                        #pass on time out we are aware
                        pass
                    finally:
                        #5 secs is more then enough 
                        #time to wait to verify it started
                        service_check = self.status()
                        service_running = service_check[0]
                        service_pid = service_check[1]
                        service_msg = service_check[2]
                        if service_running is True:
                            log_event(service_msg, 0, None, True)
                        else:
                            log_event(service_msg, 1, None, True)
                self.pause_console()
            if is_posix():
                #should we use the service files we installed? gives us start/stop/restart/status already 
                log_event("[*] Attempting to find Artillery service", 0, None, True)
                if os.path.isfile("/var/artillery/artillery.py"):
                    log_event("[*] Starting Artillery server process...", 0, None, True)
                    subprocess.Popen(["python3", "/var/artillery/artillery.py", "&"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
                else:
                    log_event("[!] Artillery server script not found at /var/artillery/artillery.py", 1, None, True)
        #       
        def stop(self):
            '''
            stops main exe by using os.kill()
            '''
            if is_windows():
                #log_event("[*] Attempting to stop service", 0, None, True)
                service_status = self.status()
                service_running = service_status[0]
                service_pid = str(service_status[1])
                service_msg = str(service_status[2])
                #check to see if service is running if false just quit
                if service_running is False:
                    log_event(service_msg, 0, None, True)
                    sys.exit()
                else:
                    log_event(service_msg, 0, None, True)
                    try:
                        msg = f"[*] Killing Artillery with processID of: {service_pid}"
                        #logs.info(msg)
                        log_event(msg, 0, None, True)
                        try:
                            #works no errors but still not clean find a better way?
                            os.kill(int(service_pid),signal.SIGTERM)
                            log_event("[*] Artillery process killed successfully.", 0, None, True)
                            return
                        except SystemError as e:
                            log_event(f"[*] SystemError occurred: {str(e)}", 2, None, True)
                            return
                    except WindowsError as werr:
                        log_event(f"[*] WindowsError occurred: {str(werr)}", 2, None, True)
                        return
                self.pause_console()
            if is_posix():
                #this is the kill_artillery func from core.py
                log_event("[*] Attempting to stop Artillery service", 0, None, True)
                try:
                    proc = subprocess.Popen(
                        "ps -A x | grep artiller[y]", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    pid, err = proc.communicate()
                    pid = [int(x.strip()) for line in pid.split()
                        for x in line.split() if int(x.isdigit())]
                    log_event("Killing the old Artillery process...",0,None,True)
                    for i in pid:
                        os.kill(i, signal.SIGKILL)
                    log_event("[*] Artillery process killed successfully.", 0, None, True)
                except Exception as e:
                    log_event(f"[*] Error occurred while trying to stop Artillery: {str(e)}", 2, None, True)
        #
        def status(self)->tuple[bool,str,str]:
            '''
            Checks to see if service is running. Returns a tuple of bool,msg,pid

            '''
            is_active = self.is_service_active()
            active = is_active[0]
            #
            if active == True:
                return (True, str(is_active[1]), str(is_active[2]))
            elif active == False or None:
                return (False, str(is_active[1]), str(is_active[2]))
        #
        def restart(self):
            """
            Restarts the artillery service.
            """
            if is_windows():
                log_event("[*] Attempting to restart Artillery service", 0, None, True)
                status = self.status()
                if status[0] is True:
                    self.stop()
                    time.sleep(5)
                    #sleep for a sec to allow process to close
                    #check to see if it is still running
                    status = self.status()
                    if status[0] is False:
                        #then start it again
                        #log_event(f"{status[1]}, starting it now.", 0, None, True)
                        self.start()
                else:
                    #log_event(f"{status[1]}, starting it now.", 0, None, True)
                    self.start()
                    #sleep for a sec to allow process to start
                    time.sleep(5)
                    #check to see if it started
                    status = self.status()
                    if status[0] is True:
                        log_event(f"{status[2]}", 0, None, True)
                    else:
                        log_event(f"{status[2]}", 1, None, True)
                
            if is_posix():
                log_event("[*] Attempting to restart Artillery service", 0, None, True)
                self.stop()
                time.sleep(5)  # wait for the process to close
                self.start()
    #setup our parser to accept cmd line options.
    #for now it is basic more options wil be added over time.
    service = SVCMgr()
    parser = argparse.ArgumentParser(prog='restart',usage='%(prog)s [options]',description='Restart manager for Artillery',add_help=True)
    subparser = parser.add_subparsers()
    start_parser = subparser.add_parser(name='start', help='starts artillery process.')
    start_parser.add_argument('start', action='store_true')
    start_parser.set_defaults(function=service.start)
    stop_parser = subparser.add_parser(name='stop', help='stops artillery process.')
    stop_parser.add_argument("stop", action='store_true')
    stop_parser.set_defaults(function=service.stop)
    restart_parser = subparser.add_parser(name='restart', help='restarts artillery process.')
    restart_parser.add_argument("restart", action='store_true')
    restart_parser.set_defaults(function=service.restart)
    args = parser.parse_args()
    try:
        if hasattr(args, 'function'):
            args.function()
    except Exception as e:
        #if error print help
        #print(e)
        log_event("[!] No valid command provided. Use 'start', 'stop', or 'restart'.", 1, None, True)
        parser.print_help()
   