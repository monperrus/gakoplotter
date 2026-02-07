from lxml import etree
import os
import glob

def write_svg(f):
  fdir = "cache/"+os.path.basename(f)+".d"
  if not os.path.exists(fdir): os.mkdir(fdir)
  namespaces = {'svg': 'http://www.w3.org/2000/svg'} 
  doc = etree.XML(open(f,"rb").read())
  for i in doc.xpath("//svg:glyph",namespaces=namespaces):
    #print(i.tag)
    #print(dir(i))
    if i.tag == "{http://www.w3.org/2000/svg}glyph":
      #print(etree.tostring(i))
      if "d" in i.attrib:
        print(i.attrib["unicode"], i.attrib["d"])
        fname=fdir+"/"+i.attrib["unicode"]+".svg"
        with open(fname,"w") as f: 
          data="""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
  <svg xmlns="http://www.w3.org/2000/svg">
          <g style="stroke-linejoin:round;stroke:#000000;stroke-linecap:round;fill:none"
              transform="translate(0,0)">
              <path
                transform="matrix(0.05,0,0,-0.05,0,0)"
                style="stroke-width:0.3846in"
                d="{}"/>
            </g>
  </svg>
  """.format(i.attrib["d"])
          
          f.write(data)
        os.system("juicy-gcode -f flavor-letter.txt "+fname+" > "+fdir+"/"+i.attrib["unicode"]+".gcode")
        os.system("vpype read "+fname+" stat > "+fdir+"/"+i.attrib["unicode"]+".stat")
        

# hershey-text/hershey-text/svg_fonts/
write_svg("./hershey-text/hershey-text/svg_fonts/HersheyScript1.svg")
write_svg("./hershey-text/hershey-text/svg_fonts/EMSOsmotron.svg")


