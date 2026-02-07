#!/bin/bash
"""
penplotter as typewriter

uses g-code parsing

usage: stdbuf -i0 -o0 -e0  python -u typewrite.py | gcode-cli -


could also be done using ./hf2gcode --no-post --no-pre "a" directly

sophistication
font size change
different font change
generative font

"""
from gcodeparser import GcodeParser
import sys, tty, termios
import random
import os

# fonts for https://gitlab.com/oskay/hershey-text/-/tree/Inkscape_v1/hershey-text/svg_fonts, cloned locally, see hershey-text/hershey-text/svg_fonts/
# echo cache/*.svg.*
# I have only two fonts for now
FONT="HersheyScript1"
FONT="EMSOsmotron"

assert os.path.exists('cache/'+FONT+'.svg.d/'), f"Font directory not found: cache/{FONT}.svg.d/"

SCALE=1

def width_letter(l):
  lfile = 'cache/'+FONT+'.svg.d/'+l+'.gcode'
  if not os.path.exists(lfile): 
    return 0
  with open(lfile, 'r') as f:
    gcode = f.read()
  data = GcodeParser(gcode)
  return max(x.params["X"] if "X" in x.params else 0 for x in GcodeParser(gcode).lines )

Z=6.55
def letter(l,translation_x,translation_y=0):
  lfile = 'cache/'+FONT+'.svg.d/'+l+'.gcode'
  if not os.path.exists(lfile): 
    print("; letter not supported: "+l)
    return
  with open(lfile, 'r') as f:
    gcode = f.read()
    # hack to adjust height
    gcode = gcode.replace("G0Z6.3","G0Z"+str(Z))
  data = GcodeParser(gcode)
  for x in data.lines:
    #print(x.params)
    if "X" in x.params:
      x.params["X"]*=SCALE
      x.params["X"]+=translation_x
    if "Y" in x.params:
      #print("foo")
      x.params["Y"]*=SCALE
      x.params["Y"]+=translation_y
  return "\n".join(x.gcode_str for x in data.lines)

def generativeletter(l,translation_x,translation_y=0):
  with open('cache/'+FONT+'.svg.d/'+l+'.gcode', 'r') as f:
    gcode = f.read()
  data = GcodeParser(gcode)
  for x in data.lines:
    #print(x.params)
    if "X" in x.params:
      x.params["X"]+=translation_x+random.randint(0,1)
    if "Y" in x.params:
      #print("foo")
      x.params["Y"]+=translation_y+random.randint(0,1)
  return "\n".join(x.gcode_str for x in data.lines)


def martin():
  x=0
  for i in "martin":
    print(letter(i,x))
    x+=10

# https://stackoverflow.com/questions/510357/how-to-read-a-single-character-from-the-user
def readchr():
  fd = sys.stdin.fileno()
  old_settings = termios.tcgetattr(fd)
  try:
      tty.setraw(sys.stdin.fileno())
      ch = sys.stdin.read(1)
  finally:
      termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
  return ch

TOP=380
x=0
y=0

print("G21 ; Set Units to Millimeters")
print("G17 ; Set Plane Selection to XY")
print("G90 ; Set Absolute Positioning")
print("F5000  ; Set Speed to 2500 mm/min")


NEWLINE_SPACE=14
def newline():
  global x,y
  #pass
#elif character=="\n":
  print("; newline")
  x=0
  y-=NEWLINE_SPACE*SCALE
  print("G00 X"+str(x)+"Y"+str(y))
  
def space():
  global x,y
  x+=10*SCALE
  print("G00 X"+str(x))

def randomspace(mins=0,maxs=10):
  global x,y
  x+=random.randint(mins,maxs)*SCALE
  print("G00 X"+str(x))

def print_char(character):
  print("; "+str(ord(character)))
  global x,y
  if character=="\r" or character=="\n" :
    newline()
  elif character==" ":
    space()
  # elif ord(character)==126:    
  elif character=="²":    
    # print(";F5")
    goto_origin()
  elif character=="~":    
    # print(";F5")
    goto_top()
  else:
    print("; ",character)
    letter_code = letter(character,x,y)
    if letter_code:
      print(letter_code)
      #x+=10
      x+=width_letter(character)*SCALE

def goto_origin():
  global x,y
  print("G00 X0 Y0 ; F5 goto 0,0")
  x=0
  y=0

def goto_top():
  global x,y
  y=TOP
  print("G00 X"+str(x)+"Y"+str(y))

def goto(_x,_y):
  global x,y
  x=_x
  y=_y
  print("G00 X"+str(_x)+"Y"+str(_y))

def query_position():
  """Query the current position using M114 g-code command.
  
  Returns the internal position state (x, y) and sends M114 command
  to query the actual machine position.
  
  Usage:
    query_position()
  """
  global x, y
  print("? ; Query current position")
  # to parse the output I need to have the socket and read from it
  print(f"; Internal state: X={x} Y={y}")
  return (x, y)
  
def typewrite_live():
  global x,y
  # we start at the opt left corner
  # print("G00 X"+str(x)+"Y"+str(y))
  goto_top()

  try:
    for i in range(0,100000):
      character = readchr()
      if ord(character) == 3:  # Ctrl-C
        break
      if ord(character) == 0x1b:  # ESC key - start of escape sequence
        # Read the next two characters to get the full F-key sequence
        next_ch = readchr()
        print(f"; ESC sequence: {next_ch}")
        if next_ch == 'O':  # F1-F4 use ESC O sequence
            final_ch = readchr()
            if final_ch == 'P':  # F1
                query_position()
            continue
      print_char(character)
      query_position()
  except KeyboardInterrupt:
    pass


def print_word(word):
  for x in word:
    print_char(x)

def test1():
  goto_top()
  # goto_origin()
  print_word("\n\n\nmartin")
  goto_origin()

def test2():
  global NEWLINE_SPACE,x,y
  NEWLINE_SPACE=3
  INIT=int(TOP*1.0)
  goto(0,INIT)
  for i in range(0,10):  
    print_char("\n")
  # print_char("\n")
  # print_char("\n")
  # print_char("\n")
  # goto_origin()
  l=[x for x in "abcdefghjklmnopqrstuvwxyz"]
  MAX=130
  while y>INIT-(MAX*1.3):
    while x<MAX:
      print_char(random.choice(l))
    newline()
      
  # print_word("\n\n\nmartin")
  goto_origin()











def test3():
  """
    in this one, I add my name and the current date in the middle

  """
  global NEWLINE_SPACE,x,y
  global Z
  # with and without the cardboard it's .75 difference
  Z=5.89
  #+.75
  NEWLINE_SPACE=5.1
  ## positioning at the beginning
  y=380
  print("G92 X0 Y"+str(y))

  INIT=int(TOP*.8)
  # goto(0,INIT)
  l=[x for x in "abcdefghjklmnopqrstuvwxyz"]
  MAX=130
  linenumber=0
  INCREASE=.02
  while y>INIT-(MAX*.18): # postcard ratio is 3:2
    charnumber = 0
    where_random = random.randint(3,10)
    while x<MAX:
      if linenumber==3 and charnumber == 0:
        Z+=INCREASE
        # print_word("martin")
        Z-=INCREASE
      if linenumber==8 and charnumber == 0:
        Z+=INCREASE
        # print_word("monperrus")
        Z-=INCREASE
      if linenumber==13 and charnumber == 0:
        Z+=INCREASE
        print_word("18/01/2025")
        Z-=INCREASE
      if charnumber%2==1:
        print_char(random.choice(l))
      else: 
        randomspace(3)
        print_char('/')
      charnumber +=1
    newline()
    linenumber+=1
  print("; "+str(linenumber))
  # print_word("\n\n\nmartin")
  # goto_origin()

def test_calibrate():
  global Z
  goto_top()
  for x in range(30,60,1):
    Z=str(x/10)
    print_word(Z)
    newline()
  goto_origin()

if __name__ == "__main__":
  typewrite_live()
  # test3()

# test_calibrate()
# typewrite_live()
