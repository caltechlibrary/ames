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

# Iterate over the rows of the Creator Report CSV file
records = {} 
with open(csv_filename) as f:
    table = csv.DictReader(f)
    for row in table:
        if 'orcid' in row:
            if '|' in row['orcid']:
                print(f"WARNING multiple orcids for {row['creator_id']}")
            else:
                print(f"Processing {row['creator_id']} -> {row['orcid']} -> {row['eprint_id']}")


# Find the rows with an orcid
# Find the eprint id numbers
# generate the EPrint XML and save for update via epadmin import tool

# # NOTE: We use get_eprints() because the XML we want should
# # conform to what epadmin will expect for this record.
# # E.g. <eprints><eprint> .... </eprint>...</eprints>
# o = get_eprints(eprint_url, eprint_id)
# if o == None:
#     print(f"Failed to get record for eprint {eprint_id}")
#     sys.exit(1)
# if 'eprint' in o:
#     # NOTE We're working with single records so let's pull out
#     # our eprint element.
#     obj = o['eprint'][0]
#     if 'creators' in obj and 'items' in obj['creators']:
#         items = obj['creators']['items']
#         for item in items:
#             if 'id' in item and item['id'] == creator_id:
#                 item['orcid'] = orcid
#                 break
#         eprint_xml = eputils.eprint_as_xml(o)
#         print(eprint_xml)
