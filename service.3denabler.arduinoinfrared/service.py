'''
    3D Enabler [for] Arduino Infrared TV - addon for Kodi to enable 3D mode
    Copyright (C) 2016 Rob Isenberg

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
import sys
import xbmc
import xbmcgui
import xbmcaddon
import simplejson
import re
import urllib2
from xml.dom.minidom import parseString
import base64
import uuid
import select
import serial
from serial import SerialException

__addon__   = xbmcaddon.Addon()

keyMap = {
          '3D'      :'3',
          'RIGHT'   :'r',
          'LEFT'    :'l',
          'UP'      :'KEY_UP',
          'DOWN'    :'KEY_DOWN',
          'EXIT'    :'x',
          'ENTER'   :'e',
          'STR'     :'~',
          'VOL_UP'  :'v',
          'VOL_DN'  :'b',
          'VOL_DOWN':'b',
          'P200'    :'@',
          'P500'    :'%',
          'P1500'   :'!'
    }

class Settings(object):
    def __init__(self):
        self.enabled        = True
        self.pause          = True
        self.black          = True
        self.notifications  = True
        self.notifymessage  = ''
        self.authCount      = 0
        self.pollCount      = 0
        self.curTVmode      = 0
        self.newTVmode      = 0
        self.detectmode     = 0
        self.pollsec        = 5
        self.idlesec        = 5
        self.inProgress     = False
        self.inScreensaver  = False
        self.skipInScreensaver  = True
        self.addonname      = __addon__.getAddonInfo('name')
        self.icon           = __addon__.getAddonInfo('icon')
        self.sequenceBegin  = 'PAUSE,STR,3D,P500'
        self.sequenceEnd    = 'ENTER,P500,EXIT,P200,EXIT,P200,EXIT,P200,EXIT,STR'
        self.sequenceLeft   = 'LEFT,P200'
        self.sequenceRight  = 'RIGHT,P200'
        self.sequencePos    = 1
        self.pos3DSBS       = 3
        self.pos3DTAB       = 2
        self.posMemory      = True
        self.comPort        = 'COM3'
        self.baud           = 9600
        self.resetPrevented = False
        self.enableSerial   = 1
        self.load()
        
    def getSetting(self, name, dataType = str):
        value = __addon__.getSetting(name)
        if dataType == bool:
            if value.lower() == 'true':
                value = True
            else:
                value = False
        elif dataType == int:
            value = int(value)
        else:
            value = str(value)
        xbmc.log('3DIRgetSetting:' + str(name) + '=' + str(value), xbmc.LOGDEBUG)
        return value
    
    def setSetting(self, name, value):
        if type(value) == bool:
            if value:
                value = 'true'
            else:
                value = 'false'
        else:
            value = str(value)
        xbmc.log('3DIRsetSetting:' + str(name) + '=' + str(value), xbmc.LOGDEBUG)
        __addon__.setSetting(name, value)
    
    def getLocalizedString(self, stringid):
        return __addon__.getLocalizedString(stringid)
    
    def load(self):
        xbmc.log('3DIRloading Settings', xbmc.LOGINFO)
        self.enabled            = self.getSetting('enabled', bool)
        self.pause              = self.getSetting('pause', bool)
        self.black              = self.getSetting('black', bool)
        self.notifications      = self.getSetting('notifications', bool)
        self.detectmode         = self.getSetting('detectmode', int)
        self.pollsec            = self.getSetting('pollsec', int)
        self.idlesec            = self.getSetting('idlesec', int)
        self.skipInScreensaver  = self.getSetting('skipInScreensaver', bool)
        self.pos3DTAB           = self.getSetting('pos3DTAB', int)
        self.pos3DSBS           = self.getSetting('pos3DSBS', int)
        self.posMemory          = self.getSetting('posMemory', bool)
        self.sequenceBegin      = self.getSetting('sequenceBegin', str)
        self.sequenceEnd        = self.getSetting('sequenceEnd', str)
        self.sequenceLeft       = self.getSetting('sequenceLeft', str)
        self.sequenceRight      = self.getSetting('sequenceRight', str)
        self.comPort            = self.getSetting('comPort', str)
        self.baud               = self.getSetting('baud', int)
        self.resetPrevented      = self.getSetting('resetPrevented', bool)
        self.enableSerial       = 1
    
def toNotify(message):
    if len(settings.notifymessage) == 0:
        settings.notifymessage = message
    else:
        settings.notifymessage += '. ' + message

def notify(timeout = 5000):
    if len(settings.notifymessage) == 0:
        return
    if settings.notifications:
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(settings.addonname, settings.notifymessage, timeout, settings.icon))
    xbmc.log('3DIRNOTIFY: ' + settings.notifymessage, xbmc.LOGINFO)
    settings.notifymessage = ''

def getStereoscopicMode():
    query = '{"jsonrpc": "2.0", "method": "GUI.GetProperties", "params": {"properties": ["stereoscopicmode"]}, "id": 1}'
    result = xbmc.executeJSONRPC(query)
    json = simplejson.loads(result)
    xbmc.log('Received JSON response: ' + str(json), xbmc.LOGDEBUG)
    ret = 'unknown'
    if json.has_key('result'):
        if json['result'].has_key('stereoscopicmode'):
            if json['result']['stereoscopicmode'].has_key('mode'):
                ret = json['result']['stereoscopicmode']['mode'].encode('utf-8')
    # "off", "split_vertical", "split_horizontal", "row_interleaved"
    # "hardware_based", "anaglyph_cyan_red", "anaglyph_green_magenta", "monoscopic"
    return ret

def getTranslatedStereoscopicMode():
    mode = getStereoscopicMode()
    if mode == 'split_horizontal': return 1
    elif mode == 'split_vertical': return 2
    else: return 0

def stereoModeHasChanged():
    if settings.curTVmode != settings.newTVmode:
        return True
    else:
        return False

# Function to send keys
def sendKey(key):
    if settings.enableSerial: ser.write(key)

def processSequence(commandSequence):
    putOnPause = False
    keySequence = ''
    # Parse commands and execute them
    for x in commandSequence.split(','):
        thisKey = x.strip().upper()
        if thisKey in keyMap:
            xbmc.log('3DIRSending ' + thisKey + ' as Key: ' + keyMap[thisKey], xbmc.LOGDEBUG)
            keySequence = keySequence + keyMap[thisKey]
        elif thisKey[:3] == 'KEY':
            xbmc.log('3DIRSending Key: ' + thisKey, xbmc.LOGDEBUG)
            keySequence = keySequence + thisKey
        elif thisKey == 'PAUSE':
            if settings.pause:
                if xbmc.Player().isPlayingVideo():
                    if not xbmc.getCondVisibility('Player.Paused'):
                        xbmc.log('3DIRPause XBMC', xbmc.LOGDEBUG)
                        xbmc.Player().pause()
                        putOnPause = True
#        elif thisKey == 'PLAY':
#            if settings.pause:
#                if xbmc.Player().isPlayingVideo():
#                    if xbmc.getCondVisibility('Player.Paused'):
#                        xbmc.log('3DIRResume XBMC', xbmc.LOGDEBUG)
#                        if putOnPause: xbmc.Player().pause()
#        elif thisKey[:1] == 'P':
#            xbmc.log('3DIRWaiting for ' + thisKey[1:] + ' milliseconds', xbmc.LOGDEBUG)
#            xbmc.sleep(int(thisKey[1:]))
        elif thisKey == 'BLACKON':
            if settings.black:
                xbmc.log('3DIRScreen to Black', xbmc.LOGDEBUG)
                blackScreen.show()
        elif thisKey == 'BLACKOFF':
            if settings.black:
                xbmc.log('3DIRScreen from Black', xbmc.LOGDEBUG)
                blackScreen.close()
        else:
            xbmc.log('3DIRUnknown command: ' + thisKey, xbmc.LOGWARNING)
    xbmc.log('3DIRDone with sequence')
    if settings.resetPrevented: ser.open()
    sendKey(keySequence)
    test = ser.read(1) # Arduino sends '~' when done with sequence to cue playback
    if settings.resetPrevented: ser.close()
    if settings.pause:
        if xbmc.Player().isPlayingVideo():
            if xbmc.getCondVisibility('Player.Paused'):
                xbmc.log('3DIRResume XBMC', xbmc.LOGDEBUG)
                if putOnPause: xbmc.Player().pause()

def mainStereoChange():
    if stereoModeHasChanged():
        xbmc.log('3DIRStereoscopic Mode changed: curTVmode:newTVmode = ' + str(settings.curTVmode) + ':' + str(settings.newTVmode), xbmc.LOGDEBUG)
        # Action Assignment
        movement = 0
        commandSequence = ''
        if settings.newTVmode == 1:
            movement = settings.pos3DTAB - settings.sequencePos
            if settings.posMemory: settings.sequencePos = settings.pos3DTAB
        elif settings.newTVmode == 2:
            movement = settings.pos3DSBS - settings.sequencePos
            if settings.posMemory: settings.sequencePos = settings.pos3DSBS
        xbmc.log('3DIRMovement: ' + str(movement), xbmc.LOGDEBUG)
        if movement != 0:
            while movement != 0:
                if movement < 0:
                    commandSequence = commandSequence + ',' + settings.sequenceLeft
                    movement = movement + 1
                elif movement > 0:
                    commandSequence = commandSequence + ',' + settings.sequenceRight
                    movement = movement - 1
        commandSequence = settings.sequenceBegin + commandSequence + ',' + settings.sequenceEnd
        xbmc.log('3DIRSequence: ' + commandSequence, xbmc.LOGDEBUG)
        processSequence(commandSequence)
        # Saving current 3D mode
        settings.curTVmode = settings.newTVmode
        #settings.setSetting('curTVmode', settings.newTVmode)
    else:
        xbmc.log('3DIRStereoscopic mode has not changed', xbmc.LOGDEBUG)
    # Notify of all messages
    notify()

def mainTrigger():
    if not settings.inProgress:
        settings.inProgress - True
        settings.newTVmode = getTranslatedStereoscopicMode()
        if stereoModeHasChanged():
            mainStereoChange()
        settings.inProgress - False

def onAbort():
    # On exit switch TV back to None 3D
    settings.newTVmode = 0
    if stereoModeHasChanged():
        xbmc.log('3DIRExit procedure: changing back to None 3D', xbmc.LOGINFO)
        mainStereoChange()
    serialEnd()

def serialBegin():
    if settings.enableSerial:
        xbmc.log("3DIRSerial Begin", xbmc.LOGDEBUG)
        try:
            ser1 = serial.Serial(settings.comPort, settings.baud)
        except SerialException:
            toNotify('Could Not Open Port')
            settings.enableSerial = 0
    if settings.enableSerial:
        xbmc.log("3DIRSerial Begin1", xbmc.LOGDEBUG)
        ser1.timeout = 5
        if not settings.resetPrevented: test = ser1.read(1)
        ser1.write('t')
        test = ser1.read(1)
        if test != 't':
            settings.enableSerial = 0
            ser1.close()
            toNotify('No Arduino Response')
        else:
            xbmc.log("3DIRSerial Begin2", xbmc.LOGDEBUG)
            ser1.write('1')
            if settings.resetPrevented: ser1.close()
            xbmc.log("3DIRSerial Started", xbmc.LOGDEBUG)
            toNotify('Arduino Connected')
            notify()
            return ser1
    notify()

def serialEnd():
    if settings.enableSerial:
        if not ser.isOpen(): ser.open()
        ser.write('0')
        xbmc.sleep(50)
        ser.close()

class MyMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
    
    def onSettingsChanged( self ):
        xbmc.log('3DIRSettings changed', xbmc.LOGDEBUG)
        serialEnd()
        settings.load()
        ser = serialBegin()
    
    def onScreensaverDeactivated(self):
        # If detect mode is poll only - do not react on events
        if settings.detectmode == 2: return
        xbmc.log('3DIRScreensaver Deactivated', xbmc.LOGDEBUG)
        settings.inScreensaver = False
    
    def onScreensaverActivated(self):
        # If detect mode is poll only - do not react on events
        if settings.detectmode == 2: return
        xbmc.log('3DIRScreensaver Activated', xbmc.LOGDEBUG)
        if settings.skipInScreensaver:
            settings.inScreensaver = True
    
    def onNotification(self, sender, method, data):
        # If detect mode is poll only - do not react on events
        if settings.detectmode == 2: return
        xbmc.log('3DIRNotification Received: SENDERIS ' + str(sender) + ': METHODIS ' + str(method) + ': DATAIS ' + str(data), xbmc.LOGDEBUG)
        if method == 'Player.OnPlay':
            if xbmc.Player().isPlayingVideo():
                xbmc.log('3DIRTrigger: onNotification: ' + str(method), xbmc.LOGDEBUG)
                #Small delay to ensure Stereoscopic Manager completed changing mode
                xbmc.sleep(500)
                mainTrigger()
        elif method == 'Player.OnStop':
            xbmc.log('3DIRTrigger: onNotification: ' + str(method), xbmc.LOGDEBUG)
            #Small delay to ensure Stereoscopic Manager completed changing mode
            xbmc.sleep(500)
            mainTrigger()

def main():
    global dialog, dialogprogress, blackScreen, settings, monitor, ser
    xbmc.log("3DIR", xbmc.LOGDEBUG)
    dialog = xbmcgui.Dialog()
    dialogprogress = xbmcgui.DialogProgress()
    blackScreen = xbmcgui.Window(-1)
    settings = Settings()
    monitor = MyMonitor()
    ser = serialBegin()
    while not xbmc.abortRequested:
#        xbmc.log("3DIR1", xbmc.LOGDEBUG)
        if settings.detectmode != 1:
#            xbmc.log("3DIR2", xbmc.LOGDEBUG)
            if not settings.inScreensaver:
#                xbmc.log("3DIR3", xbmc.LOGDEBUG)
                settings.pollCount += 1
                if xbmc.getGlobalIdleTime() <= settings.idlesec:
#                    xbmc.log("3DIR4", xbmc.LOGDEBUG)
                    if settings.pollCount > settings.pollsec:
#                        xbmc.log("3DIR5", xbmc.LOGDEBUG)
                        mainTrigger()
                        settings.pollCount = 0
                        continue
        xbmc.sleep(1000)
    onAbort()

if __name__ == '__main__':
    main()
