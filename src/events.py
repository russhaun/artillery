#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Events.py
#
#  Copyright 2018 Russ Haun
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
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
#
import os
import sys
from win32evtlogutil import ReportEvent, AddSourceToRegistry, RemoveSourceFromRegistry
from win32api import GetCurrentProcess
from win32security import GetTokenInformation, TokenUser, OpenProcessToken
from win32con import TOKEN_READ
import win32evtlog
#
def is_windows():
    return os.name == "nt"
def is_posix():
    return os.name == "posix"
#
#This script assumes dll is already registered with system working on check
#and routine to install
#set some constants that we will use
mymsgDLL = "C:\\Program Files (x86)\\Artillery\\src\\windows\\ArtilleryEvents.dll"
AppName = "Artillery"
data = "Application\0Data".encode("ascii")
#category is always one for now
category = 1
process = GetCurrentProcess()
token = OpenProcessToken(process, TOKEN_READ)
my_sid = GetTokenInformation(token, TokenUser)[0]
myType = win32evtlog.EVENTLOG_INFORMATION_TYPE
#Left this here for reference
"""Report an event for a previously added event source."""
#ReportEvent(appName, eventID, eventCategory = 0, eventType=win32evtlog.EVENTLOG_ERROR_TYPE, strings = None, data = None, sid=None):
#
#below are as defined in the "dll" look @ included .mc file for message contents
#descr = 'ARTILLERY_START'
def ArtilleryStartEvent():
        eventID = 100
        ReportEvent(AppName, eventID, eventCategory=category, eventType=myType, data=data, sid=my_sid)
#
#descr = 'ARTILLERY_STOP'
def ArtilleryStopEvent():
        eventID = 101
        ReportEvent(AppName, eventID, eventCategory=category, eventType=myType, data=data, sid=my_sid)
#
#descr = 'HONEYPOT_ATTACK'
def HoneyPotEvent(ip):
        HPip = ip
        eventID = 200
        myType = win32evtlog.EVENTLOG_WARNING_TYPE
        ReportEvent(AppName, eventID, eventCategory=category, eventType=myType, strings=HPip, data=data, sid=my_sid)
#below functions are not implemented yet. these will be included in setup.py when they are
def InstallDLL():
        """Add a source of messages to the event log."""
        #AddSourceToRegistry(appName = AppName, msgDLL = mymsgDLL, eventLogType = "Application", eventLogFlags = None):
        pass
#
#
def UninstallDLL():
        """Removes a source of messages from the event log."""
        #RemoveSourceFromRegistry(appName = AppName, eventLogType = "Application"):
        pass

#
#these are used during testing leave commented for now
#ArtilleryStartEvent()
#ArtilleryStopEvent()
#ip='127.0.0.1'
#HoneypotEvent(ip)

