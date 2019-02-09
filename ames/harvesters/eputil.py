#
# eputil.py is a Python 3.7 wrapper for the Go eprinttools
# eputil command line program.
# 
# For Go package see https://github.com/caltechlibrary/eprinttools.
#
import os
import json
import sys
from subprocess import run, Popen, PIPE
from datetime import datetime, timedelta


#
# get_eprint_keys  returns a list of keys available from the
# EPrints rest API indicated in the provided eprint_url. 
#
# The eprint_url often is in the form containing a username/password
# for access the API. E.g. 
#
#     'https://jane.doe:secret@eprint.example.edu'
#
def get_eprint_keys(eprint_url):
    cmd = ['eputil']
    cmd.append('-json')
    cmd.append(eprint_url + '/rest/eprint/')
    try:
        p = run(cmd, capture_output = True)
    except Exception as e:
        sys.stderr.write(f"{e}\n")

    exit_code = p.returncode
    if exit_code != 0:
        print(f"ERROR: {' '.join(cmd)}, exit code {exit_code}")
        return None
    value = p.stdout
    if not isinstance(value, bytes):
        value = value.encode('utf8')
    src = value.decode()
    if type(src) == str:
        if src == "":
            return []
        keys = []
        l = json.loads(src)
        for k in l:
            keys.append(f"{k}")
        return keys
    else:
        print(f"ERROR: wrong type {type(src)} for {src}")
        return None

#
# get_eprint returns a single EPrint element for given EPrint ID.
# via the EPrints rest API indicated in the provided eprint_url. 
#
# The eprint_url often is in the form containing a username/password
# for access the API. E.g. 
#
#     'https://jane.doe:secret@eprint.example.edu'
#
def get_eprint(eprint_url, eprint_id):
    eprint = {}
    cmd = ['eputil']
    cmd.append('-json')
    cmd.append(eprint_url + '/rest/eprint/' + eprint_id + '.xml')
    try:
        p = run(cmd, capture_output = True)
    except Exception as e:
        sys.stderr.write(f"{e}\n")

    exit_code = p.returncode
    if exit_code != 0:
        print(f"ERROR: {' '.join(cmd)}, exit code {exit_code}")
        return None
    value = p.stdout
    if not isinstance(value, bytes):
        value = value.encode('utf8')
    src = value.decode()
    if type(src) == str:
        if src == "":
            return {} 
        obj = json.loads(src)
        if 'eprint' in obj and len(obj['eprint']) > 0:
            return obj['eprint'][0]
        return None
    else:
        print(f"ERROR: wrong type {type(src)} for {src}")
        return None

#
# get_eprints returns an EPrint element in List form
# for given EPrint ID via the EPrints rest API indicated in the 
# provided eprint_url (the outer XML is <eprints>... rather
# than the inner XML of <eprints><eprint>...)
#
# The eprint_url often is in the form containing a username/password
# for access the API. E.g. 
#
#     'https://jane.doe:secret@eprint.example.edu'
#
def get_eprints(eprint_url, eprint_id):
    eprints = []
    eprint = {}
    cmd = ['eputil']
    cmd.append('-json')
    cmd.append(eprint_url + '/rest/eprint/' + eprint_id + '.xml')
    try:
        p = run(cmd, capture_output = True)
    except Exception as e:
        sys.stderr.write(f"{e}\n")
    exit_code = p.returncode
    if exit_code != 0:
        print(f"ERROR: {' '.join(cmd)}, exit code {exit_code}")
        return None
    value = p.stdout
    if not isinstance(value, bytes):
        value = value.encode('utf8')
    src = value.decode()
    if type(src) == str:
        if src == "":
            return []
        obj = json.loads(src)
        if 'eprint' in obj and len(obj['eprint']) > 0:
            return obj
        return None
    else:
        print(f"ERROR: wrong type {type(src)} for {src}")
        return None

