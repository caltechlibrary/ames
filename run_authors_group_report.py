import os, sys, csv
from ames.harvesters import get_group_records
from ames.matchers import edit_author_identifier

token = os.environ["CTATOK"]

group_identifier = sys.argv[1]

outfile = open(f"{group_identifier}_report.csv", "w")
writer = csv.writer(outfile)

to_update = get_group_records(token, group_identifier)
for record in to_update:
    if "doi" not in record["pids"]:
        metadata = record["metadata"]
        publisher = ""
        if "publisher" in metadata:
            publisher = metadata["publisher"]
        writer.writerow(
            [
                metadata["title"],
                publisher,
                record["metadata"]["publication_date"],
                record["id"],
            ]
        )
