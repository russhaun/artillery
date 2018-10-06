'''This script is a collection of functions for manipulting the windows firewall.it creates group
and takes an input file and creates several lists to work with. it monitors file for changes
and updates accordingly.'''
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
# Only tested with powershell v5!!!!!!!!. do not know if it will work on earlier versions
# eventid 4103 in powershell/Operational will show these event when triggered
# eventid 2005 in windowsfirewall with advanced security/firewall will also be shown
# if you have powershell transcription enabled you will also see the commands there as well
#
import subprocess
import datetime
import os
import time
import threading
import sys
from core import write_log
############################################################################################################

def is_posix():
    return os.name == "posix"
#
#
def is_windows():
    return os.name == "nt"
#
#
def get_config(cfg):
    ''' this function returns various lists used in operation of this script'''
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
seed_file = 'fwseed.txt'
blocked_hosts =[]
seed_temp = []
#firewall_hosts = program_files + "\\Artillery\\src\\windows\\firewall_rules.txt"
firewall_hosts = 'firewall_rules.txt'
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
    '''create timestamp on banlist.txt to reference for updates'''
    filename = ip_file
    time_stamp = datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)
    global last_modified_time
    last_modified_time = time_stamp
#
#
def create_firewall_list():
    '''create initial list 'blocked_hosts' from banlist.txt and
    set timestamp on file for use with update function '''
    #
    alert = "[*] FIREWALL: creating firewall list.........."
    write_log(alert)
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
    write_log(alert)
#
#
def save_firewall_list():
    '''writes out list 'firewall_hosts' to save and reload after first use. saves file as 'firewall_rules.txt'  '''
    #with open(firewall_hosts) as current_rules: 
    pass
#
#
def return_ips():
    '''return list of ips formatted as a string to use with firewall'''
    hosts = []
    with open(firewall_hosts) as ips:
        for line in ips:
        #grab all ips and create new list temporarily
            line = line.strip()
            hosts.append(line)
    ips.close()
    hosts.sort()
    fwlist = hosts
    #make our string for firewall command
    fwstring = ', '.join(map(str, fwlist))
    return(fwstring)
        

def firewall_update():
    ''' poll @ intervals with a timer at bottom of script to see if any changes
    too main blocklist. If file timestamps have changed trigger update from created list 'blocked_hosts'
    This will cause the whole list to be processed has potential to increase log size dramatically based on list size'''
    filename = ip_file
    modified_time = datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)
    global new_modified_time
    new_modified_time = modified_time
    #if time stamps differ begin update
    if (new_modified_time > last_modified_time):
        alert = "[!] FIREWALL: Changes detected to banlist.txt updating rules.........."
        print(alert)
        write_log(alert)
        alert = "[*] FIREWALL: {} was last modified on {:%Y-%m-%d %H:%M:%S}".format(filename, last_modified_time)
        write_log(alert)
        #set a new timestamp
        get_banlist_timestamp()
        #pull up our list    
        x = return_ips()
        alert = "[*] FIREWALL: Adding rules to windows firewall..........."
        write_log(alert)
        #below string equates to doing this from powershell
        # powershell.exe -ExecutionPolicy Bypass Set-NetFirewallrule -DisplayName Artillery_IP_Block -Direction in -RemoteAddress <ip list> -Action block
        # unfortunatly i have to reload the whole list which will fill up logs trying to find better way
        add_rule = powershell, executionpolicy, bypass, set_new_rule, Name, "Artillery_IP_Block", Dir, 'in', Raddr, x , Act, "block"
        subprocess.Popen(add_rule)
        alert = "[*] FIREWALL: Rules updated succesfully.........."
        write_log(alert)
    else:
        alert = "[*] FIREWALL: No changes detected sleeping.........."
        write_log(alert)
#
#
def add_firewall_rule(ip):
    '''add firewall rule to host. basically just append it to our file availible "blocked_hosts.txt"
    and trigger an update. for now this list is limited to 1000 entries'''
    attackerip = ip
    t = datetime.datetime.now()
    #write out the ip to banlist this will trigger the update
    #moved this from core.py
    fileopen = open(ip_file, "r")
    data = fileopen.read()
    if ip not in data:
        filewrite = open(ip_file, "a")
        filewrite.write(ip + "\n")
        filewrite.close()
        #write out to firewall_rules.txt for firewall update
        current_list = open(firewall_hosts, "a")
        current_list.write(ip + "\n")
        current_list.close()
    #todo make check if ip is in list just not in firewall list
    #print alert and wait for update
    alert = '[*] FIREWALL: Successfully added {} to firewall list @ {:%Y-%m-%d %H:%M:%S} triggering update..........'.format(attackerip, t)
    print(alert)
    write_log(alert)
#
#
def remove_firewall_rule(ip):
    '''removes a given ip from 'firewall_rules.txt' and banlist.txt.'''
    pass
#
#
def fw_seed():
    '''grab seed ip from fwseed.txt during setup to create initial firewall rule group.
    if not it blocks all ips and some services might fail. ex: hyperv-mgmt. :('''
    with open(seed_file) as s:
        for line in s:
            #grab all ips and create new list temporarily
            line = line.strip()
            seed_temp.append(line)
    s.close()
#
#
def make_firewall_group():
    '''create intial blank group to use'''
    fw_seed()
    x = seed_temp[0]
    make_group = powershell, executionpolicy, bypass, new_firewall_group, Name, "Artillery_IP_Block", Dir, 'in', Desc, "none", Raddr, x, Act, "block"
    subprocess.Popen(make_group)
    alert = "[*] FIREWALL: group created sucessfully.........."
    write_log(alert)
#
#
def rem_firewall_group():
    '''delete group from computer'''
    del_group = powershell, executionpolicy, bypass, remove_group, Name, "Artillery_IP_Block"
    subprocess.Popen(del_group)
    alert = "[*] FIREWALL: group removed sucessfully..........."
    write_log(alert)
    print(alert)
#
#
#DO NOT disable below this line
##################################################################################
#create initial list and timestamp
create_firewall_list()
#ip = input("[*] please type ip to test: ")
#add_firewall_rule(ip)
#make_firewall_group()
#rem_firewall_group()
#
#
def FirewallUpdateTimer():
    '''This function is the heart of script after "create_firewall_list()" function is run. will setup a timer to constantly loop
     and run firewall_update() function'''
    #set timer for every 3 minutes
    try:
        interval = 30
        threading.Timer(interval, FirewallUpdateTimer).start()
        firewall_update()
    except KeyboardInterrupt:
        sys.exit()
#run
FirewallUpdateTimer()
