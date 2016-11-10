#!/usr/bin/env python
'''
*******************************************************************************
 Description: This tool can help you determine the character
               encoding of a text file by converting one line from
               the file to every(?) possible character encoding.
               It writes the converted lines to a new text file
               using the same filename but appending the
               extension '.encodings' to it. 
               You have to examine this file visually to find the  
               correct encoding.                                   
                                                                   
  Usage      : test_encodings.py filename [number of line to test] 
                                                                   
  Licence    : Public Domain.                                      
                                                                   
  Author     : Antonios Tsolis (2016)                              
*******************************************************************************
'''

import io
import os
import sys
from encodings.aliases import aliases

encs = {
    "ascii", "big5", "big5hkscs",
    "cp037", "cp424", "cp437", "cp500", "cp720", "cp737", "cp775",
    "cp850", "cp852", "cp855", "cp856", "cp857", "cp858", "cp860",
    "cp861", "cp862", "cp863", "cp864", "cp865", "cp866", "cp869",
    "cp874", "cp875", "cp932", "cp949", "cp950",
    "cp1006", "cp1026", "cp1140", "cp1250", "cp1251", "cp1252",
    "cp1253", "cp1254", "cp1255", "cp1256", "cp1257", "cp1258",
    "euc_jp", "euc_jis_2004", "euc_jisx0213", "euc_kr",
    "gb2312", "gbk", "gb18030", "hz",
    "iso2022_jp", "iso2022_jp_1", "iso2022_jp_2", "iso2022_jp_2004",
    "iso2022_jp_3", "iso2022_jp_ext", "iso2022_kr",
    "latin_1", "iso8859_2", "iso8859_3", "iso8859_4", "iso8859_5",
    "iso8859_6", "iso8859_7", "iso8859_8", "iso8859_9", "iso8859_10",
    "iso8859_13", "iso8859_14", "iso8859_15", "iso8859_16",
    "johab", "koi8_r", "koi8_u",
    "mac_cyrillic", "mac_greek", "mac_iceland",
    "mac_latin2", "mac_roman", "mac_turkish",
    "ptcp154", "shift_jis", "shift_jis_2004", "shift_jisx0213",
    "utf_32", "utf_32_be", "utf_32_le",
    "utf_16", "utf_16_be", "utf_16_le",
    "utf_7", "utf_8", "utf_8_sig",
    "idna", "mbcs", "palmos", "punycode", "rot_13",
    "raw_unicode_escape", "unicode_escape", "unicode_internal",
    "base64_codec", "bz2_codec", "hex_codec", "uu_codec", "zlib_codec"
}


def write_encodings(filename, line_number, final_encoding):
    # To ensure that we cover as many as possible encodings,
    # we take the union between our predefined encoding set and the
    # set of the values from the encodings.aliases.aliases.
    encodings = encs.union(set(aliases.values()))

    data = dict()

    # Read line from file
    try:
        with io.open(filename, "rb") as f:
            lines = f.readlines()
            line = lines[line_number-1]
            print("\nProcessing line number: " + str(line_number))
            if len(line) < 3:
                print("!!!Warning!!!: Possible empty line.")
            print("")
    except Exception:
        _, err, _ = sys.exc_info()
        print("Error reading " + filename)
        print(err)
        sys.exit(1)

    # Decode it using every possible encoding
    for enc in encodings:
        try:
            data[enc] = line.decode(enc)
        except Exception:
            _, err, _ = sys.exc_info()
            print("Cannot decode using " + enc)
            # print(err)

    # We write the results in a new utf-8 text file
    # We use the same filename + an '.encodings' extension
    fpath = os.path.abspath(filename)
    newfilename = fpath + '.encodings'
    print("\nWriting successfully tested encodings in " + newfilename)

    with open(newfilename, 'w') as out:
        c = 0
        for enc in sorted(data.keys()):
            try:
                out.write("%-20s" % enc)
                if (sys.version_info[0] < 3):
                    line = data[enc].encode(final_encoding)
                else:
                    line = data[enc]
                out.write(line)
                out.write(os.linesep)
                c += 1
            except Exception:
                _, err, _ = sys.exc_info()
                print("Cannot encode " + enc + " to " + final_encoding)
                # print(err)

    print("\n" + str(c) + " out of " + str(len(encodings)) +
          " tested encodings were written.\n")


if __name__ == '__main__':
    nargs = len(sys.argv)-1
    if nargs < 1 or nargs > 2:
        exit("Usage: test_encodings.py filename [number of line to test]")
    if nargs == 2:
        line_number = int(sys.argv[2])
    else:
        line_number = 1
    write_encodings(sys.argv[1], line_number, 'utf_8')
