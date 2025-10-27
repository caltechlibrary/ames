import os, sys, argparse
from ames.harvesters import get_author_records
from ames.matchers import delete_author_identifier

token = os.environ["CTATOK"]

parser = argparse.ArgumentParser(
    prog="authors_name_update",
    description="Updates a name identifier or adds a new one",
)

parser.add_argument(
    "search_identifier", type=str, help="The identifier to search by"
)
parser.add_argument("identifier_to_delete", type=str, help="The identifier to delete")

args = parser.parse_args()
search_identifier = args.search_identifier
identifier_to_delete = args.identifier_to_delete

to_update = get_author_records(search_identifier, token)
for record in to_update:
    print(
        f"Deleting identifier {identifier_to_delete} from {record}"
    )
    delete_author_identifier(
            record,
            token,
            identifier_to_delete,
        )
