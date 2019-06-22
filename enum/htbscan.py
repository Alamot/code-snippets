#!/usr/bin/env python
# Author: Alamot
import argparse
import re
import subprocess
import sys


def run_command(command):
    print("\nRunning command: "+' '.join(command))
    sp = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = ""
    while True:
        out = sp.stdout.read(1).decode('utf-8')
        if out == '' and sp.poll() != None:
            break
        if out != '':
            output += out
            sys.stdout.write(out)
            sys.stdout.flush()
    return output
 

def enum(ip, ports, max_rate, outfile=None):
    # Running masscan
    cmd = ["sudo", "masscan", "-e", "tun0", "-p" + ports,
           "--max-rate", str(max_rate), "--interactive", ip]
    output = run_command(cmd)
    if outfile:
        for line in output.splitlines():
            if "rate:" not in line: # Don't write 'rate:' lines
                outfile.write(line + "\n")
        outfile.flush()

    # Get discovered TCP ports from the masscan output, sort them and run nmap for those
    results = re.findall('port (\d*)/tcp', output)
    if results:
        tcp_ports = list({int(port) for port in results})
        tcp_ports.sort()
        tcp_ports = ''.join(str(tcp_ports)[1:-1].split())
        # Running nmap
        cmd = ["sudo", "nmap", "-A", "-p"+tcp_ports, ip]
        output = run_command(cmd)
        if outfile:
            outfile.write(output)
            outfile.flush()

    # Get discovered UDP ports from the masscan output, sort them and run nmap for those
    results = re.findall('port (\d*)/udp', output)
    if results:
        udp_ports = list({int(port) for port in results})
        udp_ports.sort()
        udp_ports = ''.join(str(udp_ports)[1:-1].split())
        # Running nmap
        cmd = ["sudo", "nmap", "-A", "-sU", "-p"+udp_ports, ip]
        output = run_command(cmd)
        if outfile:
            outfile.write(output)
            outfile.flush()


def main():
    parser = argparse.ArgumentParser(description="Port/Service enumaration tool.")
    parser.add_argument("IP",  help="IP address to scan.")
    parser.add_argument("-tp", "--tcp-ports", dest="tcp_ports", default="1-65535", help="List of ports/port ranges to scan (TCP only).")
    parser.add_argument("-up", "--udp-ports", dest="udp_ports", default="1-65535", help="List of ports/port ranges to scan (UDP only).")
    parser.add_argument("-r", "--max-rate", dest="max_rate", default=500, type=int, help="Send packets no faster than <number> per second")
    parser.add_argument("-o", "--output", dest="outfile", help="File to write output to.")
    args = parser.parse_args()
    
    # Construct ports string
    ports = ""
    tcp = args.tcp_ports and args.tcp_ports.lower() not in ["0", "None"]
    udp = args.udp_ports and args.udp_ports.lower() not in ["0", "None"]
    if tcp:
        ports += args.tcp_ports
    if tcp and udp:
        ports += ","
    if udp:
        ports += "U:" + args.udp_ports
        
    # Write to file?
    if args.outfile:
        with open(args.outfile, "at") as outfile:
            enum(args.IP, ports, args.max_rate, outfile)
    else:
        enum(args.IP, ports, args.max_rate)
        
    
if __name__ == "__main__":
    main()
