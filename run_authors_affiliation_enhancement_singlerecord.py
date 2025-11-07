import os, sys, argparse, json
from ames.matchers import add_authors_affiliations
from caltechdata_api import get_metadata

token = os.environ["CTATOK"]
dimensions_key = os.environ["DIMKEY"]

parser = argparse.ArgumentParser(
    prog="authors_affitiliation_enhancement_singlerecord",
    description="Adds affiliations from dimensions to single authors record, ignoring any mismatch in author numbers",
)

parser.add_argument(
    "record_identifier", type=str, help="The rdm record identifier to enhance"
)

args = parser.parse_args()
record_identifier = args.record_identifier
record = get_metadata(record_identifier, authors=True)

add_authors_affiliations(record, token, dimensions_key, ignore_mismatch=True)
