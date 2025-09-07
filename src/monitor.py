# all standard python imports such as sys,os and the like are in core.py no need to
 #include again. only add libraries that are not a part of std libs.aka neeed to be pip installed
#############################
#
# This one monitors file system integrity
#these wil be merged to one function in future
#
#############################
from .core import is_posix,is_windows,settings,log_event
from .email_handler import *

monitor_email_logger = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())
#
if is_windows():
    # left to show imports
    # from pathlib import PureWindowsPath
    # import win32file
    # import win32con
    from .core import threading,PureWindowsPath,win32file,win32con,os,re
    def watch_directory_for_changes(Fpath,k=None):

        '''this will monitor a folder path of your choosing and notify on
        changes this will only work on Windows systems
    '''
        #will add in more logic here
        ACTIONS = {
            1 : "Created",
            2 : "Deleted",
            3 : "Updated",
            4 : "Renamed from something",
            5 : "Renamed to something"
        }
    #
        FILE_LIST_DIRECTORY = 0x0001
    #without FILE_SHARE_DELETE on the CreateFile call, the directory can't be deleted or renamed while it's being watched
    #removing FILE_SHARE_DELETE prevents renaming or deleting ?immutable maybe kinda?
        path_to_watch = Fpath
        hDir = win32file.CreateFile (
        path_to_watch,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None
        )
        while 1:
        #
        # ReadDirectoryChangesW takes a previously-created
        # handle to a directory, a buffer size for results,
        # a flag to indicate whether to watch subtrees and
        # a filter of what changes to notify.
        #
        # up
        # the buffer size to be sure of picking up all
        # events when a large number of files were
        # deleted at once.
        #
            results = win32file.ReadDirectoryChangesW (
            hDir,
            1024,
            True,
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
            win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
            win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
            win32con.FILE_NOTIFY_CHANGE_SIZE |
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
            win32con.FILE_NOTIFY_CHANGE_SECURITY,
            None,
            None
            )

            for action, file in results:
                full_filename = os.path.join(path_to_watch, file)
                alert = f'[!!] Monitor Alert: {full_filename} {ACTIONS.get (action, "Unknown")}'
                log_event(alert,0,None,True)

if is_posix():
    from .core import time,threading,hashlib,os,re,subprocess
    def monitor_system(time_wait):
        # total_compare is a tally of all sha512 hashes
        total_compare = ""
        # what files we need to monitor
        check_folders = settings.get_config("current","MONITOR_FOLDERS")
        #check_folders = read_config("MONITOR_FOLDERS")
        # split lines
        check_folders = check_folders.replace('"', "")
        check_folders = check_folders.replace("MONITOR_FOLDERS=", "")
        check_folders = check_folders.rstrip()
        check_folders = check_folders.split(",")
        # cycle through tuple
        for directory in check_folders:
            time.sleep(0.1)
            # we need to check to see if the directory is there first, you never
            # know
            if os.path.isdir(directory):
                # check to see if theres an include
                exclude_check = settings.get_config("current","EXCLUDE")
                #exclude_check = read_config("EXCLUDE")
                match = re.search(exclude_check, directory)
                # if we hit a match then we need to exclude
                if not directory in exclude_check:
                    # this will pull a list of files and associated folders
                    for path, subdirs, files in os.walk(directory):
                        for name in files:
                            filename = os.path.join(path, name)
                            # check for sub directory exclude paths
                            if not filename in exclude_check:
                                # some system protected files may not show up, so
                                # we check here
                                if os.path.isfile(filename):
                                    try:
                                        fileopen = open(filename, "rb")
                                        data = fileopen.read()
                                    except:
                                        pass
                                    hash = hashlib.sha512()
                                    try:
                                        hash.update(data)
                                    except:
                                        pass
                                    # here we split into : with filename :
                                    # hexdigest
                                    compare = filename + ":" + hash.hexdigest() + "\n"
                                    # this will be all of our hashes
                                    total_compare = total_compare + compare

        # write out temp database
        temp_database_file = open("/var/artillery/database/temp.database", "w")
        temp_database_file.write(total_compare)
        temp_database_file.close()

        # once we are done write out the database, if this is the first time,
        # create a database then compare
        if not os.path.isfile("/var/artillery/database/integrity.database"):
            # prep the integrity database to be written for first time
            database_file = open("/var/artillery/database/integrity.database", "w")
            database_file.write(total_compare)
            database_file.close()

        # hash the original database
        if os.path.isfile("/var/artillery/database/integrity.database"):
            database_file = open("/var/artillery/database/integrity.database", "r")
            try:
                database_content = database_file.read().encode('utf-8')
            except:
                database_content = database_file.read()
            if os.path.isfile("/var/artillery/database/temp.database"):
                temp_database_file = open(
                    "/var/artillery/database/temp.database", "r")
                try:
                    temp_hash = temp_database_file.read().encode('utf-8')
                except:
                    temp_hash = temp_database_file.read()

                # hash the databases then compare
                database_hash = hashlib.sha512()
                database_hash.update(database_content)
                database_hash = database_hash.hexdigest()

                # this is the temp integrity database
                temp_database_hash = hashlib.sha512()
                temp_database_hash.update(temp_hash)
                temp_database_hash = temp_database_hash.hexdigest()
                # if we don't match then there was something that was changed
                if database_hash != temp_database_hash:
                    # using diff for now, this will be rewritten properly at a
                    # later time
                    compare_files = subprocess.Popen(
                        "diff /var/artillery/database/integrity.database /var/artillery/database/temp.database", shell=True, stdout=subprocess.PIPE)
                    output_file = compare_files.communicate()[0]
                    if output_file == "":
                        # no changes
                        pass

                    else:
                        
                        subject = "[!] Artillery has detected a change. [!]"
                        output_file = "********************************** The following changes were detected at %s **********************************\n" % (
                            str(datetime.datetime.now())) + str(output_file) + "\n********************************** End of changes. **********************************\n\n"

        # put the new database as old
        if os.path.isfile("/var/artillery/database/temp.database"):
            shutil.move("/var/artillery/database/temp.database",
                        "/var/artillery/database/integrity.database")

def monitor_start():
    '''
    Function that starts folder monitor routine depending on platform
    '''
    if is_windows():
        '''Starts Windows folder watch routine for specified directories. for now
    it tells when something happens. will work in more logic later'''
        try:
            paths_to_watch = settings.get_config("current","MONITOR_FOLDERS")
            paths_to_watch = paths_to_watch.replace('"', "")
            paths_to_watch = paths_to_watch.replace(" ", "")
            paths_to_watch = paths_to_watch.replace("MONITOR_FOLDERS=", "")
            paths_to_watch = paths_to_watch.strip(" ")
            paths_to_watch = paths_to_watch.split(",")
        except BaseException as e:
            #add exception log here
            log_event(e.args,2,None,False)
        # cycle through tuple
        for directory in paths_to_watch:
            path = PureWindowsPath(directory)
            try:
                log_event(f"[*] Starting Folder Monitor on path: {path}",0,None,True)
                #have to pass None here start_new_thread doesn't like when u only give 1 var
                #on function it only watches the first entry if u don't
                k = None
                threading.Thread(group=None,target=watch_directory_for_changes,args=(str(path), k),daemon=True).start()
                #thread.start_new_thread(watch_directory_for_changes, (str(path), k))
            except Exception as err:
                log_event(err,2,None,False)
    if is_posix():
        '''Starts Linux folder watch routine for specified directories.'''
        # start the monitoring
        time_wait = settings.get_config("current","MONITOR_FREQUENCY")
        # loop forever
        while 1:
            threading.Thread(group=None,target=monitor_system,args=(time_wait),daemon=True).start()
            #thread.start_new_thread(monitor_system, (time_wait,))
            time_wait = int(time_wait)
            time.sleep(time_wait)
