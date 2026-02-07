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
import traceback
import time
import statistics
import matplotlib.pyplot as plt


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
    # print(posX, posY,posZ,i,j,k,g)
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
            # print(l)
            if l.get('X', None) == None: l["X"]= posX
            if l.get('Y', None) == None: l["Y"]= posY
            if l.get('Z', None) == None: l["Z"]= posZ
            if l.get('I', None) == None: l["I"]= i
            if l.get('J', None) == None: l["J"]= j
            if l.get('K', None) == None: l["K"]= k
            if l.get('G', None) == None: l["G"]= g
            colorZ = int(l.get("Z")*scalerZcolor)
            if l.get('G', None) == 1:
                print("; draw line", [posX, posY,l.get('X'),l.get('Y'), colorZ, linewidth])
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
            for cmd in ls:
                s.send((cmd + "\n").encode("utf-8"))
                time.sleep(0.05)  # Small pause between commands
            s.settimeout(1.0)
            try:
                response = s.recv(4096).decode("utf-8").strip()
                # if response:
                #     print(f"Response: {response}")
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Read error: {e}")
        except Exception as e:
            print(f"Socket error: {e}")
    else:
        for cmd in ls:
            print(f"{cmd}")
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

def laser_on(power=100, speed=420   ):
    """Turns the laser on with the specified power (default 1000)."""
    # 1000 / 300 for simple paper still cuts
    # 1000 / 400 cuts well normal paper
    # not that it first warm up
    d_internal([f"M3 S{power}", f"F{speed}"])

def laser_off():
    """Turns the laser off."""
    d_internal(["M5"])

def query_position():
    """Query the current position using ? g-code command.
    
    Returns the machine position (x, y, z) parsed from the response.
    """
    # print("? ; Query current position")
    response = d_internal(["?"])
    if response:
        # Example GRBL response: <Idle|WPos:0.000,0.000,0.000|Bf:15,128|FS:0,0>
        # or <Idle|MPos:0.000,0.000,0.000|Bf:15,128|FS:0,0|WCO:0.000,0.000,0.000>
        match = re.search(r'[WM]Pos:([-.\d]+),([-.\d]+),([-.\d]+)', response)
        if match:
            x, y, z = map(float, match.groups())
            # print(f"Parsed Position: X={x}, Y={y}, Z={z}")
            return x, y, z
    return None

def spirals(origin, diameter):
    """Draw spirals using G3 counter-clockwise arc commands.
    
    Creates concentric circles at decreasing radii to approximate a spiral.
    
    Args:
        origin: tuple (x, y) - center point of the spiral
        diameter: float - outer diameter of the spiral
    
    Usage:
        spirals((50, 50), 40)  # Draw spiral centered at (50,50) with 40mm diameter
    """
    x_center, y_center = origin
    max_radius = diameter / 2
    num_circles = 8  # Number of concentric circles
    
    commands = []
    
    # Move to starting position (pen up)
    commands.append("G0 Z0")
    commands.append(f"G00 X{x_center + max_radius} Y{y_center}")
    
    # Pen down
    commands.append("G0 Z8")
    # Draw concentric circles from outside to center
    for i in range(num_circles):
        radius = max_radius * (1 - i / num_circles)
        
        if radius < 0.5:  # Stop if radius gets too small
            break
        
        # Draw circle as two semicircles
        # Current position: (x_center + radius, y_center)
        
        # First semicircle: right to left (180 degrees)
        end_x = x_center - radius
        end_y = y_center
        i_offset = -radius  # I: offset from current X to center X
        j_offset = 0         # J: offset from current Y to center Y
        commands.append(f"G3 X{end_x:.3f} Y{end_y:.3f} I{i_offset:.3f} J{j_offset:.3f}")
        
        # Second semicircle: left to right (180 degrees)
        # Now at (x_center - radius, y_center)
        next_radius = max_radius * (1 - (i + 1) / num_circles)
        end_x = x_center + next_radius
        end_y = y_center
        i_offset = radius    # I: offset from current X (x_center - radius) to center X (x_center)
        j_offset = 0         # J: offset from current Y to center Y
        commands.append(f"G3 X{end_x:.3f} Y{end_y:.3f} I{i_offset:.3f} J{j_offset:.3f}")
    
    
    # Pen up
    commands.append("G0 Z0")
    
    d_internal(commands)


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
            stmt = input("; >>> ")
            if stmt.strip() == "exit":
                break
            if stmt.strip() == "?":
                query_position()
                continue
            if stmt.strip() == "0":
                m(0,0)
                continue
            if stmt.strip():
                if "(" not in stmt and ")" not in stmt:
                    stmt += "()"
                print(f"; Executing: {stmt}")
                exec(stmt)
                # Save history after each successful command
                readline.set_history_length(1000)
                readline.write_history_file(history_file)
        except KeyboardInterrupt:
            print("\nCtrl-C received, sending G0X0Y0...")
            d("G0X0Y0")
            break
        except EOFError:
            break
        except Exception as e:
            # print(f"Error: {e}")
            traceback.print_exc()

def foo():
    print("s")

def laser_test():
    laser_on(800)
    # 10 it warms up
    for i in range(7,2,-1):
        speed = 100 + i * 50  # Variable speed from 100 to 550
        d(f"F{speed}")
        size = 10
        x_offset = i * (size + 2)
        m(x_offset, 0)
        q(size)


    laser_off()

def clock_test():
    connect("/tmp/tio-socket0")
    init()
    before = time.time()
    clock3(60)
    after = time.time()
    print(f"Total time: {after - before:.2f} seconds")
    m(0,0)

def clock2(zvalue=7):
    """
    draw one spot per second with just pen down

    draw ten spots in total

    between spots, move as fast as possible to the next position, and then draw the next spot at the specified speed.

    python -c "from live_plotter import clock2; clock2()" | gcode-cli -
    """
    num_spots = 25
    spot_duration = 1  # seconds per spot
    
    # Fast movement speed between spots
    rapid_speed = 5000
    
    distance = 10
    for i in range(num_spots):
        # Position for this spot (arrange in a row)
        x_offset = i * distance  # 10mm spacing between spots
        y_offset = 0
        
        # Move quickly to position (pen up)
        d(f"F{rapid_speed}")
        m(x_offset, y_offset)
        
        # Pen down for the spot
        d(f"G0 Z{zvalue}")
        
        # Wait for 1 second
        d(f"G4 P.46")  # Dwell for 1 second (P is in seconds for most controllers)
        # time.sleep(spot_duration)
        
        # Pen up
        d("G0 Z0")
    
    # Return to origin at fast speed
    d(f"F{rapid_speed}")
    m(0, 0)

def clock4(zvalue=7):
    init()
    results = {}
    for feed_rate in range(800, 1200, 100):
        vals = []
        for x in range(0, 4):
            data = clock4_internal(x*7, 0, 0, feed_rate)
            vals.append(data["ratio"])

        # for some reasons the first one is slower
        vals = vals[1:]
        print(vals)
        print(feed_rate, statistics.mean(vals))
        results[feed_rate] = statistics.mean(vals)
        m(0,0)
        
    # Plot the results
    feed_rates = list(results.keys())
    ratios = list(results.values())
    
    plt.figure(figsize=(10, 6))
    plt.plot(feed_rates, ratios, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('Feed Rate (mm/min)')
    plt.ylabel('Ratio (Actual Time / Theoretical Time)')
    plt.title('Feed Rate vs Time Ratio')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
        

def clock4_internal(init_x = 0, init_y = 0, zvalue=7, threoretical_feed_rate=1000):
    """
    draw the longest possible vertical line, and measure the time it takes to draw it, then compute ratio between feed rate F and actual time.
    python -c "from live_plotter import clock4; clock4()" | gcode-cli -
    """

    line_length = 100  # mm - longest possible vertical line

    CORRECTION_RATIO = 1.2703992525736492 * 1.0364954471588135
    CORRECTION_RATIO = 1
    test_feed_rate = threoretical_feed_rate * CORRECTION_RATIO  # mm/min - test feed rate
    

    # Calculate theoretical time: time = distance / (speed/60)
    theoretical_time = (line_length / threoretical_feed_rate) * 60  # in seconds
    
    print(f";Drawing {line_length}mm line at F{test_feed_rate}")
    print(f";Theoretical time: {theoretical_time:.2f} seconds")
    
    # Fast movement speed
    rapid_speed = 5000
    
    # Move to starting position
    d(f"F{rapid_speed}")
    m(init_x, init_y)
    
    # Set test feed rate
    d(f"F{test_feed_rate}")
    
    d(f"G0 Z{zvalue}")

    # Start timing
    start_time = time.time()
    
    # draw vertical line
    d(f"G01 X{init_x} Y{line_length}")
    
    
    current_y = init_y
    # Poll current position 20 times
    while current_y < line_length:  # Timeout after 2x theoretical time
        pos = query_position()
        if pos:
            current_x, current_y, current_z = pos
            #print(f"; Current position: X={current_x:.2f}, Y={current_y:.2f}, Z={current_z:.2f}")
            time.sleep(0.1)  # Small delay between polls
    # Stop timing
    end_time = time.time()
    actual_time = end_time - start_time
    
    # Pen up
    d("G0 Z0")

    # Compute ratio
    ratio = actual_time / theoretical_time
    
    data = {
        'line_length': line_length,
        'theoretical_time': theoretical_time,
        'actual_time': actual_time,
        'ratio': ratio,
        'theoretical_feed_rate': threoretical_feed_rate,
        'set_feed_rate': test_feed_rate,
        'effective_feed_rate': line_length * 60 / actual_time
    }


    print(f";Actual time: {actual_time:.2f} seconds")
    print(f";Theoretical Feed rate: {data['theoretical_feed_rate']} mm/min")
    print(f";Effective feed rate: {data['effective_feed_rate']} mm/min")
    print(f";Ratio (actual/theoretical): {data['ratio']:.4f}")
    
    # Return to origin
    d(f"F{rapid_speed}")
    m(init_x, init_y)
    

    # print(";" + (";".join(str(data).split("\n"))))
    return data

def clock3(num_lines = 10, zvalue=7):
    """
    draw one horizontal line per second with just pen down
    compute the feed rate F so that it takes exactly 1 second to draw each line, based on the length of the line and the desired duration.

    draw ten lines in total, one of top of the other, with 2mm spacing

    between lines, move as fast as possible to the next position

    python -c "from live_plotter import clock3; clock3()" | gcode-cli -
    """
    line_length = 30  # mm
    line_spacing = 2  # mm between lines
    line_duration = 1  # second per line
    
    # Calculate feed rate: to draw line_length mm in 1 second
    # F is in mm/min, so F = line_length * 60
    draw_speed = line_length * 60  # mm/min
    
    # Fast movement speed between lines
    rapid_speed = 5000
    
    for i in range(num_lines):
        # Position for this line (stacked vertically)
        x_start = 0
        y_position = i * line_spacing
        x_end = line_length
        
        # Move quickly to starting position (pen up)
        d(f"F{rapid_speed}")
        m(x_start, y_position)
        
        # Set drawing speed for this line (to take 1 second)
        d(f"F{draw_speed}")
        
        # Pen down and draw line
        d(f"G0 Z{zvalue}")
        d(f"G01 X{x_end} Y{y_position}")
        
        # Pen up
        d("G0 Z0")
    
    # Return to origin at fast speed
    d(f"F{rapid_speed}")
    m(0, 0)

def clock1(zvalue=7):
    """
    draw one square per second, with the F parameter controlling the speed of the movement, and thus the time it takes to draw each square.

    draw ten squares in total

    between squares, move as fast as possible to the next position, and then draw the next square at the specified speed.

    python -c "from live_plotter import clock_test; clock_test()" | gcode-cli -
    """
    size = 10  # Size of each square in mm
    num_squares = 10
    
    # Calculate perimeter and feed rate for 1 second per square
    perimeter = 4 * size  # Total distance to draw one square
    # F is in mm/min, so for 1 second we need: perimeter * 60 mm/min
    draw_speed = perimeter * 60  # This will make each square take 1 second
    
    # Fast movement speed between squares
    rapid_speed = 5000
    
    for i in range(num_squares):
        # Position for this square (arrange in a row)
        x_offset = i * (size + 5)  # 5mm spacing between squares
        y_offset = 0
        
        # Move quickly to starting position (pen up)
        d(f"F{rapid_speed}")
        m(x_offset, y_offset)
        
        # Set drawing speed for this square (to take 1 second)
        d(f"F{draw_speed}")
        
        # Draw the square
        d_internal([
            f"G0 Z{zvalue}",  # Pen down
            f"G01 X{x_offset + size} Y{y_offset}",
            f"G01 X{x_offset + size} Y{y_offset + size}",
            f"G01 X{x_offset} Y{y_offset + size}",
            f"G01 X{x_offset} Y{y_offset}",
            f"G0 Z{zvalue}"   # Pen up
        ])
    
    # Return to origin at fast speed
    d(f"F{rapid_speed}")
    m(0, 0)


def spirals_test():
    """
    python -c "from live_plotter import spirals_test; spirals_test()" | gcode-cli -
    """
    init()
    spirals((50, 50), 40)
    m(0,0)
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", help="Socket address (host:port or path)")
    args, unknown = parser.parse_known_args()
    
    if args.socket:
        connect(args.socket)

    repl()
    # plotFile(sys.argv[1])
