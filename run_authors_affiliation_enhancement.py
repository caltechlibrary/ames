import os, sys, argparse, json, csv
from ames.harvesters import get_author_records, get_records_pub_date
from ames.matchers import add_authors_affiliations
from caltechdata_api import get_metadata

token = os.environ["CTATOK"]
dimensions_key = os.environ["DIMKEY"]

parser = argparse.ArgumentParser(
    prog="authors_affitiliation_enhancement",
    description="Adds affiliations from dimensions to author records",
)

parser.add_argument(
    "author_identifier", type=str, help="The author identifier of records to enhance"
)

completed = []

infile = "completed_records.csv"
if os.path.exists(infile):
    with open(infile, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            completed.append(row[0].strip())
completed_writer = csv.writer(open(infile, "a"))

args = parser.parse_args()
author_identifier = args.author_identifier
# to_update = [get_metadata('6dmax-vx632',authors=True)]
to_update = get_author_records(author_identifier, token, all_metadata=True)
# to_update = get_records_pub_date(start_date='2022-01-01',end_date='2022-12-31')

for record in to_update:
    rdm_id = record["id"]
    if rdm_id not in completed:
        add_authors_affiliations(
            record,
            token,
            dimensions_key,
        )
        completed_writer.writerow([rdm_id])
