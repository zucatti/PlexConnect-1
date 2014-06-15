import re
import sys
import math 
import ntpath
import urllib
import urllib2


import ConfigParser

import os.path
import unicodedata
from Debug import * 
from Version import __VERSION__  # for {{EVAL()}}, display in settings page
import Settings, ATVSettings
import PlexAPI

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageFilter

class ImageBackground():
    options = {\
        'template' : 'plex',\
        'title' : '',\
        'subtitle' : '',\
        'image' : 'blank.jpg',\
        'resolution' : '1080',\
        'font' : 'fonts/OpenSans/OpenSans-Light.ttf',\
        'titleSize' : '50',\
        'subtitleSize' : '35',\
        'titleColor' : 'ffffff',\
        'subtitleColor' : 'ffffff',\
        'anchorX' : 'right',\
        'anchorY' : 'top',\
        'offsetX' : '75',\
        'offsetY' : '10',\
        'lineheight' : '170',\
        'imageBlur' : None,\
        'layers' : []\
    }
    
    cfg = {}
    
    def __init__(self,opts):
        for opt in self.options:
            self.cfg[opt] = self.options[opt]
        if opts != None:
         for opt in opts:
            if self.cfg[opt] != opts[opt]:
                self.cfg[opt] = opts[opt]

                          
    def setOptions(self,opts):
        for opt in opts:
            if self.cfg[opt] != opts[opt]:
                self.cfg[opt] = opts[opt]
                
    def getRendersize(self, res):
        if str(res)=="poster":
            renderwidth = 512
            renderheight = 768
        elif str(res)=="16X9":
            renderwidth = 768
            renderheight = 432
        elif str(res)=="flow":
            renderwidth = 768
            renderheight= 256
        elif str(res)=="square":
            renderwidth = 768
            renderheight = 768
        else:
            renderwidth = 1280
            renderheight = 720
        return renderwidth, renderheight
        
    def fullHDtext(self,number):
        number = int(number)*1080/720
        return number
    
    def createFileHandle(self):
        cachefileStyle = normalizeString(self.cfg['template'])
        cachefileTitle = normalizeString(self.cfg['title'])
        cachefileSubtitle = normalizeString(self.cfg['subtitle'])
        cachefileRes = normalizeString(self.cfg['resolution'])
        
        sourcefile = remove_junk(str(self.cfg['image']))
        sourcefile = remove_junk(str(sourcefile))

        
        t1s = normalizeString(self.cfg['titleSize'])
        t1c = normalizeString(self.cfg['titleColor'])
        tax = normalizeString(self.cfg['anchorX'])
        tay = normalizeString(self.cfg['anchorY'])
        tox = normalizeString(self.cfg['offsetX'])
        toy = normalizeString(self.cfg['offsetY'])
        t2s = normalizeString(self.cfg['subtitleSize'])
        t2c = normalizeString(self.cfg['subtitleColor'])
        lh = normalizeString(self.cfg['lineheight'])
        ib = normalizeString(self.cfg['imageBlur'])
        
        # add layers
        layerrange = range(0, len(self.cfg['layers']))
        cachefileLayers = ""
        for layercounter in layerrange:
            if self.cfg['layers'][layercounter] != None:
                cachefileLayers = cachefileLayers+"+"+normalizeString(self.cfg['layers'][layercounter])
                
        # fix for extra long subtitles
        if len(cachefileSubtitle) > 30:
            cachefileSubtitle = cachefileSubtitle[0:30]
        cachefile = cachefileStyle+cachefileLayers+"+"+sourcefile+"+"+cachefileTitle+"+"+t1s+"+"+t1c+"+"+tax+"+"+tay+"+"+tox+"+"+toy+"+"+cachefileSubtitle+"+"+t2s+"+"+t2c+"+"+lh+"+"+ib+"+"+cachefileRes
        
        return cachefile


    def resizedMerge (self,background, stylepath):
        isatv2=0

        renderwidth, renderheight = self.getRendersize(self.cfg['resolution'])
        if str(renderheight) == "720":
            height = int(self.cfg['resolution'])
            if height == 720:
                isatv2 = 1
                width = 1920
                height = 1080
            elif height == 1080:
                width = 1920
        else:
            width = renderwidth
            height = renderheight
            
        im = Image.new("RGB", (width, height), "black")
        background = background.resize((width, height), Image.ANTIALIAS)
    
        # Blur BG
        if self.cfg['imageBlur'] != None and self.cfg['imageBlur'] != "" and self.cfg['imageBlur'] > 0:
            for i in range(0,int(self.cfg['imageBlur'])):
                background = background.filter(ImageFilter.BLUR)
        im.paste(background, (0, 0), 0)
        # Layers
        layerrange = range(0, len(self.cfg['layers']))
        for layercounter in layerrange:
            if self.cfg['layers'][layercounter] != None:
                layer = Image.open(stylepath+"/images/"+self.cfg['layers'][layercounter]+".png")
                layer = layer.resize((width, height), Image.ANTIALIAS)
                im.paste(layer, ( 0, 0),layer)
    
        if isatv2>0:
            im = im.resize((1280, 720), Image.ANTIALIAS)
        return im

    def textToImage(self, im, stylepath, index):
        if index == 1:
            if self.cfg['titleSize'] != None and self.cfg['titleSize'] != "":
                fontsize = int(self.cfg['titleSize'])
            else:
                fontsize = int(params[4]) / 24
            
            if self.cfg['titleColor'] != None and self.cfg['titleColor'] != "":
                if is_hex(str(self.cfg['titleColor'])):
                    textcolor = self.cfg['titleColor']
                    textcolor = tuple(int(textcolor[i:i+len(textcolor)/3], 16) for i in range(0, len(textcolor), len(textcolor)/3))
                else:
                    textcolor = self.cfg['titleColor']
            else: # Default Color
                textcolor = (255, 255, 255)
            
            text = unicode(urllib.unquote(self.cfg['title']), 'utf-8').replace('+',' ').strip()
                                
        elif index == 2:
            if self.cfg['subtitleSize'] != None and self.cfg['subtitleSize'] != "":
                fontsize = int(self.cfg['subtitleSize'])
            else:
                fontsize = int(params[4]) / 36
                
            if self.cfg['subtitleColor'] != None and self.cfg['subtitleColor'] != "":
                if is_hex(str(self.cfg['subtitleColor'])):
                    textcolor = self.cfg['subtitleColor']
                    textcolor = tuple(int(textcolor[i:i+len(textcolor)/3], 16) for i in range(0, len(textcolor), len(textcolor)/3))
                else:
                    textcolor = self.cfg['subtitleColor']
            else: # Default Color
                textcolor = (255, 255, 255)
                
            text = unicode(urllib.unquote(self.cfg['subtitle']), 'utf-8').replace('+',' ').strip()
                
        # TypeSpace
        draw = ImageDraw.Draw(im)
        font = stylepath+"/"+self.cfg['font']
        width, height = draw.textsize(text, ImageFont.truetype(font, int(fontsize)))
        renderwidth, renderheight = self.getRendersize(self.cfg['resolution'])

        # Anchor and Offset X
        if (self.cfg['anchorX'] != None and self.cfg['anchorX'] != "" ) or (self.cfg['offsetX'] != None and self.cfg['offsetX'] != ""):
            if self.cfg['anchorX'] == "right":
                offsetx = renderwidth - width - int(self.cfg['offsetX'])
            elif self.cfg['anchorX'] == "center":
                offsetx = (renderwidth - width) / 2
            elif self.cfg['anchorX'] == "left":
                offsetx = int(self.cfg['offsetX'])
            else:
                offsetx = 80
        else:
            offsetx = 80
        # Anchor and Offset Y
        if ( self.cfg['anchorY'] != None and self.cfg['anchorY'] != "" ) or ( self.cfg['offsetY'] != None and self.cfg['offsetY'] != "" ):
            if self.cfg['anchorY'] == "bottom":
                offsety = renderheight - int(self.cfg['offsetY'])
            elif self.cfg['anchorY'] == "middle":
                offsety = ( renderheight - height ) / 2
            elif self.cfg['anchorY'] == "top" or self.cfg['anchorY'] == "":
                offsety = int(self.cfg['offsetY'])
            else:
                offsety = 80
            # Subtitle
            
            if index > 1 and ( self.cfg['title'] != None and self.cfg['title'] != "" ):
                if self.cfg['titleSize'] != None or self.cfg['titleSize'] != "":
                    titlefontsize = int(self.cfg['titleSize'])
                else: # Default Size
                    titlefontsize = int(self.cfg['resolution']) / 24
                if self.cfg['lineheight'] != None and self.cfg['lineheight'] != "":
                    offsety = offsety + (titlefontsize * int(self.cfg['lineheight']) / 100)
                else:
                    offsety = offsety + (titlefontsize * 130 / 100)
        else:
            offsety = 80
        # Handle 1080 / atv3 Text
        if self.cfg['resolution'] == "1080":
            fontsize = self.fullHDtext(fontsize)
            offsetx = self.fullHDtext(offsetx)
            offsety = self.fullHDtext(offsety)
        # Write    
        draw.text((int(offsetx), int(offsety)), text , font=ImageFont.truetype(font, int(fontsize)), fill=textcolor)
        return im

    def generate(self):
    
    # Catch the Params
        cachepath = sys.path[0]+"/assets/fanartcache"
        stylepath = sys.path[0]+"/assets/templates/"+self.cfg['template']
        cachefile = self.createFileHandle()
        
        dprint(__name__, 1, 'Check for Cachefile.')  # Debug
        # Already created?
        if os.path.isfile(cachepath+"/"+cachefile+".png"):
            dprint(__name__, 1, 'Cachefile  found.')  # Debug
            return cachefile+".png" # Bye Bye
        # No it's not
        else:
            dprint(__name__, 1, 'No Cachefile found. Generating Background.')  # Debug
            # Setup Background
            url = urllib.unquote(self.cfg['image'])
            if os.path.isfile(stylepath+"/images/"+url):
                dprint(__name__, 1, 'Fetching Template Image.'  )  # Debug
                background = Image.open(stylepath+"/images/"+url)
            elif url[0][0] != "/":
                try:
                    bgfile = urllib2.urlopen(url)
                except urllib2.URLError, e:
                    dprint(__name__, 1, 'error: {0}', str(e.code)+" "+e.msg+" // url:"+ url )  # Debug
                    background = Image.open(stylepath+"/images/blank.jpg")
                else:
                    dprint(__name__, 1, 'Fetting Remote Image.')  # Debug
                    output = open(cachepath+"/tmp.png",'wb')
                    output.write(bgfile.read())
                    output.close()
                    background = Image.open(cachepath+"/tmp.png")
                
            # Set Resolution and Merge Layers
            #if params[4] == "720":
            dprint(__name__, 1, 'Merging Layers.')  # Debug
            im = self.resizedMerge(background, stylepath)
            #else: # 1080
            # im = resizedMerge(background, params, fanartpath)
            # Setup Title Type Space
            dprint(__name__, 1, 'Add Text.')  # Debug
            if self.cfg['title'] != None and self.cfg['title'] != "":
                im = self.textToImage (im, stylepath, 1)
            # Setup Subtitle Type Space
            if self.cfg['subtitle'] != None and self.cfg['subtitle'] != "":
                im = self.textToImage (im, stylepath, 2)
            # Save to Cache
            im.save(cachepath+"/"+cachefile+".png")  
            dprint(__name__, 1, 'Cachefile  generated.')  # Debug
            return cachefile+".png"
        
       
            
            
            
            
            
        
        
        
        
        
   
# Layered Fullscreen Background
# usage:
# {{LFBG(<TEMPLATE>,                           
#  1     <TITLE>,                               
#  2     <SUBTILE>,                             
#  3     <FANART>,                              
#  4     <RESOLUTION>                          
#  5  [, <FONT>,                                
#  6     <TITLESIZEATV2>,                      
#  7     <SUBTITLESIZEATV2>,                          
#  8     <TITLECOLOR>,                    
#  9     <SUBTITLECOLOR>,                       
# 10     <ANCHOR-X>,                            
# 11     <ANCHOR-Y>,                            
# 12     <ANCHOR-X-OFFSET>,                     
# 13     <ANCHOR-Y-OFFSET>,                     
# 14     <LINEHEIGHT>
# 15     <IMAGEBLUR>,                           
# 16     <LAYERNAME-1>,...<LAYERNAME-N> ]       
# )}}
#
# return a png-Filename
     
        

def generate(self, src, srcXML, param):
    # Catch the Params
    params = eval('['+self._(param.replace(' ','+'))+']')
    cachepath = sys.path[0]+"/assets/fanartcache"  
    stylepath = sys.path[0]+"/assets/templates/"+str(params[0])
    cachefile = createFileHandle(params)

    # Setup Background
    if params[3] != "":
      url = urllib.unquote(params[3])
      if os.path.isfile(stylepath+"/images/"+url):
        background = Image.open(stylepath+"/images/"+url)
      elif url[0][0] != "/": 
        try:
          bgfile = urllib2.urlopen(url)
        except urllib2.URLError, e:
          dprint(__name__, 1, 'error: {0}', str(e.code)+" "+e.msg+" // url:"+ url )  # Debug
          background = Image.open(stylepath+"/images/blank.jpg")  
        else:
          output = open(cachepath+"/tmp.png",'wb')
          output.write(bgfile.read())
          output.close()  
          background = Image.open(cachepath+"/tmp.png") 
    else:
      if os.path.isfile(stylepath+"/images/blank.jpg"):
        background = Image.open(stylepath+"/images/blank.jpg")
        background = background.convert('RGB') 
      
    # Already created?
    if os.path.isfile(cachepath+"/"+cachefile+".png"):
      return cachefile+".png" # Bye Bye  
    # No it's not
    else:             
      # Set Resolution and Merge Layers
      #if params[4] == "720":
      im = resizedMerge(background, params, stylepath) 
      #else: # 1080
       # im = resizedMerge(background, params, fanartpath)               
      # Setup Title Type Space
      if params[1] != None and params[1] != "":
        im = textToImage(1, im, params, stylepath)  
      # Setup Subtitle Type Space
      if params[2] != None and params[2] != "":
        im = textToImage(2, im, params, stylepath)  
      # Save to Cache
      im.save(cachepath+"/"+cachefile+".png")   
    return cachefile+".png"

def textToImage(index, im, params, stylepath):
    # Set Font      
    if params[5] != None and params[5] != "":  
      font = stylepath+"/"+params[5]
  #  else: # Default Font
   #   font = /OpenSans-Bold.ttf"  
    # Set Font Size
    if params[index+5] != None and params[index+5] != "": 
      fontsize = int(params[index+5])
    else: # Default Size
      if index == 2:
        fontsize = int(params[4]) / 36
      else:
        fontsize = int(params[4]) / 24
    # Set Color From Hex Value
    if params[index+7] != None and params[index+7] != "": 
      if is_hex(str(params[index+7])):
        textcolor = params[index+7]
        textcolor = tuple(int(textcolor[i:i+len(textcolor)/3], 16) for i in range(0, len(textcolor), len(textcolor)/3)) 
      else:
        textcolor = params[index+7]
    else: # Default Color
      textcolor = (255, 255, 255) 
    # Text & TypeSpace
    text = unicode(urllib.unquote(params[index]), 'utf-8').replace('+',' ').strip()
    draw = ImageDraw.Draw(im)
    width, height = draw.textsize(text, ImageFont.truetype(font, int(fontsize)))  
    

     
    if str(params[4])=="poster":
      renderwidth = 512
      renderheight = 768
    elif str(params[4])=="16X9":
      renderwidth = 768
      renderheight = 432
    elif str(params[4])=="flow":
      renderwidth = 768
      renderheight= 256 
    elif str(params[4])=="square":
      renderwidth = 768
      renderheight = 768
    else:
      renderwidth = 1280
      renderheight = 720
    # Anchor and Offset X
    if params[10] != None or params[10] != "" or params[12] != None or params[12] != "": 
      if params[10] == "right":
        offsetx = renderwidth - width - int(params[12])
      elif params[10] == "center":
        offsetx = ( renderwidth - width ) / 2
      elif params[10] == "left":
        offsetx = int(params[12])
      else:
       offsetx = 80
    else:
      offsetx = 80
    # Anchor and Offset Y
    if ( params[11] != None or params[11] != "" ) or ( params[13] != None or params[13] != "" ): 
      if params[11] == "bottom":
        offsety = renderheight - int(params[13])
      elif params[11] == "middle":
        offsety = ( renderheight - height ) / 2
      elif params[11] == "top" or params[11] == "":
        offsety = int(params[13])
      else:
        offsety = 80
      # Subtitle   
      
      if index > 1 and ( params[1] != None and params[1] != "" ):
        #title = unicode(urllib.unquote(params[1]), 'utf-8').replace('+',' ').strip()
        #titledraw = ImageDraw.Draw(im)
        if params[6] != None or params[6] != "": 
          titlefontsize = int(params[6])
        else: # Default Size
          titlefontsize = int(params[4]) / 24
        #titlewidth, titleheight = titledraw.textsize(title, ImageFont.truetype(font, int(titlefontsize)))
        if params[14] != None and params[14] != "":
          offsety = offsety + (titlefontsize * int(params[14]) / 100)
        else:
          offsety = offsety + (titlefontsize * 130 / 100)   
    else:
      offsety = 80    
    # Handle 1080 / atv3 Text
    if params[4] == "1080":
      fontsize = fullHDtext(fontsize)  
      offsetx = fullHDtext(offsetx)   
      offsety = fullHDtext(offsety)   
    # Write    
    draw.text((int(offsetx), int(offsety)), text , font=ImageFont.truetype(font, int(fontsize)), fill=textcolor)
    return im    

def resizedMerge (background, params, stylepath):
    isatv2=0
    
    if params[4] == "poster":
      height = 768
      width = 512
    elif params[4] == "16X9":
      height = 432
      width = 768     
    elif params[4] == "flow":
      height = 256
      width = 768 
    elif params[4] == "square":
      height = 768
      width = 768
    else:
      height = int(params[4])
      if height == 720:
        isatv2 = 1
        width = 1920
        height = 1080
      else:
        width = 1920
        
    
    im = Image.new("RGB", (width, height), "black")
    background = background.resize((width, height), Image.ANTIALIAS)

    # Blur BG
    if params[15] != None and params[15] != "":
      for i in range(0,int(params[15])):
        background = background.filter(ImageFilter.BLUR)
    im.paste(background, (0, 0), 0)
    # Layers    
    layerrange = range(16, len(params))
    for layercounter in layerrange:
      if params[layercounter] != None:
        layer = Image.open(stylepath+"/images/"+params[layercounter]+".png")
        layer = layer.resize((width, height), Image.ANTIALIAS)
        im.paste(layer, ( 0, 0),layer)
        
    if isatv2>0:
      im = im.resize((1280, 720), Image.ANTIALIAS)
    return im 







def createFileHandle(params):    
    cachefileStyle = normalizeString(params[0])
    cachefileTitle = normalizeString(params[1])
    cachefileSubtitle = normalizeString(params[2])
    cachefileRes = normalizeString(params[4])

    t1s = normalizeString(params[6])
    t1c = normalizeString(params[8])
    tax = normalizeString(params[10])
    tay = normalizeString(params[11])
    tox = normalizeString(params[12])
    toy = normalizeString(params[13])
    t2s = normalizeString(params[7])
    t2c = normalizeString(params[9])
    lh = normalizeString(params[14])
    
    # add layers
    layerrange = range(16, len(params))
    cachefileLayers = ""
    for layercounter in layerrange:
       if params[layercounter] != None:
         cachefileLayers = cachefileLayers+"+"+normalizeString(params[layercounter])   
    # fix for extra long subtitles 
    if len(cachefileSubtitle) > 30:
      cachefileSubtitle = cachefileSubtitle[0:30]    
    cachefile = cachefileStyle+"+"+cachefileLayers+"+"+cachefileTitle+"+"+t1s+"+"+t1c+"+"+tax+"+"+tay+"+"+tox+"+"+toy+"+"+cachefileSubtitle+"+"+t2s+"+"+t2c+"+"+lh+"+"+cachefileRes
    return cachefile






# HELPERS

def purgeFanart():
    folder = sys.path[0]+"/assets/fanartcache"
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception, e:
            print e



def normalizeString(text):
    text = urllib.unquote(str(text)).replace(' ','+')
    text = unicodedata.normalize('NFKD',unicode(text,"utf8")).encode("ascii","ignore")  # Only ASCII CHARS
    text = re.sub(r'\W+', '+', text) # No Special Chars  
    return text
    
def fullHDtext(number):
    number = int(number)*1080/720
    return number
    
def is_hex(s):
    hex_digits = set("0123456789abcdefABCDEF")
    for char in s:
        if not (char in hex_digits):
            return False
    return True
    
def remove_junk(url):
    temp = urllib.unquote(str(url))
    temp = temp.split('/')[-1]
    temp = temp.split('?')[0]
    temp = temp.split('&')[0]
    return temp