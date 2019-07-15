#
# epfmt is a Python 3.7 wrapper for the functionality of
# the epfmt command line tool which is part of the eprinttools Go
# package
#
# For the Go package see https://github.com/caltechlibrary/eprinttools.
#
import json
import ames
import sys, os, inspect
from subprocess import run


# get path to executible
def get_epfmt_exec():
    platform = sys.platform
    m_path = os.path.dirname(inspect.getfile(ames))
    path = os.path.join(m_path, "exec/Linux/epfmt")
    if platform.startswith("darwin"):
        path = os.path.join(m_path, "exec/MacOS/epfmt")
    elif platform.startswith("win"):
        path = os.path.join(m_path, "exec/Win/epfmt.exe")
    return path


#
# eprint_as_xml takes a Python dict of EPrint content like
# that fetched with eputil returns the object as EPrint XML.
#
def eprint_as_xml(eprint_obj):
    src = json.dumps(eprint_obj)
    # if not isinstance(src, bytes):
    #    src = src.encode('utf-8')
    execp = get_epfmt_exec()
    cmd = [execp, "-xml"]
    try:
        p = run(cmd, input=src.encode("utf-8"), capture_output=True)
    except Exception as e:
        sys.stderr.write(f"{e}\n")
    exit_code = p.returncode
    if exit_code != 0:
        print(f"ERROR: {' '.join(cmd)}, exit code {exit_code}")
        return None
    value = p.stdout
    if not isinstance(value, bytes):
        value = value.encode("utf8")
    return value.decode()


#
# eprint_as_json takes a Python Dict of EPrint content
# like that fetch with eputil returns the object in JSON format.
#
def eprint_as_json(eprint_obj):
    src = json.dumps(eprint_obj)
    if not isinstance(src, bytes):
        src = src.encode("utf-8")
    execp = get_epfmt_exec()
    cmd = [execp, "-json"]
    try:
        p = run(cmd, input=src, capture_output=True)
    except Exception as e:
        sys.stderr.write(f"{e}\n")
    exit_code = p.returncode
    if exit_code != 0:
        print(f"ERROR: {' '.join(cmd)}, exit code {exit_code}")
        return None
    value = p.stdout
    if not isinstance(value, bytes):
        value = value.encode("utf8")
    return value.decode()
