#!/usr/bin/env python2
# Author: Alamot
# This is a XOR plaintext attack tool: If we know a part of the plaintext maybe
# we can recover the key and the whole text in successive steps.
from __future__ import print_function
from __future__ import division
import string, sys

max_key_length = 20
ignore_code = 0xff
printable_key = True


def is_printable(text, ignore_code):
    for ch in text:
        if ord(ch) == ignore_code:
            continue
        if ch not in string.printable:
            return False
    return True
    
    
if len(sys.argv) < 2:
    print("Usage: "+sys.argv[0]+"<filename> <known plaintext>")
    exit()

filename = sys.argv[1]
known_plaintext = sys.argv[2]
    
with open(filename, "rb") as f:
    data = f.read()

print("Searching XOR-encrypted "+filename+" for string '"+known_plaintext+"'")
    
for i in range(len(data)-len(known_plaintext)):
    partial_key = ""
    for j in range(len(known_plaintext)):
        if known_plaintext[j] == ignore_code:
            partial_key += chr(ignore_code)
        else:
            partial_key += chr(ord(data[i+j]) ^ ord(known_plaintext[j]))
    #print("Single key: "+partial_key)
    padding = ((i+len(known_plaintext))%len(known_plaintext))
    if not printable_key or is_printable(partial_key, ignore_code):
        for n in range(len(partial_key), max_key_length):    #try different key lengths
            for m in range(max_key_length-len(partial_key)): #try different partial key positions
                expanded_key = chr(ignore_code)*m+partial_key+chr(ignore_code)*(n-len(partial_key)-m)
                repeated_key = (expanded_key)*((len(data) // len(expanded_key)) + 1)
                #print("Repeated key: "+repeated_key)
                decrypted_text = ""
                for x in range(len(data)):
                    if ord(repeated_key[x]) == ignore_code:
                        decrypted_text += chr(ignore_code)
                    else:
                        decrypted_text += chr(ord(data[x]) ^ ord(repeated_key[x]))
                if is_printable(decrypted_text, ignore_code):
                    print("Key length: "+str(len(expanded_key)), "\nPartial Key: "+expanded_key, "\nPlaintext: "+decrypted_text)
                    print("")
    
