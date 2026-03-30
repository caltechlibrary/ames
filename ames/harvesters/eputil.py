#
# eputil.py is a Python 3.7 wrapper for the Go eprinttools
# eputil command line program.
#
# For Go package see https://github.com/caltechlibrary/eprinttools.
#
import json
import sys, os, inspect
import ames
from subprocess import run


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
    execp = "eputil"
    cmd = [execp]
    cmd.append("-json")
    cmd.append(eprint_url + "/rest/eprint/")
    try:
        p = run(cmd, capture_output=True)
    except Exception as e:
        sys.stderr.write(f"{e}\n")

    exit_code = p.returncode
    if exit_code != 0:
        print(f"ERROR: {' '.join(cmd)}, exit code {exit_code}")
        return None
    value = p.stdout
    if not isinstance(value, bytes):
        value = value.encode("utf8")
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
# get_eprint returns a RDM-flavored jsom version of the Eprint record
#
# It requires the following environemnt varoables to be set outside of the
# application
#
# EPRINT_USER="__USERNAME_GOES_HERE__"
# EPRINT_PASSWORD="__PASSWORD_GOES_HERE__"
# EPRINT_HOST="eprints.example.edu"
#
def get_eprint(eprint_url, eprint_id):
    execp = "eprint2rdm"
    cmd = [execp]
    cmd.append(eprint_url)
    cmd.append(eprint_id)
    try:
        p = run(cmd, capture_output=True)
    except Exception as e:
        sys.stderr.write(f"{e}\n")

    exit_code = p.returncode
    if exit_code != 0:
        print(f"ERROR: {' '.join(cmd)}, exit code {exit_code}")
        return None
    value = p.stdout
    if not isinstance(value, bytes):
        value = value.encode("utf8")
    src = value.decode()
    if type(src) == str:
        if src == "":
            return {}
        obj = json.loads(src)
        return obj
    else:
        print(f"ERROR: wrong type {type(src)} for {src}")
        return None
