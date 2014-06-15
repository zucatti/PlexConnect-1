#!/usr/bin/env python
import urllib
import urllib2
import os
import subprocess
import sys
sys.stdout.flush()

def getcertificate(cn,certfile):
  # use openssl on nix-platforms
  if os.name == "posix":
    certpath = "./assets/certificates/"
    if not os.path.isfile(certpath+certfile+".pem"):
      #print("Generating certificate for "+cn+" (openssl)")
      devnull = open('/dev/null', 'w')
      subprocess.Popen("openssl req -new -nodes -newkey rsa:2048 -outform pem -out "+certpath+certfile+".cer -keyout "+certpath+certfile+".key -x509 -days 3650 -subj \"/C=US/CN="+cn+"\";cat "+certpath+certfile+".cer "+certpath+certfile+".key >> "+certpath+certfile+".pem",stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
  
  #windows generates certificates online
  else:
    certpath = "assets\\certificates\\"
    if not os.path.isfile(certpath+certfile+".pem"):
      print("Generating certificate for "+cn)
      url = "http://www.selfsignedcertificate.com"
      post_data_dictionary = {'common_name':cn}
      post_data_encoded = urllib.urlencode(post_data_dictionary)

      request_object = urllib2.Request(url, post_data_encoded)

      response = urllib2.urlopen(request_object)
      html_string = response.read()

      #html_string = urllib.urlopen("http://www.selfsignedcertificate.com").read()
      sane = 0
      needlestack = []
      while sane == 0:
        curpos = html_string.find("href")
        if curpos >= 0:
          html_stringlen = len(html_string)
          html_string = html_string[curpos:html_stringlen]
          curpos = html_string.find('"')
          html_stringlen = len(html_string)
          html_string = html_string[curpos+1:html_stringlen]
          curpos = html_string.find('"')
          needle = html_string[0:curpos]
          
          if needle.startswith("download"):
            needlestack.append(needle)
        
        else:
          sane = 1
      f = open(certpath+certfile+'.pem', 'w')
      for item in reversed(needlestack):
        
        certresponse = urllib2.urlopen("http://www.selfsignedcertificate.com/"+item)
        certoutput = certresponse.read()
        if "key" in item:
          c = open(certpath+certfile+'.key', 'w')
          c.write(certoutput)
          c.close()
        if "cert" in item:
          c = open(certpath+certfile+'.cer', 'w')
          c.write(certoutput)
          c.close()
          
        f.write(certoutput)
      f.close
  
# commonname, output file

getcertificate("trailers.apple.com","trailers")
getcertificate("www.icloud.com","imovie")
getcertificate("secure.marketwatch.com","wsj")