# Author: Alamot
import os
import sys
import glob
import json
import argparse
from zipfile import ZipFile
from collections import defaultdict


# Some powerful groups to IGNORE in our analysis
POWERFUL_GROUPS = {"ADMINISTRATORS", "DOMAIN ADMINS", "ENTERPRISE ADMINS",
                   "ENTERPRISE KEY ADMINS", "KEY ADMINS", "ACCOUNT OPERATORS",
                   "DOMAIN CONTROLLERS", "ENTERPRISE DOMAIN CONTROLLERS",
                   "ENTERPRISE READ-ONLY DOMAIN CONTROLLERS",
                   "RAS AND IAS SERVERS"}

# BloodHound data types
DATA_TYPES = {"computers", "containers", "domains", "gpos", "groups", "ous", "users"}


# We use this custom class for missing OID values
class KeyDefaultDict(dict):
    def __missing__(self, key):
        return {"name":key}


# Some dicts we will use to store the data
users = dict()
groups = dict()
oids = KeyDefaultDict()
rights = defaultdict(dict)

special_issues = {"unconstraineddelegation":set(),
                  "trustedtoauth":set(),
                  "passwordnotreqd":set(),
                  "dontreqpreauth":set(),
                  "userpassword":set()}

special_users = {"AllowedToDelegate":set(),
                 "DcomUsers":set(),
                 "LocalAdmins":set(),
                 "PSRemoteUsers":set(),
                 "PrivilegedSessions":set(),
                 "RegistrySessions":set(),
                 "RemoteDesktopUsers":set()}


def process_json(json_data, name):
    ''' Process Bloodhound json and store interesting data '''
    # Process and store users
    if json_data["meta"]["type"] == "users":
        for entry in json_data["data"]:
            # Process and store AllowedToDelegate
            if entry["AllowedToDelegate"]:
                for x in entry["AllowedToDelegate"]:
                    name_field = name if name in entry["Properties"] else "name"
                    special_users["AllowedToDelegate"].add((entry["Properties"][name_field], x["ObjectIdentifier"]))
            # Process and store any other special issue
            for key in special_issues.keys():
                if key in entry["Properties"] and entry["Properties"][key]:
                    name_field = name if name in entry["Properties"] else "name"
                    special_issues[key].add(entry["Properties"][name_field])
    # Process and store computers
    elif json_data["meta"]["type"] == "computers":
        for entry in json_data["data"]:
            # Process and store AllowedToDelegate
            if entry["AllowedToDelegate"]:
                for x in entry["AllowedToDelegate"]:
                    name_field = name if name in entry["Properties"] else "name"
                    special_users["AllowedToDelegate"].add((entry["Properties"][name_field], x["ObjectIdentifier"]))
            # Process and store unconstraineddelegation and trustedtoauth
            for key in ["unconstraineddelegation", "trustedtoauth"]:
                if key in entry["Properties"] and entry["Properties"][key]:
                    name_field = name if name in entry["Properties"] else "name"
                    special_issues[key].add(entry["Properties"][name_field])
            # Process and store special users
            for key in special_users.keys():
                if "Results" in entry[key] and entry[key]["Results"]:
                    for x in entry[key]["Results"]:
                        name_field = name if name in entry["Properties"] else "name"
                        special_users[key].add((entry["Properties"][name_field], x["ObjectIdentifier"]))
    # Store groups and group members
    elif json_data["meta"]["type"] == "groups":
        for entry in json_data["data"]:
            groups[entry["ObjectIdentifier"]] = entry["Members"]
    # Process and store rights
    if any(x == json_data["meta"]["type"] for x in DATA_TYPES):
        for entry in json_data["data"]:
            oids[entry["ObjectIdentifier"]] = entry["Properties"]
            for x in entry["Aces"]:
                rights[x["RightName"]][x["PrincipalSID"]] = entry["ObjectIdentifier"]


def main():
    ''' Main function '''
    parser = argparse.ArgumentParser(description="A tool that analyzes BloodHound data and outputs interesting findings.")
    parser.add_argument("filepath", help="BloodHound zip archive or path to JSON files.")
    parser.add_argument("-p", "--highvalue", dest="highvalue_only", action='store_true',  help="Show only findings with high value targets.")
    parser.add_argument("-n", "--name", dest="name", default='name',  help="Print [name|distinguishedname|samaccountname] (default: %(default)s)")
    args = parser.parse_args()
    if not os.path.exists(args.filepath):
        sys.exit("Cannot find input path: " + args.filepath)
    name, ext = os.path.splitext(args.filepath)

    print("================================ PROCESSING ==================================")

    if ext == ".zip":
        zf = ZipFile(args.filepath)
        for filename in zf.namelist():
            if not filename.endswith('.json'):
                continue
            print("Processing", filename)
            with zf.open(filename) as f:
                json_data = json.loads(f.read())
            # Process BloodHound json and store interersting data
            process_json(json_data, args.name)
    else:
        for filepath in glob.glob(args.filepath + "/*.json"):
            print("Processing", filepath)
            with open(filepath, "rt") as f:
                json_data = json.loads(f.read())
            # Process BloodHound json and store interersting data
            process_json(json_data, args.name)

    print()
    print("*************************** INTERESTING FINDINGS *****************************")

    # Print special issues
    for key in special_issues.keys():
        if special_issues[key]:
            for x in special_issues[key]:
                print(key + ":", x)

    # Print special users
    for key in special_users.keys():
        for x in special_users[key]:
            if any(group in oids[x[1]]["name"] for group in POWERFUL_GROUPS):
                continue
            print(key + ":", oids[x[1]][args.name], "->", x[0])

    # Print rights:
    for right in sorted(rights.keys()):
        for x in sorted(rights[right].keys()):
            src_name = args.name if args.name in oids[x] else "name"
            dst_name = args.name if args.name in oids[rights[right][x]] else "name"
            # Ignore powerful groups
            if any(group in oids[x]["name"] for group in POWERFUL_GROUPS):
                continue
            # Ignore non-high value targets if the user set the arg
            if args.highvalue_only and ("highvalue" in oids[rights[right][x]]) and (not oids[rights[right][x]]["highvalue"]):
                continue
            src = oids[x][src_name]
            if x in groups and groups[x]:
                src += " ("
                members = set()
                for member in groups[x]:
                    oid = member["ObjectIdentifier"]
                    name_field = args.name if args.name in oids[oid] else "name"
                    members.add(oids[oid][name_field])
                src += ', '.join(members)
                src += ")"
            print(right + ":", src, "->", oids[rights[right][x]][dst_name])


if __name__ == '__main__':
    main()
