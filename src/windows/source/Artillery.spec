# -*- mode: python -*-
print("##########################################################################################")
print("[*] Importing some stuff for the build to be easier.....")
import os
from os import listdir
from os.path import isfile, join
import subprocess
import time
import sys

def get_time():
    '''returns local time for use in script'''
    now = time.localtime()
    ascii = time.asctime(now)
    return(ascii)
#
CHANGELOG = 'changelog.txt'
def write_changelog():
    '''creates changelog or appends to existing any changes
    you wish to include. useful to keeptrack of small incremental
    changes and specifics that can be included in main changelog'''
    answer = input("[?] Would like to include changes for this build?: ")
    if (answer.lower() in ["yes", "y"]):
        line = input("[*] please give a brief description of changes: ")
        with open(CHANGELOG, 'a') as changes:
            line = line.strip()
            changes.write("* "+line+"\n")
        return
    elif (answer.lower() in ["no", "n"]):
        print("[*] Not including changes")
        return
    else:
        return
# 
TIMENOW =get_time()
print("[*] Build started @ "+ TIMENOW)   
print("[*] Done with imports.....")
print("#########################################################################################")
print("[*] Setting up variables.....")
block_cipher = None
HOME = os.getcwd()
FINALBUILD = HOME+"\\finalbuild"
CLIENTFINAL = HOME+'\\finalbuild\\Artillery'
CLIENTICONS = CLIENTFINAL+'\\src\\icons'
CLIENTWIN = CLIENTFINAL+'\\src\\windows'
CLIENTDATABASE = CLIENTFINAL+'\\database'
CLIENTLOGS = CLIENTFINAL+'\\logs'
CLIENTREADME = CLIENTFINAL+'\\readme'
SOURCECODE = CLIENTWIN+'\\source'
HOOKSPATH = SOURCECODE+'\\hooks'
SOURCEREADME = SOURCECODE+'\\readme'
SOURCEDIST = SOURCECODE+'\\dist'
SOURCELOGS = SOURCECODE+'\\logs'
SOURCEDATABASE = SOURCECODE+'\\database'
SOURCECODESRC = SOURCECODE+'\\src'
ICONSRCDIR = SOURCECODESRC+'\\icons'
WINSRCDIR = SOURCECODESRC+'\\windows'
CLIENTSOURCE = ['Artillery.py','remove_ban.py','restart_server.py']
ICONSOURCE = ['avatar.jpg','window_icon.png', 'bd_icon_OiD_icon.ico','toast_events_icon.ico']
HOOKFILE = HOME+'\\hooks\\hook-win10toast.py'
READMEFILE = 'README.md'
SPECFILE = 'Artillery.spec'
BUILDUI = False
BUILDFILE = 'build_instructions.txt'
AUTOSTARTFILE = 'login.bat'
ARTILLERY_EXE = 'Artillery.exe'
CLIENT_FILES = ['Artillery.exe', 'Restart.exe', 'Unban.exe']
#create all final folders if not present####################################################
if os.path.exists(FINALBUILD):
    print("[*] finalbuild path is present.....")
else:
    print("[*] finalbuild path not present creating.....")
    os.makedirs(HOOKSPATH)
    os.makedirs(SOURCEREADME)
    os.makedirs(SOURCEDIST)
    os.makedirs(SOURCEDATABASE)
    os.makedirs(SOURCELOGS)
    os.makedirs(WINSRCDIR)
    os.makedirs(ICONSRCDIR)
    #os.makedirs(CLIENTFINAL)
    os.makedirs(CLIENTICONS)
    #os.makedirs(CLIENTWIN)
    os.makedirs(CLIENTDATABASE)
    os.makedirs(CLIENTLOGS)
    os.makedirs(CLIENTREADME)
#
def get_filenames(filepath):
    '''returns filenames in a given path'''
    dirname = HOME+ filepath
    filenames = [f for f in listdir(dirname) if isfile(join(dirname, f))]
    return filenames
#
def create_source_zip():
    '''creates zip archive of sourcecode dir'''
    print("[*] making source.zip.....")
    try:
        if os.path.exists(SOURCECODE):
            os.chdir(CLIENTWIN)
            subprocess.run(['python', '-m','zipfile', '-c', 'source.zip', SOURCECODE])
            time.sleep(2)
            subprocess.run(['cmd', '/C', 'copy', 'source.zip', CLIENTWIN],stdout=subprocess.DEVNULL)
            os.chdir(HOME)     
    except FileNotFoundError:
        raise
#
def write_source_code():
    '''copies compiled\src files to finalbuild folder'''
    if os.path.isfile('README.md'):
        print("[*] Copying documentation files.....")
        subprocess.run(['cmd', '/C', 'copy', READMEFILE, SOURCECODE],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', READMEFILE, CLIENTFINAL],stdout=subprocess.DEVNULL)
        rdmefldr = get_filenames('\\readme')
        os.chdir('readme')
        for item in rdmefldr:
            subprocess.run(['cmd', '/C', 'copy', item, CLIENTREADME],stdout=subprocess.DEVNULL)
            subprocess.run(['cmd', '/C', 'copy', item, SOURCEREADME],stdout=subprocess.DEVNULL)
        print("[*] Done.....")
    os.chdir(HOME)
    if os.path.isfile('build_instructions.txt'):
        print("[*] Copying build instructions file.....")
        subprocess.run(['cmd', '/C', 'copy', BUILDFILE, SOURCECODE],stdout=subprocess.DEVNULL)
        print("[*] Done.....")
    if os.path.isfile('login.bat'):
        print("[*] Copying run on login file.....")
        subprocess.run(['cmd', '/C', 'copy', AUTOSTARTFILE, CLIENTFINAL],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', AUTOSTARTFILE, SOURCECODE],stdout=subprocess.DEVNULL)
        print("[*] Done.....")  
    if os.path.isfile('Artillery.spec'):
        print("[*] Copying spec file.....")
        subprocess.run(['cmd', '/C', 'copy', SPECFILE, SOURCECODE],stdout=subprocess.DEVNULL)
        time.sleep(1)
        print("[*] Done.....")
    if os.path.isfile('config'):
        print("[*] Copying config/banlist files.....")
        subprocess.run(['cmd', '/C', 'copy', 'config', CLIENTFINAL],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', 'banlist.txt', CLIENTFINAL],stdout=subprocess.DEVNULL)
        time.sleep(2)
        subprocess.run(['cmd', '/C', 'copy', 'config', SOURCECODE],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', 'banlist.txt', SOURCECODE],stdout=subprocess.DEVNULL)
        print("[*] Done...")
    time.sleep(1)
    if os.path.isfile('Artillery.py'):
        print("[*] Copying artillery/restart/removeban source.....")
        for item in CLIENTSOURCE:
            subprocess.run(['cmd', '/C', 'copy', item, SOURCECODE],stdout=subprocess.DEVNULL)
        print("[*] Done.....")
    time.sleep(1)
    if os.path.isfile('src\\core.py'):
        print("[*] Copying core files source.....")
        srcdirfiles= get_filenames('\\src')
        os.chdir('src')
        for item in srcdirfiles:
            subprocess.run(['cmd', '/C', 'copy', item, SOURCECODESRC],stdout=subprocess.DEVNULL)
        print("[*] Done.....")
    os.chdir(HOME)
    time.sleep(1)
    if os.path.isfile('src\\icons\\avatar.jpg'):
        print("[*] Copying icons.....")
        icons = get_filenames('\\src\\icons')
        os.chdir('src\icons')
        for item in icons:
            subprocess.run(['cmd', '/C', 'copy', item, ICONSRCDIR],stdout=subprocess.DEVNULL)
            subprocess.run(['cmd', '/C', 'copy', item, CLIENTICONS],stdout=subprocess.DEVNULL)
        print("[*] Done.....")
    os.chdir(HOME)
    if os.path.isfile('src\\windows\\ArtilleryEvents.dll'):
        print("[*] copying windows files.....")
        os.chdir('src\windows')
        #this adds files to finalbuild\artillery\src\windows folder
        subprocess.run(['cmd', '/C', 'copy', 'ArtilleryEvents.dll', CLIENTWIN],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', 'WindowsTODO.txt', CLIENTWIN],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', 'ArtilleryEvents.reg', CLIENTWIN],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', 'dll_reg.bat', CLIENTWIN],stdout=subprocess.DEVNULL)
        #and also to project source dir
        subprocess.run(['cmd', '/C', 'copy', 'ArtilleryEvents.dll', WINSRCDIR],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', 'WindowsTODO.txt', WINSRCDIR],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', 'ArtilleryEvents.reg', WINSRCDIR],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', 'dll_reg.bat', WINSRCDIR],stdout=subprocess.DEVNULL)
        print("[*] Done.....")   
    os.chdir(HOME)
    if os.path.isfile(HOOKFILE):
        print("[*] Copying hook file.....")
        os.chdir('hooks')
        subprocess.run(['cmd', '/C', 'copy', HOOKFILE, HOOKSPATH],stdout=subprocess.DEVNULL)
        print("[*] Done.....")
    os.chdir(HOME)
    if os.path.isfile("database\\temp.database"):
        print("[*] Copying database file.....")
        os.chdir('database')
        subprocess.run(['cmd', '/C', 'copy', 'temp.database', SOURCEDATABASE],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', 'temp.database', CLIENTDATABASE],stdout=subprocess.DEVNULL)
        print("[*] Done.....")
    os.chdir(HOME)
    if os.path.isfile("logs\\alerts.log"):
        print("[*] Copying log file.....")
        os.chdir('logs')
        subprocess.run(['cmd', '/C', 'copy', 'alerts.log', SOURCELOGS],stdout=subprocess.DEVNULL)
        subprocess.run(['cmd', '/C', 'copy', 'alerts.log', CLIENTLOGS],stdout=subprocess.DEVNULL)
        print("[*] Done.....")
    os.chdir(HOME)
    print("[*] Switching to dist folder.....")
    time.sleep(2)
    os.chdir("dist")
    if os.path.isfile(ARTILLERY_EXE):
        print("[*] Found the client files continuing.....")
        for file in CLIENT_FILES:
            #SET FILE VERSION INFO AS SEEN IN PROPERTIES-->details of exe
            subprocess.run(['cmd', '/C', 'pyi-set_version', file+'_ver_info.txt',file],stdout=subprocess.DEVNULL)   
        for file in CLIENT_FILES:
            subprocess.run(['cmd', '/C', 'copy', file+'_ver_info.txt', SOURCEDIST],stdout=subprocess.DEVNULL)
            subprocess.run(['cmd', '/C', 'copy', file, CLIENTFINAL],stdout=subprocess.DEVNULL)
    time.sleep(2)
    os.chdir(HOME)
    return
#
bin_files = []
win_dll_path = ['C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLS\\x64']
pyqt5_dll_path = [HOMEPATH + '\\pyqt5\\qt\\bin\\']
hooks_dir = [HOME+'\\hooks']
print("[*] Done setting up variables.....")
print("############################################################################################")
print("[*] Setting up file data.....")
UI_PYFILES =[('ArtilleryUI.py', '.')]
CONSOLE_PY_FILES = [('Artillery.py','.')]
SRCFILES = [('src\\*.py', 'src\\')]
WINDOWSFILES = [('src\\windows\\*.txt','src\\windows'),('src\\windows\\*.bat', 'src\\windows')]
icons = [('src\\icons\\*.png', 'src\\icons')]
bin_icon =[('src\\icons\\*.ico', 'src\\icons'),
            ('src\\windows\\ArtilleryEvents.reg', 'src\\windows'),
            ('src\\windows\\*.dll', 'src\\windows')
            ]
print("[*] Done with file data.....")
print("############################################################################################")
if BUILDUI: #file is not ready for release yet so this will return false for now
    print("[*] Building ArtilleryUI.exe")
    ui = Analysis(['ArtilleryUI.py'],
                pathex= win_dll_path + pyqt5_dll_path,
                binaries=bin_icon,
                datas=UI_PYFILES+icons+WINDOWSFILES+SRCFILES,
                hiddenimports=['resource', 'smtplib', 'logging.handlers', 'win32com', 'win32com.shell', 'win32com.shell.shell', 'win32com.shell.shellcon.', 'win32process', 'win32security', 'win32event'],
                hookspath=hooks_dir,
                runtime_hooks=[],
                excludes=[],
                win_no_prefer_redirects=False,
                win_private_assemblies=False,
                cipher=block_cipher,
                noarchive=False)
    ui_pyz = PYZ(ui.pure, ui.zipped_data,
                cipher=block_cipher)
    ui_exe = EXE(ui_pyz,
            ui.scripts,
            ui.binaries,
            ui.zipfiles,
            ui.datas,
            icon = ['src\\icons\\toast_events_icon.ico'],
            name='ArtilleryUI',
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            runtime_tmpdir=None,
            console=False )
    print("[!] Done building ArtilleryUI.exe")
#print("###############################################################################")
print("[*] Building Artillery.exe")
console = Analysis(['Artillery.py'],
             pathex= win_dll_path,
             binaries=bin_icon,
             datas=CONSOLE_PY_FILES+icons+WINDOWSFILES+SRCFILES,
             hiddenimports=['resource', 'smtplib', 'email.mime', 'logging.handlers', 'win32com', 'win32com.shell', 'win32com.shell.shell', 'win32com.shell.shellcon.', 'win32process', 'win32security', 'win32event'],
             hookspath=hooks_dir,
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
console_pyz = PYZ(console.pure, console.zipped_data,
             cipher=block_cipher)
console_exe = EXE(console_pyz,
          console.scripts,
          console.binaries,
          console.zipfiles,
          console.datas,
          icon = ['src\\icons\\toast_events_icon.ico'],
          name='Artillery',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
print("[*] Done building Artillery.exe")
print("########################################################################################")
print("[*] Building Restart.exe")
restart = Analysis(['restart_server.py'],
             pathex= win_dll_path,
             binaries=bin_icon,
             datas=icons,
             hiddenimports=['resource', 'smtplib', 'email.mime', 'logging.handlers', 'win32com', 'win32com.shell', 'win32com.shell.shell', 'win32com.shell.shellcon.', 'win32process', 'win32security', 'win32event'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
restart_pyz = PYZ(restart.pure, restart.zipped_data,
             cipher=block_cipher)
restart_exe = EXE(restart_pyz,
          restart.scripts,
          restart.binaries,
          restart.zipfiles,
          restart.datas,
          icon = ['src\\icons\\toast_events_icon.ico'],
          name='Restart',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
print("[*] Done building Restart.exe")
print("########################################################################################")
print("[*] Building UnBan.exe")
remove = Analysis(['remove_ban.py'],
             pathex= win_dll_path,
             binaries=bin_icon,
             datas=icons,
             hiddenimports=['resource', 'smtplib', 'email.mime', 'logging.handlers', 'win32com', 'win32com.shell', 'win32com.shell.shell', 'win32com.shell.shellcon.', 'win32process', 'win32security', 'win32event'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
remove_pyz = PYZ(remove.pure, remove.zipped_data,
             cipher=block_cipher)
remove_exe = EXE(remove_pyz,
          remove.scripts,
          remove.binaries,
          remove.zipfiles,
          remove.datas,
          icon = ['src\\icons\\toast_events_icon.ico'],
          name='UnBan',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
print("[*] Done building UnBan.exe")
print("###############################################################")
print("[*] Grabbing source files.....")
write_changelog()
write_source_code()
print("[*] Source files copied.....")
print("################################################################")
os.chdir(HOME)
create_source_zip()
TIMENOW = get_time()
#print("[*] "+TIMENOW)
print("[*] Project Build finished @ "+ TIMENOW)