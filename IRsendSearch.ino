/*
 * IRremote: IRsendDemo - demonstrates sending IR codes with IRsend
 * An IR LED must be connected to Arduino PWM pin 3.
 * Version 0.1 July, 2009
 * Copyright 2009 Ken Shirriff
 * http://arcfn.com
 */

#include <IRremote.h>

IRsend irsend;
long code;

void setup()
{
  Serial.begin(9600);
  Serial.write('1');
  pinMode(2,OUTPUT);
  digitalWrite(2,LOW);
}

unsigned long data = 0x3400;
unsigned long knowns[] = {0x10EF,0xA956,0x0CF3,0xD02F,0x0FF0,0x8877,0x48B7,0xC837,0x28D7,0xA857,0x6897,0xE817,0x18E7,0x9867,0x08F7,0xCA35,0x58A7,0x40BF,0xC03F,0x00FF,0x807F,0x7887,0x9E61,0x906F,0xC23D,0xD52A,0xA25D,0x02FD,0x827D,0xE01F,0x609F,0x22DD,0x14EB,0x55AA,0xDA25,0x4EB1,0x8E71,0xC639,0x8679,0x04FB,0x847B,0x9C63,0x8D72,0x0DF2,0x5DA2,0xF10E,0x718E,0x7E81,0xff00,0xdf20,0x05fa};


bool isUnknown(unsigned long code){
  for (int i=0; i<51; i++){
    if (knowns[i] == code) return false;
  }
  return true;
}

int delayBoost = 0;
int counter = 0;

void loop() {
  if (Serial.available ()>0) {
    data -= 50;
    delayBoost = 1500;
    counter = 0;
    Serial.read();
  }
  if(isUnknown(data)) tv(data);
  Serial.println(data,HEX);
  delay(delayBoost);
  if (counter > 30) delayBoost = 0;
  counter++;
  data++;
}
void sound(long in){
  for (int i = 0; i < 3; i++) {
    irsend.sendSony(in, 15);
    delay(40);
  }
}
void tv(long in){
  irsend.sendLG((0x20df0000+in), 32);
  delay(108);
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
