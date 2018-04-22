#!/usr/bin/env python2
# Author: Alamot
# This is a XOR plaintext attack tool: If we know a part of the plaintext maybe
# we can recover the key and the whole text in successive steps.
from __future__ import print_function
from __future__ import division
import string, sys


ignore_code = 0xff
printable_key = True
max_key_length = 21


def is_printable(text, ignore_code):
    for ch in text:
        if ord(ch) == ignore_code:
            continue
        if ch not in string.printable:
            return False
    return True


def lrotate(s, d):
    ''' Function to rotate string left by d length '''
    return s[d:] + s[0:d]

    
if len(sys.argv) < 2:
    print("Usage: "+sys.argv[0]+"<filename> <known plaintext> [max_key_length]")
    exit()

filename = sys.argv[1]
known_plaintext = sys.argv[2]
if len(known_plaintext) > max_key_length:
    print("The length of the known plaintext is greater than max_key_length (="+str(max_key_length)+"). Please give a smaller plaintext or incrase max_key_length.")
    exit()
if len(sys.argv) > 3:
    print(len(sys.argv))
    max_key_length = int(sys.argv[3])+1
    
with open(filename, "rb") as f:
    data = f.read()

print("Searching XOR-encrypted "+filename+" for string '"+known_plaintext+"'")

try:    
    for i in range(len(data)-len(known_plaintext)):
        partial_key = ""
        for j in range(len(known_plaintext)):
            if known_plaintext[j] == ignore_code:
                partial_key += chr(ignore_code)
            else:
                partial_key += chr(ord(data[i+j]) ^ ord(known_plaintext[j]))
        #print("Single key: "+partial_key)
        if is_printable(partial_key, ignore_code) or not printable_key:
            for n in range(len(partial_key), max_key_length):    #try different key lengths
                for m in range(n): #try different partial key positions
                    expanded_key = lrotate(partial_key+chr(ignore_code)*(n-len(partial_key)), m)
                    #print(expanded_key, m)
                    repeated_key = (expanded_key)*((len(data) // len(expanded_key)) + 1)
                    decrypted_text = ""
                    for x in range(len(data)):
                        if ord(repeated_key[x]) == ignore_code:
                            decrypted_text += chr(ignore_code)
                        else:
                            decrypted_text += chr(ord(data[x]) ^ ord(repeated_key[x]))
                    if is_printable(decrypted_text, ignore_code):
                        print("Key length: "+str(len(expanded_key)), "\nPartial Key: "+expanded_key, "\nPlaintext: "+decrypted_text)
                        print("")
except KeyboardInterrupt:
    print("\nCtrl+C received. Exiting...")
    exit()
