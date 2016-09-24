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

# Put commands of form <wheelup>RunPlugin(plugin://service.3denabler.arduinoinfrared/?VOL_UP)</wheelup> in your keymap to control volume with the arduino IR interface as well

import xbmc
import xbmcaddon
import serial
import sys

__addon__   = xbmcaddon.Addon()

cmd = False
if sys.argv[2] == '?VOL_UP':
    cmd = 'v'
elif sys.argv[2] == '?VOL_DN' or sys.argv[2] == '?VOL_DOWN':
    cmd = 'b'

if cmd != False:
    xbmc.log("3DIRCommand: " + cmd, xbmc.LOGDEBUG)
    ser = serial.Serial(__addon__.getSetting('comPort'), __addon__.getSetting('baud'))
    ser.write(cmd)
    ser.close()
else: xbmc.log("3DIRCommand" + sys.argv[2] + " Not Recognized", xbmc.LOGDEBUG)