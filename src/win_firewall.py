
# -*- coding: utf-8 -*-
#
#  win_firewall_add.py
#
#  Copyright 2018 russhaun <>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
###############################################################################################
# after reading a given file into memory this script will monitor file for changes
# when changes are detected it will update list and force update the firewall rules. 
# currently reads in whole list each time looking for way to just append
#----------------------------------------------------------------------------------------------
# Only tested with powershell v5!!!!!!!!. do not know if it wil work on earlier versions
# eventid 4103 in powershell/Operational will show these event when triggered
# eventid 2005 in windowsfirewall with advanced security/firewall will also be shown
# if you have powershell transcription enabled you will also see the commands there as well
#
import subprocess
import datetime
import os 
import time
import threading
#from core import write_log
############################################################################################################
'''pre-defined variables used during script operation.'''
def is_posix():
    return os.name == "posix"
#
def is_windows():
    return os.name == "nt"
#
def get_config(cfg):
    firew = ['New-NetFirewallRule ', 'Set-NetFirewallrule ', 'Remove-NetFirewallRule', '-Action ', '-DisplayName ', '-Direction ', '-Description ', '-Enabled ', '-RemoteAddress']
    pshell = ['powershell.exe ', '-ExecutionPolicy ', 'Bypass ']
    if cfg == 'Firewall':
        firew.sort(reverse=True)
        return firew
    elif cfg == 'PShell':
        pshell.sort(reverse=True) 
        return pshell
    else:
        print("Config not found")
program_files = os.environ["PROGRAMFILES(X86)"]
ip_file = program_files + "\\Artillery\\banlist.txt"
blocked_hosts =[]
last_modified_time = ''
new_modified_time = ''
firewall = get_config('Firewall')
pscmd = get_config('PShell')
powershell = pscmd[0]
executionpolicy = pscmd[2]
bypass = pscmd[1]
set_new_rule = firewall[0]
new_firewall_group = firewall[2]
remove_group = firewall[1]
Raddr = firewall[3]
En = firewall[4]
Name = firewall[5]
Dir = firewall[6]
Desc = firewall[7]
Act = firewall[8]
#
#
def get_banlist_timestamp():
    '''create timestamp to reference for updates'''
    filename = ip_file
    time_stamp = datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)
    global last_modified_time
    last_modified_time = time_stamp


def write_log(alert):
    #if is_posix():
        #syslog(alert)
    #changed path to be more consistant across windows versions
    if is_windows():
        #program_files = os.environ["PROGRAMFILES(X86)"]
        if not os.path.isdir(program_files + "\\Artillery\\logs"):
            os.makedirs(program_files + "\\Artillery\\logs")
        if not os.path.isfile(program_files + "\\Artillery\\logs\\alerts.log"):
            filewrite = open(
                program_files + "\\Artillery\\logs\\alerts.log", "w")
            filewrite.write("***** Artillery Alerts Log *****\n")
            filewrite.close()
        filewrite = open(program_files + "\\Artillery\\logs\\alerts.log", "a")
        filewrite.write(alert + "\n")
        filewrite.close()


def create_firewall_list():
    '''create initial list 'blocked_hosts' from banlist.txt and
    set timestamp on file for use with update function '''
    #
    alert = "[*] FIREWALL: creating firewall list.........."
    print(alert)
    #write_log(alert) 
    with open(ip_file) as f:
        #skip header lines from banlist.txt
        for _ in range(13):
            next(f)
        for line in f:
        #grab all ips and create new list to manage
            line = line.strip()
            blocked_hosts.append(line)
    f.close()
    #set timestamp for update function
    get_banlist_timestamp()
    alert = "[*] FIREWALL: list done.........."
    print(alert)
    #write_log(alert)
       
#
def firewall_update():
    ''' poll @ intervals with a timer at bottom of script to see if any changes 
    too main blocklist. If file timestamps have changed trigger update from created list 'blocked_hosts' 
    This will cause the whole list to be processed has potential to increase log size dramatically based on list size'''
    filename = ip_file
    #print('[*] {} was last modified on {:%Y-%m-%d %H:%M:%S}'.format(filename, last_modified_time))
    modified_time = datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)
    global new_modified_time
    new_modified_time = modified_time
    #if time stamps differ begin update
    if (new_modified_time > last_modified_time):
        alert = "[!] FIREWALL: Changes detected to banlist.txt updating rules.........."
        print(alert)
        write_log(alert)
        alert = "[*] FIREWALL: {} was last modified on {:%Y-%m-%d %H:%M:%S}".format(filename, last_modified_time)
        print(alert)
        write_log(alert)
        #set a new timestamp
        get_banlist_timestamp()
        #pull up our list
        #hosts = blocked_hosts
        alert = "[*] FIREWALL: Adding rules to windows firewall..........."
        print(alert)
        #write_log(alert)
        #below string equates to doing this from powershell
        # powershell.exe -ExecutionPolicy Bypass Set-NetFirewallrule -DisplayName Artillery_IP_Block -Direction in -RemoteAddress <ip list> -Action block
        # unfortunatly i have to reload the whole list which will fill up logs trying to find better way
        add_rule= powershell, executionpolicy, bypass, set_new_rule, Name, "Artillery_IP_Block", Dir, 'in', Raddr, blocked_hosts, Act, "block"
        #subprocess.Popen(add_rule)
        #print(add_rule)
        alert = "[*] FIREWALL: Rules updated succesfully.........."
        print(alert)
        #write_log(alert)
#   
    else:
        print("[*] FIREWALL: No changes detected sleeping..........")
#
#
def add_firewall_rule(ip):
    '''add firewall rule to host. basically just append it to our list availible "blocked_hosts"
    and trigger an update'''
    attackerip = ip
    t = datetime.datetime.now()
    #for line in attackerip:
    #    line = line.strip()
    #    blocked_hosts.append(line)
    #sort hosts list
    #blocked_hosts.sort()
    #print alert and then triger update
    print('[*] FIREWALL:Successfully added {} to firewall list @ {:%Y-%m-%d %H:%M:%S} triggering update..........'.format(attackerip, t))
    #firewall_update()
#
def remove_firewall_rule(ip):
    pass
#
def make_firewall_group():
    '''create intial blank group to use'''
    make_group= powershell, executionpolicy, bypass, new_firewall_group, Name, "Artillery_IP_Block", Dir, 'in', Desc, "Default group used by Artillery to manage blocked hosts", Act, "block"
    #print(make_group)
    subprocess.Popen(make_group)
    print("[*] FIREWALL: group created sucessfully..........")
#
def rem_firewall_group():
    '''delete group from computer'''
    del_group = powershell, executionpolicy, bypass, remove_group, Name, "Artillery_IP_Block"
    subprocess.Popen(del_group)
    print("[*] FIREWALL: group removed sucessfully...........")

#below string equates to doing this from powershell
#  powershell.exe -ExecutionPolicy Bypass Set-NetFirewallrule -DisplayName Artillery_IP_Block -Direction in -Description none -RemoteAddress <ip to block> -Action block
#print('[*] {} was last modified on {:%Y-%m-%d %H:%M:%S} updating rules.....'.format(filename, new_modified_time))
#get_timestamp()
#create_firewall_list()
#firewall_update()
#DO NOT disable below this line
##################################################################################
#create initial list and timestamp
#create_firewall_list()
#ip = input("[*] please type ip to test: ")
#add_firewall_rule(ip)
#make_firewall_group()
#rem_firewall_group()
def FirewallUpdateTimer():
    '''This function is the heart of script after "create_firewall_list()" function is run. will setup a timer to constantly loop
     and run firewall_update() function'''
    #set timer for every 5 minutes
    try:
        interval = 300
        threading.Timer(interval,FirewallUpdateTimer).start()
        firewall_update()
    except KeyboardInterrupt:
        sys.exit()
#run 
#FirewallUpdateTimer()
