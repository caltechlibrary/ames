#!/usr/bin/env python3

#
# run_eprint_report.py provides a small number of common reports.
# reports are generated as CSV files.
#
import os
import sys
import random
from ames.harvesters import get_eprint_keys, get_eprints, get_eprint

batch_size = 100

def usage(msg = "", exit_code = 0):
    app_name = os.path.basename(sys.argv[0])
    print(f'''USAGE: {app_name} REPORT_NAME URL_TO_EPRINTS \\
        OUTPUT_CSV_FILE [SAMPLE_SIZE]

EXAMPLE:

    {app_name} creator \\
        'https://username:secret@eprint.example.edu' \\
        creator_report.csv

    {app_name} doi \\
        'https://username:secret@eprint.example.edu' \\
        doi_report.csv
''')
    if msg != "":
        print("")
        print(msg)
    sys.exit(exit_code)

#
# creator_report crawls the EPrints REST API and accumulates 
# creators, orcids and their eprint article
# numbers. Returns a list in a table format.
#
def creator_report(eprint_url, csv_filename, sample_size = 0):
    print(f"Retrieving keys from {eprint_url}, saving report to {csv_filename}")
    keys = get_eprint_keys(eprint_url)
    if keys == None:
        print(f"ERROR: could not get keys, check URL {eprint_url}")
        sys.exit(1)
    
    if len(keys) == 0:
        print(f"ERROR: no keys returned for {eprint_url}")
        sys.exit(1)
    
    # NOTE: You can debug using a sample_size > 0
    if sample_size > 0:
        keys = random.sample(keys, sample_size)
    keys.sort(key=int, reverse = True)
    
    creators = {}
    creator_ids = []
    i = 0
    j = 0
    print(f"Processing {len(keys)} eprint records for creators")
    for eprint_id in keys:
        obj = get_eprint(eprint_url, eprint_id)
        if obj != None:
            if 'creators' in obj and 'items' in obj['creators']:
                items = obj['creators']['items']
                for item in items:
                    if 'id' in item:
                        creator_id = item['id']
                        orcid = '' 
                        if 'orcid' in item:
                            orcid = item['orcid']
                        if creator_id in creators:
                            creators[creator_id]['eprint_ids'].append(eprint_id)
                            if orcid != '':
                                if not orcid in creators[creator_id]['orcids']:
                                    creators[creator_id]['orcids'].append(orcid)
                        else:
                            j += 1
                            creators[creator_id] = {}
                            if orcid != '':
                                creators[creator_id]['orcids'] = [orcid]
                            else:
                                creators[creator_id]['orcids'] = []
                            creators[creator_id]['eprint_ids'] = [eprint_id]
                            creator_ids.append(creator_id)
        i += 1
        if (i % batch_size) == 0:
            print(f"Processed {i} eprints, found {j} creators, last eprint id processed {eprint_id}")
    
    print(f"Processed {i} eprints, found {j} creators, total")
    
    creator_ids.sort()
    print("")
    print(f"Collected creators from {eprint_url}, saving in {csv_filename}")
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
    with open(csv_filename, 'w', encoding = 'utf-8') as f:
        f.write("Creator ID, ORCID(s), EPrint ID(s)\n")
        for creator_id in creator_ids:
            creator = creators[creator_id]
            orcid = "|".join(creator['orcids'])
            eprint_ids = "|".join(creator['eprint_ids'])
            print(f"Writing: {creator_id},{orcid},{eprint_ids}")
            f.write(f"{creator_id},{orcid},{eprint_ids}\n")
    print("All Done!")
    


#
# doi_report crawls the EPrints REST API and accumulates doi and
# returns a list one per line.
#
def doi_report(eprint_url, csv_filename, sample_size = 0):
    print(f"Retrieving keys from {eprint_url}, saving report to {csv_filename}")
    keys = get_eprint_keys(eprint_url)
    if keys == None:
        print(f"ERROR: could not get keys, check URL {eprint_url}")
        sys.exit(1)
    
    if len(keys) == 0:
        print(f"ERROR: no keys returned for {eprint_url}")
        sys.exit(1)
    
    
    # NOTE: You can debug using a sample_size > 0
    if sample_size > 0:
        keys = random.sample(keys, sample_size)
    keys.sort(key=int, reverse = True)
    
    dois = []
    i = 0
    j = 0
    print(f"Processing {len(keys)} eprint records for doi")
    for eprint_id in keys:
        obj = get_eprint(eprint_url, eprint_id)
        if obj != None:
            doi, itype, description = '', '', ''
            if 'related_url' in obj and 'items' in obj['related_url']:
                items = obj['related_url']['items']
                for item in items:
                    if 'url' in item:
                        doi = item['url'].strip()
                    if 'type' in item:
                        itype = item['type'].strip().lower()
                    if 'description' in item:
                        description = item['description'].strip().lower()
                    if itype == 'doi' and description == 'article':
                        #print(f"{doi}")
                        dois.append(doi)
                        j += 1
                        break
            elif 'doi' in obj:
                doi = obj['doi'].strip()
                dois.append(doi)
                j += 1
        i += 1
        if (i % batch_size) == 0:
            print(f"Processed {i} eprints, {j} doi, last eprint id processed {eprint_id}")
    
    print(f"Processed {i} eprints, found {j} doi, total")
    
    print("")
    print(f"Collected doi from {eprint_url}, saving in {csv_filename}")
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
    with open(csv_filename, 'w', encoding = 'utf-8') as f:
        f.write("doi\n")
        for doi in dois:
            print(f"Writing: {doi}")
            f.write(f"{doi}\n")
    print("All Done!")

#
# Main script setup and processing
#

if len(sys.argv) < 4:
    usage("", 1)
report_name = sys.argv[1]
eprint_url = sys.argv[2]
csv_filename = sys.argv[3]
sample_size = 0
if len(sys.argv) > 4:
    sample_size = int(sys.argv[4])

if report_name == "creator":
    creator_report(eprint_url, csv_filename, sample_size)
elif report_name == "doi":
    doi_report(eprint_url, csv_filename, sample_size)
else:
    usage(f"ERROR: unknown report name, {report_name}", 1)

