import os, sys, argparse, json
from ames.harvesters import get_author_records
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

# Read in supported identitifiers - this will go away once we upgrade
# authors
with open("ror.txt") as infile:
    lines = infile.readlines()
    ror = [e.strip() for e in lines]

args = parser.parse_args()
author_identifier = args.author_identifier
#to_update = [get_metadata('6dmax-vx632',authors=True)]
to_update = get_author_records(token, author_identifier, all_metadata=True)

for record in to_update:
    add_authors_affiliations(
            record,
            token,
            dimensions_key,
            allowed_identifiers=ror,
        )
