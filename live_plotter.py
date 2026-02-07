#!/usr/bin/python3
# live coding the pen plotter
# usage: 
# prerequisites:
# /home/martin/bin/gcode-cli from https://github.com/hzeller/gcode-cli
# first start the socket with 
# nc -lU /tmp/tio-socket0 | gcode-cli -
# python3
# from live_plotter import *
# init()
# q(10)
# l(x,y) # line to x,y
#
# # %load_ext autoreload
# %autoreload 2


#-------------------------------------------------------------------------------

import tkinter as tk, tkinter.constants, tkinter.filedialog
import re
import PIL
from PIL import ImageDraw, Image, ImageOps
import math
import os
import sys
import socket
import importlib
import argparse
import readline
import rlcompleter


def gcode2dict(filename):
    return gcode2dict_internal(open(filename,"r").readlines())

def gcode2dict_internal(lines):
    thisGcodeLine= {}
    gCodeDict =[]
    separator = '(M|G|X|Y|Z|I|J|K|F|S|P|;)'
    regex = re.compile(separator,flags= re.IGNORECASE)
    for line in lines:
        thisGcodeLine= {}
        lineList = regex.split(line.rstrip('\n ').upper())
        for i in range(len(lineList)):
            if lineList[i] == (";" or "(" or ""):
                break
            try:
                if lineList[i] in separator: thisGcodeLine[lineList[i].upper()] = float(lineList[i+1].rstrip('\n '))
            except:
                pass
        gCodeDict.append(thisGcodeLine)
    #print(gCodeDict)
    return gCodeDict

def replace(filename, outputfilename, gCodeDict, GValue, axis, searchValue, newValue):
    posX, posY,posZ,i,j,k,g = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0
    a_list = ("M","G", "X", "Y", "Z", "I", "J", "K", "F", "S", "P")

    if searchValue == "*":

        for l in  gCodeDict:
            if l.get('G', None) != None:
                g = l.get('G')
                l["G"] = int(l.get("G"))
            if (l.get('G', None) == GValue) or (g == GValue) :
                l[axis]= newValue


        with open(outputfilename,"w") as f:

            for l in  gCodeDict:
                lsorted =[(key, l[key]) for key in a_list if key in l]
                for key, value in lsorted:
                    f.write(key + str(value) + " ")
                f.write("\n")



def dict2image(gCodeDict, draw, linewidth):
    posX, posY,posZ,i,j,k,g = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0
    return dict2image_internal(gCodeDict, draw, linewidth, posX, posY,posZ,i,j,k,g)

def dict2image_internal(gCodeDict, draw, linewidth, posX, posY,posZ,i,j,k,g):
    print(posX, posY,posZ,i,j,k,g)
    #posX, posY,posZ,i,j,k,g = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0
    scaler = 1.0
    seqX = [x.get('X', 0) for x in gCodeDict]
    seqI = [x.get('I', 0) for x in gCodeDict]
    minX = min(seqX)
    maxX = max(seqX)
    seqY = [x.get('Y', 0) for x in gCodeDict]
    seqJ = [x.get('J', 0) for x in gCodeDict]
    minY = min(seqY)
    maxY = max(seqY)
    seqZ = [x.get('Z', 0) for x in gCodeDict]
    minZ = min(seqZ)
    maxZ = max(seqZ)
    #offsetX = 0.0-minX
    offsetX = linewidth
    #offsetY = 0.0-minY
    offsetY = linewidth
    offsetZ = 0.0-minZ
    dictScaler = ["X","Y","Z","I","J","K"]
    colorZ =0
    if maxX - minX == 0: maxX= 1e-200
    if maxY - minY == 0: maxY= 1e-200
    #scaler = min(sizeX/(maxX - minX),sizeY/(maxY - minY))
    scaler = 1
    
    
    ## setting scalerZcolor
    if maxZ-minZ == 0: scalerZcolor = 1
    elif maxZ-minZ > 0: scalerZcolor = 255/(maxZ-minZ)/scaler
    else: scalerZcolor = 255/(minZ-maxZ)/scaler
    # print("scalerZcolor",scalerZcolor, maxZ,minZ)
    scalerZcolor = 51

    for l in  gCodeDict:
        for key, value in l.items():
            if key =="X":
                l[key]= (value + offsetX)* scaler
            elif key =="Y":
                l[key]= (value + offsetY) * scaler
            #elif key =="Z":
                #l[key]= (value + offsetZ)* scaler
            #elif key in dictScaler:
                #l[key]= value * scaler
        if l.get('X', None) != None or l.get('Y', None) != None or l.get('Z', None) != None or l.get('I', None) != None or l.get('J', None) != None or l.get('K', None) != None:
            print(l)
            if l.get('X', None) == None: l["X"]= posX
            if l.get('Y', None) == None: l["Y"]= posY
            if l.get('Z', None) == None: l["Z"]= posZ
            if l.get('I', None) == None: l["I"]= i
            if l.get('J', None) == None: l["J"]= j
            if l.get('K', None) == None: l["K"]= k
            if l.get('G', None) == None: l["G"]= g
            colorZ = int(l.get("Z")*scalerZcolor)
            if l.get('G', None) == 1:
                print("draw line", [posX, posY,l.get('X'),l.get('Y'), colorZ, linewidth])
                draw.line([posX, posY,l.get('X'),l.get('Y')], width=linewidth)
            elif l.get('G', None) == 3:
                centerX = posX+l.get("I")
                centerY = posY+l.get("J")
                if (posX-centerX) == 0:
                    centerX+=1e-200
                if (posY-centerY) == 0:
                    centerY+=1e-200
                startAngle = math.degrees(math.atan2((posY-centerY),(posX-centerX)))
                if (l.get("X")-centerX) == 0:
                    centerX+=1e-200
                if (l.get("Y")-centerY) == 0:
                    centerY+=1e-200
                stopAngle = math.degrees(math.atan2((l.get("Y")-centerY),(l.get("X")-centerX)))
                radius = math.sqrt(l.get("I")**2+l.get("J")**2)
                if startAngle == stopAngle:
                    stopAngle += 360
                draw.arc([centerX-radius, centerY-radius, centerX+radius, centerY+radius], startAngle, stopAngle, fill=colorZ, width=linewidth)
            elif l.get('G', None) == 2:
                centerX = posX+l.get("I")
                centerY = posY+l.get("J")
                if (posX-centerX) == 0:
                    centerX+=1e-200
                startAngle = math.degrees(math.atan2((posY-centerY),(posX-centerX)))
                if (l.get("X")-centerX) == 0:
                    centerX+=1e-200
                stopAngle = math.degrees(math.atan2((l.get("Y")-centerY),(l.get("X")-centerX)))
                if startAngle == stopAngle: stopAngle += 360
                radius = math.sqrt(l.get("I")**2+l.get("J")**2)
                draw.arc([centerX-radius, centerY-radius, centerX+radius, centerY+radius], stopAngle, startAngle, fill=colorZ, width=linewidth)

            if l.get('X', None) != None: posX = l.get('X')
            if l.get('Y', None) != None: posY = l.get('Y')
            if l.get('Z', None) != None: posZ = l.get('Z')
            if l.get('I', None) != None: i= l.get("I")
            if l.get('J', None) != None: j= l.get("J")
            if l.get('K', None) != None: k= l.get("K")
            if l.get('G', None) != None: g = l.get('G')
    return posX, posY,posZ,i,j,k,g

def init():
    global draw,linewidth,image,state
    sizeX = 300
    sizeY = 420
    linewidth = 5

    image = Image.new(mode = "L", size = (sizeX, sizeY),color="white")
    
    state= ( 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)

    draw = ImageDraw.Draw(image)
    d_internal([
        "G21 ; Set units to millimeters",
        "G17 ; Select XY plane for arc movements",
        "G90 ; Use absolute positioning",
        "F2000 ; Set feed rate to 2000 mm/min",
        "G00 X0 Y0 ; Rapid move to origin (X=0, Y=0)",
        "G00 Z0 ; Rapid move Z to 0",
    ])



s = None

def connect(address):
    global s
    try:
        if ":" in address and not address.startswith("/"):
             host, port = address.split(":")
             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
             s.connect((host, int(port)))
        else:
             s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
             s.connect(address)
        print(f"Connected to {address}")
    except Exception as e:
        print(f"Failed to connect to {address}: {e}")
        s = None

def d_internal(ls): 
    global draw,linewidth,image, state
    # print("state",state)
    posX, posY,posZ,i,j,k,g = state
    state = dict2image_internal(gcode2dict_internal(ls),draw, linewidth, posX, posY,posZ,i,j,k,g)
    #image.show()
    
    # send to socket
    # test with nc -lU /tmp/tio-socket0
    # tio --socket unix:/tmp/tio-socket0 /dev/ttyACM0
    global s
    response = None
    if s:
        try:
            # print(f"; Sending to socket:\n{''.join(ls)}")
            s.send(("\n".join(ls)+"\n").encode("utf-8"))
            s.settimeout(1.0)
            try:
                response = s.recv(4096).decode("utf-8").strip()
                if response:
                    print(f"Response: {response}")
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Read error: {e}")
        except Exception as e:
            print(f"Socket error: {e}")
    return response
        

def d(s):
    d_internal([s])
    

def q(size):
    global state
    posX, posY,posZ,i,j,k,g = state
    d_internal([
        "G00 X"+str(posX)+ " Y"+str(posY),
        "G0 Z5", 
        "G01 X"+str(posX+size)+ " Y"+str(posY),
        "G01 X"+str(posX+size)+ " Y"+str(posY+size),
        "G01 X"+str(posX)+ " Y"+str(posY+size),
        "G01 X"+str(posX)+ " Y"+str(posY),
        "G0 Z0"
        ])

def m(x,y):
    d_internal(["G0 Z0", "G00 X"+str(x)+ " Y"+str(y)])

def l(x,y):
    d_internal(["G0 Z5", "G01 X"+str(x)+ " Y"+str(y), "G0 Z0"])

def laser_on(power=1000):
    """Turns the laser on with the specified power (default 1000)."""
    # 300 for simple paper still cuts
    d_internal([f"M3 S{power}", "F400"])

def laser_off():
    """Turns the laser off."""
    d_internal(["M5"])

def query_position():
    """Query the current position using ? g-code command.
    
    Returns the machine position (x, y, z) parsed from the response.
    """
    print("? ; Query current position")
    response = d_internal(["?"])
    if response:
        # Example GRBL response: <Idle|WPos:0.000,0.000,0.000|Bf:15,128|FS:0,0>
        # or <Idle|MPos:0.000,0.000,0.000|Bf:15,128|FS:0,0|WCO:0.000,0.000,0.000>
        match = re.search(r'[WM]Pos:([-.\d]+),([-.\d]+),([-.\d]+)', response)
        if match:
            x, y, z = map(float, match.groups())
            print(f"Parsed Position: X={x}, Y={y}, Z={z}")
            return x, y, z
    return None

def r():
    global live_plotter
    """ reload the module """
    importlib.reload(live_plotter)
    
##    return image
def plotFile(filename):
    #return
    sizeX = 300
    sizeY = 420
    linewidth = 5

    image = Image.new(mode = "L", size = (sizeX, sizeY),color="white")
    draw = ImageDraw.Draw(image)


    #filename = tkinter.filedialog.askopenfilename(initialdir = "./",title = "Select file",
        #filetypes = (("nc-Files",".nc .cnc"),("all files","*.*")));
    #root.destroy()
    if filename != "":
        with open(filename, 'r') as file:
            input_line_count = sum(1 for line in file)
        print(input_line_count)

        gdict = gcode2dict(filename)
        #print(gdict)
        dict2image(gcode2dict(filename),draw, linewidth)
        #dict2image(gcode2dict("plottablefieldlayer1.gcode"),draw, linewidth)
        image = image.transpose(PIL.Image.FLIP_TOP_BOTTOM)
        image.show()

def repl():
    """
    get python statements as input and execute them, until "exit" is entered
    """
    history_file = os.path.expanduser("~/.live_plotter_history")
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass

    # Enable tab completion
    readline.set_completer(rlcompleter.Completer(globals()).complete)
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    init()
    while True:
        try:
            stmt = input(">>> ")
            if stmt.strip() == "exit":
                break
            if stmt.strip() == "?":
                query_position()
                continue
            if stmt.strip():
                exec(stmt)
                # Save history after each successful command
                readline.set_history_length(1000)
                readline.write_history_file(history_file)
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")

def foo():
    print("s")
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", help="Socket address (host:port or path)")
    args, unknown = parser.parse_known_args()
    
    if args.socket:
        connect(args.socket)

    repl()
    # plotFile(sys.argv[1])
