#!/usr/bin/env python2
# Author: Alamot
import os
import sys
import glob
import errno
import base64
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    def __init__(self, key, iv):
        self.key = key
        self.iv = iv

    def encrypt(self, source):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padding = AES.block_size - len(source) % AES.block_size 
        data = source + chr(padding) * padding
        return base64.b64encode(cipher.encrypt(data))

    def decrypt(self, source):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        data = cipher.decrypt(base64.b64decode(source))
        padding = ord(data[-1])
        if data[-padding:] != chr(padding) * padding:
            raise ValueError("Invalid padding...")
        return data[:-padding]


def makedir(directory):
    ''' Make a directory. '''
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            print("[E] makedir")


if len(sys.argv) < 5 or sys.argv[1] not in ["dec", "enc"]:
    print("Usage: python cordova-aes.py <enc/dec> <secret_key> <iv_value> <file(s)>")
    sys.exit(1)

action = sys.argv[1]
key = sys.argv[2]
iv = sys.argv[3]
files = sys.argv[4:]
cipher = AESCipher(key, iv)

makedir(action)

if type(files) == str:
    files = [files]
    
for filename in files:
    out_path = action + "/" + filename
    with open(filename, 'r') as inf:
        data = inf.read()
    if action == "dec":
        data = data.replace('\n', '')
        with open(out_path, "w") as f:
            f.write(cipher.decrypt(data))
        print("[+] Decrypted data have been written into '" + out_path + "'")
    elif action == "enc":
        with open(out_path, "w") as f:
            f.write(cipher.encrypt(data))
        print("[+] Encrypted data have been written into '" + out_path + "'")
