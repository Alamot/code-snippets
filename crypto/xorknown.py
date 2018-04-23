#!/usr/bin/env python2
# Author: Alamot
# This is a XOR plaintext attack tool: If we know a part of the plaintext maybe
# we can recover the key and the whole text.
from __future__ import print_function
from __future__ import division
import string, sys


ignore_code = 0xff
printable_key = True
max_key_length = 21


def is_printable(text, ignore_code):
    ''' Function to check if every character in text is printable '''
    for ch in text:
        if ord(ch) == ignore_code:
            continue
        if ch not in string.printable:
            return False
    return True


def lrotate(s, d):
    ''' Function to rotate string left by d length '''
    return s[d:] + s[0:d]

    
if len(sys.argv) < 2 or sys.argv[1].strip().lower() == "--help":
    print("Known-plaintext attack:\n"+sys.argv[0]+" <encrypted file> <known plaintext> [max_key_length]")
    print("\nDecrypt using known key:\n"+sys.argv[0]+" <encrypted file> --key=the_known_key")
    exit()

filename = sys.argv[1]

if sys.argv[2].strip().lower()[:5] == "--key":
    known_key = sys.argv[2].strip()[6:]
    with open(filename, "rb") as f:
        data = f.read()
    decrypted_text = ""
    repeated_key = (known_key)*((len(data) // len(known_key)) + 1)
    for x in range(len(data)):
        decrypted_text += chr(ord(data[x]) ^ ord(repeated_key[x]))
    print("Key length: "+str(len(known_key)), "\nPartial Key: "+known_key, "\nPlaintext: "+decrypted_text)
    exit()
else:
    known_plaintext = sys.argv[2]

if len(known_plaintext) > max_key_length:
    print("The length of the known plaintext is greater than max_key_length (="+str(max_key_length)+"). Please give a smaller plaintext or incrase max_key_length.")
    exit()
    
if len(sys.argv) > 3:
    max_key_length = int(sys.argv[3])+1
    
with open(filename, "rb") as f:
    data = f.read()

print("Searching XOR-encrypted "+filename+" for string '"+known_plaintext+"' (max_key_length = "+str(max_key_length-1)+")")

try:    
    for i in range(len(data)-len(known_plaintext)): # Try known plaintext in every position
        partial_key = ""
        for j in range(len(known_plaintext)):
            if known_plaintext[j] == ignore_code:
                partial_key += chr(ignore_code)
            else:
                partial_key += chr(ord(data[i+j]) ^ ord(known_plaintext[j]))
        #print("Single key: "+partial_key)
        if is_printable(partial_key, ignore_code) or not printable_key:
            for n in range(len(partial_key), max_key_length): # Try different key lengths
                for m in range(n):                            # Try different partial key positions
                    expanded_key = lrotate(partial_key+chr(ignore_code)*(n-len(partial_key)), m)
                    #print(expanded_key, m)
                    repeated_key = (expanded_key)*((len(data) // len(expanded_key)) + 1)
                    decrypted_text = ""
                    for x in range(len(data)): # Try to decrypt the encoded text
                        if ord(repeated_key[x]) == ignore_code:
                            decrypted_text += chr(ignore_code)
                        else:
                            decrypted_text += chr(ord(data[x]) ^ ord(repeated_key[x]))
                    if is_printable(decrypted_text, ignore_code): # Is the whole result printable?
                        if known_plaintext in decrypted_text:
                            print("Key length: "+str(len(expanded_key)), "\nPartial Key: "+expanded_key, "\nPlaintext: "+decrypted_text)
                            print("")
except KeyboardInterrupt:
    print("\nCtrl+C received. Exiting...")
    exit()
