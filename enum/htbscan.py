#!/usr/bin/env python
# Author: Alamots
import subprocess, re, sys

ip = "127.0.0.1"
max_rate = "500"
ports = "0-65535"

if len(sys.argv) > 1:
    ip = sys.argv[1]
else:
    print("Usage: "+sys.argv[0]+" <IP> [max_rate] [ports]")
    exit()

if len(sys.argv) > 2:
    max_rate = sys.argv[2]

if len(sys.argv) > 3:
    ports = sys.argv[3]


# Running masscan
cmd = ["sudo", "masscan", "-e", "tun0", "-p"+ports, "--max-rate", max_rate, "--interactive", ip]
print("\nRunning command: "+' '.join(cmd))
sp = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
output = ""
while True:
    out = sp.stdout.read(1).decode('utf-8')
    if out == '' and sp.poll() != None:
        break
    if out != '':
        output += out
        sys.stdout.write(out)
        sys.stdout.flush()

# Getting discovered ports from the masscan output and sorting them
results = re.findall('port (\d*)', output)
if results:
    ports = list({int(port) for port in results})
    ports.sort()
    # Running nmap
    cmd = ["sudo", "nmap", "-A", "-p"+''.join(str(ports)[1:-1].split()), ip]
    print("\nRunning command: "+' '.join(cmd)+"\n")
    sp = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = ""
    while True:
        out = sp.stdout.read(1).decode('utf-8')
        if out == '' and sp.poll() != None:
            break
        if out != '':
            output += out
            sys.stdout.write(out)
            sys.stdout.flush()
    
