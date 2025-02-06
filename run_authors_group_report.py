import os, sys, csv, json
from ames.harvesters import get_group_records

group_identifier = sys.argv[1]

#outfile = open(f"{group_identifier}_report.csv", "w")
#writer = csv.writer(outfile)

to_update = get_group_records(group_identifier)

outfile = open(f"{group_identifier}_report.json", "w")
outfile.write(json.dumps(to_update, indent=4))

#for record in to_update:
#    if "doi" not in record["pids"]:
#        metadata = record["metadata"]
#        publisher = ""
#        if "publisher" in metadata:
#            publisher = metadata["publisher"]
#        writer.writerow(
#            [
#                metadata["title"],
#                publisher,
#                record["metadata"]["publication_date"],
#                record["id"],
#            ]
#        )
