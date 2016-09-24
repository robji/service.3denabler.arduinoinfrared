# 3D Enabler for Arduino Infrared TV

This addon for Kodi interfaces with a dedicated Arduino to issue infrared commands to components in range of an infrared LED. Specifically, this addon detects when Kodi enters a 3D mode and issues the infrared commands to the tv to put it in the same mode. This addon also has a command receiver that can be used in the keymap to issue infrared commands from a keypress, such as volume controls sending commands to a sound system.

# Target Audience

This is not a simple plug-and-play addon. If you intend to use this addon, you must have at least a basic understanding of Arduino and python code. You also need an Arduino, the corresponding USB cable, a 10uF or larger capacitor (if using volume command receiver), one or more infrared LEDs (can be salvaged from old remotes), and wire to dedicate to this project. This addon is presented as-is without any guarantees. It works on my Windows 10 machine with Kodi 16.1 on the Confluence skin and my Arduino Uno. I believe it will work universally but it has not been tested on other configurations.

# Hardware Setup for Arduino Uno

1. The capacitor goes between the ground and reset pins to prevent the Arduino from rebooting every time the serial interface is opened. This is necessary for the volume commands to be fast, but not necessary if only used for the 3D commands. Note that this requires you to manually reset the Arduino to upload code, so you may want to leave this out while getting your IR codes situated.
2. The LED goes positive side in pin 3, ground in pin 2. Pin 3 is necessary to utilize a hardware timer (check IRremote github page for your model), any pin or straight ground can be used for ground. Adjacent pins look cleaner to me so I prefer it.

Some Arduino models are different so search as needed.

# Arduino Code

The Arduino sketches utilize the IRremote library, found here: https://github.com/z3t0/Arduino-IRremote .

The remote codes can be difficult to decipher, but the LIRC project has most everything you'll need: http://lirc.sourceforge.net/remotes/ . The codes in their repository can require a math operation done on them first to be useful to this project as seen in the Arduino sketch, but they are correct.

IRsend2 is the sketch used for Kodi interactivity. IRsendSearch is used to scan for remote codes if needed, for example the LG 3D button is not in the LIRC database. 

# Kodi 3D Configuration

1. Get the pyserial addon from SuperRepo: https://superrepo.org/kodi/addon/script.module.pyserial/ by either direct download or installing the repo
2. Download this repo as a zip file and extract the service.3denabler.arduinoinfrared folder out. Zip that up and install from within Kodi or place it directly in your addons folder and restart Kodi.
3. Set your serial port and baud rate in the addon settings. If you have prevented the Arduino resetting, check that box as well.
4. Set your 3d option positions and sequences in the addon settings. Position is the spot in the menu that the 3d option is located, sequences are keypresses to achieve each action. The 'STR' keypresses signal the Arduino to accept a string before processing anything to avoid filling the serial buffer if there's a ridiculously long sequence. Uncheck 'TV remembers previous position' if your tv starts at the beginning of the menu each time you press 3d.

You should be in business at this point.

# Kodi Keymap Configuration

**YOU MUST HAVE PREVENTED THE ARDUINO RESET TO USE THIS**. If you haven't, the 3D service will grab control of the Arduino and you will get 'Port already open' errors in the log.

Check the mouse.xml file to see my setup for volume up and down. The commandreceiver.py file is what is activated by those commands, so edit that file as needed to send other commands. I might add a section to the settings for this eventually, but if you've gotten this far I think you'll be able to get that too.

# Special Credits:

1. Pavel Kuzub for the 3D Enabler Samsung addon base structure: https://github.com/PavelKuzub/service.3denabler.samsungtv
2. Ken Shirriff for the Arduino IRremote library: https://github.com/z3t0/Arduino-IRremote
3. The LIRC project for their infrared remote code repository: http://lirc.sourceforge.net/remotes/
4. The pyserial project and the Kodi bundling of it: https://superrepo.org/kodi/addon/script.module.pyserial/

That should be it. Feel free to use this code in compliance with the GPL.
