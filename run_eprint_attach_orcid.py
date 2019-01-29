#!/usr/bin/env python3

#
# Attach an orcid to a creator given an REST URL API, eprint id
# number, the creator id and orcid. Output a an update EPrintXML
# suitable for importing with epadmin
#
import os
import sys
import csv
from ames.harvesters import get_eprint_keys, get_eprints, get_eprint
from ames.converters import eprint_as_xml, eprint_as_json


def usage(msg = "", exit_code = 0):
    app_name = os.path.basename(sys.argv[0])
    print(f'''USAGE: 
    
    {app_name} URL_TO_EPRINTS \\
        CREATOR_CSV_FILE CREATOR_ID [EXPORT_DIRECTORY]

This script reads the CREATOR_ID from CREATOR_CSV_FILE and
retrieves the ORCID and EPrint IDs to update.

EXPORT_DIRECTORY if provided will hold the eprint XML generated
for import via epadmin. If not provided it deposits the eprint
XML in the current directory in the form of EPRINT_ID.xml where
EPRINT_ID is the numeric eprint id number.

EXAMPLE:

After running run_eprint_report creator ... use the CSV
rows to update a specific creator id of JONES-J. The exported
eprint XML will be placed inthe updates directory.

    {app_name} 'https://username:secret@eprint.example.edu' \\
            creator_report.csv JONES-J \\
            updates

''')
    if msg != "":
        print("")
        print(msg)
    sys.exit(exit_code)

if len(sys.argv) < 3:
    usage("Expected URL to EPrints, CSV Creator report filename", 1)

eprint_url, csv_filename, export_folder = sys.argv[1], sys.argv[2], sys.argv[3], '.'

if len(sys.argv) == 4:
    export_folder = sys.argv[3]

#FIXME: Need to generate find all the authors with ORCID in
# given eprint records so that we can do one update and fix that
# record.

# Iterate over the rows of the Creator Report CSV file
records = {} 
with open(csv_filename) as f:
    table = csv.DictReader(f)
    for row in table:
        if 'orcid' in row:
            if '|' in row['orcid']:
                print(f"WARNING multiple orcids for {row['creator_id']}")
            else:
                print(f"Saving {row['eprint_id']} -> {row['creator_id']} -> {row['orcid']}")
                eprint_id = row['eprint_id']
                orcid = row['orcid']
                creator_id = row['creator_id']
                if not eprint_id in records:
                    records[eprint_id] = {}
                records[eprint_id][creator_id] = orcid


# For each record find the eprint record, update the creators with orcids
for record in records:
    # Fetch EPrint object
    # For each creator id in record append in EPrint object
    # Generate the EPrint XML and save for update via epadmin import tool
