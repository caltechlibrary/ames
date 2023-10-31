import os, sys
from ames.harvesters import get_author_records
from ames.matchers import edit_author_identifier

token = os.environ["CTATOK"]

old_identifier = sys.argv[1]
new_identifier = sys.argv[2]

to_update = get_author_records(token, old_identifier)
for record in to_update:
    edit_author_identifier(record, token, old_identifier, new_identifier)
