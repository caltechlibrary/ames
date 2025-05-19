import os, sys, argparse
from ames.harvesters import get_author_records
from ames.matchers import edit_author_identifier

token = os.environ["CTATOK"]

parser = argparse.ArgumentParser(
    prog="authors_name_update",
    description="Updates a name identifier or adds a new one",
)

parser.add_argument(
    "old_identifier", type=str, help="The old identifier to be replaced"
)
parser.add_argument("new_identifier", type=str, help="The new identifier to be added")
parser.add_argument("-new-scheme", type=str, help="The new scheme to be added")
parser.add_argument("-add", action="store_true")

args = parser.parse_args()
old_identifier = args.old_identifier
new_identifier = args.new_identifier

to_update = get_author_records(old_identifier, token)
for record in to_update:
    if args.add:
        edit_author_identifier(
            record,
            token,
            old_identifier,
            new_identifier,
            add=args.add,
            new_scheme=args.new_scheme,
        )
    else:
        edit_author_identifier(record, token, old_identifier, new_identifier)
