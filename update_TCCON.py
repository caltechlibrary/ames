import os, requests
from caltechdata_api import decustomize_schema
from ames.matchers import update_citation

# Get access token from TIND sed as environment variable with source token.bash
token = os.environ["TINDTOK"]

production = True

if production == True:
    url = "https://data.caltech.edu/api/records"
else:
    url = "https://cd-sandbox.tind.io/api/records"

response = requests.get(url + "/?size=1000&q=subjects:TCCON")
hits = response.json()

for h in hits["hits"]["hits"]:
    rid = h["id"]
    print(rid)
    record = decustomize_schema(h["metadata"], True)
    update_citation(record, rid, token)
