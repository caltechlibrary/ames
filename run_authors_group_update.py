import os, sys
from ames.harvesters import get_author_records
from ames.matchers import add_group

token = os.environ["CTATOK"]

name_file = sys.argv[1]
group_identifier = sys.argv[2]
year = sys.argv[3]

input_file = open(name_file, "r", encoding="utf-8-sig")
names = input_file.read().splitlines()
input_file.close()

for name in names:
    print(name)
    to_update = get_author_records(name, token, year)
    for record in to_update:
        add_group(record, token, group_identifier)
