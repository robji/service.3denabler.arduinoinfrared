#include <IRremote.h>

IRsend irsend;

void setup()
{
  Serial.begin(9600);
  delay(50);
  Serial.print('1');
  Serial.setTimeout(300);
  pinMode(2,OUTPUT);
  digitalWrite(2,LOW);
}

String cmd;
char ch;

void loop() {
  delay(25);
  if (Serial.available ()>0) {
    ch = Serial.read();
    if (ch == '~'){
      cmd = Serial.readString();
      int j = cmd.length();
      for (int i=0; i<j; i++){
        parseCmd(cmd[i]);
      }
      Serial.print('~');
    } else {
      parseCmd(ch);
    }
  }
}

void parseCmd (char C) {
  switch (C){
    case 't': // test connection
      Serial.print(C);
      break;
    case '0': // turn off sound
      sound(0x540c);
      break;
    case '1': // wake both
      sound(0x3c0c);
    case '4': // wake tv
      tv(0x8877);
      tv(0xda25);
      tv(0xda25);
      break;
    case '5': // turn off tv
      tv(0x10ef);
      break;

    // Sound system volume (Kodi runs passthrough audio without volume control)
    case 'v': // sound vol+
      sound(0x240c);
      break;
    case 'b': // sound vol-
      sound(0x640c);
      break;

    // TV nav commands
    case '3': // 3d button
      tv(0x3bc4);
      break;
    case 'r': // tv right
      tv(0x609f);
      break;
    case 'l': // tv left
      tv(0xe01f);
      break;
    case 'e': // tv enter
      tv(0x22dd);
      break;
    case 'x': // tv exit
      tv(0xda25);
      break;
    
    // delays (run on arduino instead of pc to keep proper timing)
    case '@':
      delay(200);
      break;
    case '%':
      delay(500);
      break;
    case '!':
      delay(1500);
      break;
    default:
      break;
  }
}
void sound(long in){
  for (int i = 0; i < 3; i++) {
    irsend.sendSony(in, 15);
    delay(40);
  }
  delay(20);
}
void tv(long in){
  irsend.sendLG((0x20df0000+in), 32);
  delay(110);
}
/*
sony
540c power
240c vol+
640c vol-
140c mute
320c balance
--- SOURCES TURN IT ON ---
220c video 1
3c0c video 2

lg
0x10ef power
0x8877 1 (turns on without turning off)
13ec, 15ea => No storage units available
16e9, 25da Self Diagnosis
19e6 Next source
2bd4 Component 2
33CD HDMI 2
3BC4 3d
*/
