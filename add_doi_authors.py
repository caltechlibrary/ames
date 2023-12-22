import os, sys, csv
import requests
from ames.matchers import add_doi

token = os.environ["CTATOK"]

record_file = sys.argv[1]

with open(record_file, "r") as f:
    reader = csv.DictReader(f)
    for record in reader:
        if record["Publisher"] == "California Institute of Technology":
            add_doi(record["Record ID"], token)
