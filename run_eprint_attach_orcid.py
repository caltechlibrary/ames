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
        CREATOR_CSV_FILE [EXPORT_DIRECTORY]

This script reads the CREATOR_ID from CREATOR_CSV_FILE and
retrieves the ORCID and EPrint IDs to update.

EXPORT_DIRECTORY if will hold the eprint XML generated
for import via the formal EPrints epadmin tool. The name
is in the form of EXPORT_DIRECTORY/EPRINT_ID.xml where 
EPRINT_ID is the numeric eprint id number. If the 
EXPORT_DIRECTORY is not provided it will put the XML files
in the current directory.

EXAMPLE:

After running run_eprint_report creator ... use the CSV
rows to update a specific creator id of JONES-J. The exported
eprint XML will be placed inthe updates directory.

    {app_name} 'https://username:secret@eprint.example.edu' \\
            creator_report.csv updates

''')
    if msg != "":
        print("")
        print(msg)
    sys.exit(exit_code)

if len(sys.argv) < 3:
    usage("Expected URL to EPrints, CSV Creator report filename", 1)

eprint_url, csv_filename = sys.argv[1], sys.argv[2]

export_folder = '.'
if len(sys.argv) == 4:
    export_folder = sys.argv[3]

#FIXME: Need to generate find all the authors with ORCID in
# given eprint records so that we can do one update and fix that
# record.

# Iterate over the rows of the Creator Report CSV file
print(f"Processing {csv_filename}")
records = {} 
with open(csv_filename) as f:
    table = csv.DictReader(f)
    for row in table:
        creator_id = row['creator_id']
        update_ids = []
        if '|' in row['update_ids']:
                    update_ids = row['update_ids'].split('|')
        elif row['update_ids'] != '':
                    update_ids.append(row['update_ids'])
        if 'orcid' in row and len(update_ids) > 0:
            if '|' in row['orcid']:
                print(f"WARNING skipping, multiple orcids for {creator_id} {row['orcid']}")
            elif len(update_ids) > 0 :
                orcid = row['orcid']
                update_ids = []
                if '|' in row['update_ids']:
                    update_ids = row['update_ids'].split('|')
                elif row['update_ids'] != '':
                    update_ids.append(row['update_ids'])
                orcid = row['orcid']
                creator_id = row['creator_id']
                print(f"Saving {row['creator_id']}, {row['orcid']} for eprints {update_ids}")
                for eprint_id in update_ids:
                    if not eprint_id in records:
                        records[eprint_id] = {}
                    records[eprint_id][creator_id] = orcid


print(f"Generating EPrints XML")
# For each record find the eprint record, update the creators with orcids
for eprint_id in records:
    # Fetch EPrint object
    o = get_eprints(eprint_url, eprint_id)

    # NOTE We're working with single records so let's pull out
    # our eprint element.
    if 'eprint' in o:
        obj = o['eprint'][0]
        if 'creators' in obj and 'items' in obj['creators']:
            items = obj['creators']['items']
            # For each creator w/orcid in record append in EPrint object
            for creator_id in records[eprint_id]:
                for item in items:
                    if 'id' in item and item['id'] == creator_id:
                        # Attach the ORCID
                        item['orcid'] = records[eprint_id][creator_id]
                        break
            # Generate the EPrint XML for update via epadmin import tool
            eprint_xml = eprint_as_xml(o)
            f_name = os.path.join(export_folder, f"{eprint_id}.xml")
            with open(f_name, "w") as f:
                print(f"Writing {f_name}")
                f.write(eprint_xml)

