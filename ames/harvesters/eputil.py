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

# get path to executible
def get_eputil_exec():
    platform = sys.platform
    m_path = os.path.dirname(inspect.getfile(ames))
    path = os.path.join(m_path, "exec/Linux/eputil")
    if platform.startswith("darwin"):
        path = os.path.join(m_path, "exec/MacOS/eputil")
    elif platform.startswith("win"):
        path = os.path.join(m_path, "exec/Win/eputil.exe")
    return path


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
    execp = get_eputil_exec()
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
# get_eprint returns a single EPrint element for given EPrint ID.
# via the EPrints rest API indicated in the provided eprint_url.
#
# The eprint_url often is in the form containing a username/password
# for access the API. E.g.
#
#     'https://jane.doe:secret@eprint.example.edu'
#
def get_eprint(eprint_url, eprint_id):
    execp = get_eputil_exec()
    cmd = [execp]
    cmd.append("-json")
    cmd.append(eprint_url + "/rest/eprint/" + eprint_id + ".xml")
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
        if "eprint" in obj and len(obj["eprint"]) > 0:
            return obj["eprint"][0]
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
    execp = get_eputil_exec()
    cmd = [execp]
    cmd.append("-json")
    cmd.append(eprint_url + "/rest/eprint/" + eprint_id + ".xml")
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
        obj = json.loads(src)
        if "eprint" in obj and len(obj["eprint"]) > 0:
            return obj
        return None
    else:
        print(f"ERROR: wrong type {type(src)} for {src}")
        return None
