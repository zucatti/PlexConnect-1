#!/usr/bin/env python


import SimpleHTTPServer
import os
import SocketServer
import socket
import logging
import cgi
import getpass
import subprocess
import sys
import signal
import time
import certificates
from subprocess import call,Popen, PIPE
import webbrowser
from shutil import copyfile
import urllib2
import struct
from PlexConnect import cmdShutdown, shutdown

mypid = os.getpid()

def localIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('1.2.3.4', 1000))
    return s.getsockname()[0]

def delete_command():
    global delete_file
    if os.name == "posix":
        delete_file = "rm "
    else:
        delete_file = "del "

def startup_init(): 
    
    if os.path.exists("connector.txt"): # webserver still up ?
        url = "http://"+str(localIP())+":"

        # webserver still running on [port] ? if yes, open browser directly
        try: 
            output = Popen("cat connector.txt", shell=True, stdout=PIPE).communicate()[0]
            url = url + str(output.strip()) # connector.txt contains port number
            urllib2.urlopen(url)
            start_browser(url)
        except urllib2.URLError, (err): # start up
            print("PlexConnector: status cannot be determined. retrying ")
            removefiles = Popen(delete_file+"connector.txt", shell=True,stderr=PIPE,stdout=PIPE).communicate()
            startup_init()
    else:
        set_platform()
        start_webserver()


def start_browser(url):

    # try opening local webbrowser if available
    try: 
        print("PlexConnector: Opening: "+url)
        webbrowser.get()
        webbrowser.open_new(url)
    except:
        print("PlexConnector: No default browser found.\nOpen: "+url+" in a browser")  


def set_platform():

    global plexconnectpath
  
    cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
 
    if sys.platform.startswith('darwin'): # OSX
        plexconnectpath = cwd+"/PlexConnect_daemon.bash "
        call("echo 1 >daemon_support.txt",shell=True)
        call("launchctl list | grep -c plexconnect >daemon_installed.txt",shell=True) #outputs: 0=not installed,1=daemon installed 
    
    elif sys.platform.startswith('win32'):
        
        if controlsupport == True:
            
            plexconnectpath = "python PlexConnect_WinService.py "
            call("echo 1 >daemon_support.txt",shell=True)
            output = Popen("sc query PlexConnect-service", shell=True, stdout=PIPE).communicate()[0]
            if output.find("FAILED") > 0:
                call("echo 0 >daemon_installed.txt",shell=True)   
            else:
                call("echo 1 >daemon_installed.txt",shell=True)   

        else:
            plexconnectpath = "start /B pythonw PlexConnect.py"
            call("echo 0 >daemon_installed.txt",shell=True)
            call("echo 0 >daemon_installed.txt",shell=True)  

    else: # linux
        plexconnectpath = cwd+"/PlexConnect_daemon.bash "
        call("echo 0 >daemon_support.txt",shell=True)
        call("echo 0 >daemon_installed.txt",shell=True)


def start_webserver():

    global server
    global httpd
    global port
        
    if os.path.isfile("Settings.cfg"): # show wizard if settings.cfg not exists
        plexconnect_status(localIP())
    else:
        call("echo PlexConnect is not running > plexconnect_status.txt",shell=True)

    copyfile("./support/setup/index.html", "./index.html")
    RequestHandler = ServerHandler
    
    while True:
        try:
            httpd = SocketServer.TCPServer(("", port), RequestHandler)
            signal.signal(signal.SIGINT, sig_handler)
            signal.signal(signal.SIGTERM, sig_handler)

            url = "http://"+localIP()+":"+str(port) 
            start_browser(url)
            call("echo "+str(port)+" > connector.txt",shell=True)
            httpd.serve_forever()
            break
        except KeyboardInterrupt:
            break
        except IOError as e:
                port = port+1 # just try next port - possible TIME_WAIT
                continue
        break

def plexconnect_status(host):

    if os.name == "posix":
        call(plexconnectpath+" status > plexconnect_status.txt",shell=True)
    else: #win32
        
        output = Popen("sc query PlexConnect-service", shell=True, stdout=PIPE).communicate()[0]

        if output.find("FAILED") > 0:
            command = Popen("tasklist /FI \"IMAGENAME eq pythonw.exe\" /NH ", shell=True, stderr=PIPE,stdout=PIPE).communicate()[0]
            time.sleep(1)

            if len(command) > 81:
                call("echo PlexConnect is running > plexconnect_status.txt",shell=True)
            else:
                call("echo PlexConnect is not running > plexconnect_status.txt",shell=True)

        else:
            if output.find("STOPPED") > 0:
                call("echo PlexConnect is not running > plexconnect_status.txt",shell=True)
            else:
                call("echo PlexConnect is running > plexconnect_status.txt",shell=True)

    time.sleep(2)
   

def plexconnect_control(control):
    global controlsupport
    if control == "install" or control == "uninstall" or control == "remove":
        if sys.platform.startswith('darwin'): #OSX specific
            command = Popen("./support/OSX/"+control+".bash", shell=True, stderr=PIPE,stdout=PIPE).communicate()[0] 
            time.sleep(2) # actions may still be in progress  
        else:
            if sys.platform.startswith('win32') and control == "remove":
                call(plexconnectpath+"stop", shell=True)
                time.sleep(3)
                call(plexconnectpath+control, shell=True)
                print("win "+plexconnectpath+":"+control)
 
            else:
                call(plexconnectpath+control, shell=True)
    else:
        if os.name == "posix": # OSX / Linux flavors
            command = Popen(plexconnectpath+control, shell=True, stderr=PIPE,stdout=PIPE).communicate()[0] 
        else: # win 32
            if controlsupport == False and control == "stop":
                cmdShutdown()
                shutdown()
                time.sleep(2)
                command = Popen("taskkill /FI \"IMAGENAME eq pythonw.exe\" /F", shell=True, stderr=PIPE,stdout=PIPE).communicate()[0] 
                call("echo PlexConnect is not running > plexconnect_status.txt",shell=True)
            if controlsupport == False and control == "start":
                    
                proc = Popen(["start.bat"],shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(2)
                call("echo PlexConnect is running > plexconnect_status.txt",shell=True)

            if controlsupport == True and control == "start":
                output = Popen("sc query PlexConnect-service", shell=True, stdout=PIPE).communicate()[0]

                if output.find("FAILED") > 0:
                    command = Popen(plexconnectpath+" install", shell=True, stderr=PIPE,stdout=PIPE).communicate()[0]  
                    time.sleep(3)
                    command = Popen(plexconnectpath+control, shell=True, stderr=PIPE,stdout=PIPE).communicate()[0] 
                    time.sleep(3)
                else:
                    command = Popen(plexconnectpath+control, shell=True, stderr=PIPE,stdout=PIPE).communicate()[0]
            else:
                    command = Popen(plexconnectpath+control, shell=True, stderr=PIPE,stdout=PIPE).communicate()[0]
                    call("echo PlexConnect is not running > plexconnect_status.txt",shell=True)

   
    time.sleep(2)
    set_platform() # update all proper programfile & paths        
    time.sleep(2)    
    plexconnect_status(localIP)

def cleanup():
    print("PlexConnector: Shutting down GUI")
    files = "daemon_support.txt daemon_installed.txt connector.txt plexconnect_status.txt"
    removefiles = Popen(delete_file + files, shell=True,stderr=PIPE,stdout=PIPE).communicate()
    time.sleep(3)
    

def sig_handler(signum, frame):
    cleanup()    
    
    if os.name == "posix":
        try:
            command = Popen("ps -ef | grep -i Plexconnect_OSX_Setup | grep -v grep | cut -d \" \" -f4", shell=True, stderr=PIPE,stdout=PIPE).communicate()[0]
            if len(command)>0:
                endapp= call("kill -9 "+command, shell=True)
        except:
            print("PlexConnector: Stopped.")

    try:
        os.kill(mypid,signal.SIGKILL)
    except:
        os.kill(mypid,signal.SIGTERM)


class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def log_message(self, format, *args):
        return

    def do_POST(self):

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
        })

        if "start" not in form and "stop" not in form and "kill" not in form:
            if "config" in form:
                # save config
                f = open("Settings.cfg", "w")
                f.write(form.getvalue("config"))
                f.close()
                if "boot" not in form:
                    plexconnect_control("restart")
            if "boot" in form:  # install as daemon; value=install|uninstall
                if form.getvalue("boot") == "uninstall" and sys.platform.startswith('win32'):
                    plexconnect_control("remove")        
                else:
                    plexconnect_control(form.getvalue("boot")) 
        elif "stop" in form:
            plexconnect_control("stop")
        elif "start" in form:
            plexconnect_control("start")
        elif "kill" in form:
            sig_handler("kill","kill")
            # os._exit(1)
        if "kill" not in form:
            set_platform()
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)



if __name__=="__main__":

    global controlsupport
    delete_command()

    if os.name.startswith('posix'):

        if not os.geteuid()==0:
            sys.exit("PlexConnector error: Root privileges required\nUsage: sudo ./setup.py (port - optional)\n")
        else:
            print("PlexConnector: "+ sys.platform +" "+str(struct.calcsize("P") * 8)+"-bit")
    else:

        try: 
            import win32service
        except:
            sys.exit("PlexConnector error: pywin32 not installed.\nDownload and install from: http://sourceforge.net/projects/pywin32/files/pywin32/")
        else:
            controlsupport = True

    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 8080

    startup_init()



    
