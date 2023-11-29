import os, sys
import requests
from ames.harvesters import get_pending_requests, get_records_from_date
from ames.matchers import check_doi


def is_dupe(data, margin):
    pids = False
    idvn = False
    eprints = False
    if "pids" in data:
        if "doi" in data["pids"]:
            doi = data["pids"]["doi"]["identifier"]
            if check_doi(doi) > margin:
                print(doi, "DUPE", data["id"])
            pids = True
    if "identifiers" in data["metadata"]:
        identifiers = data["metadata"]["identifiers"]
        for idv in identifiers:
            scheme = idv["scheme"]
            if scheme == "doi":
                doi = idv["identifier"]
                if check_doi(doi) > margin:
                    print(doi, "DUPE", data["id"])
                idvn = True
            if scheme == "eprintid":
                eprints = True

    if pids == False and idvn == False and eprints == False:
        print(f"missing DOI for {data['id']}")


token = os.environ["CTATOK"]

community = "aedd135f-227e-4fdf-9476-5b3fd011bac6"

pending = get_pending_requests(token, community, return_ids=True)

base = "https://authors.library.caltech.edu"
url = base + "/api/records/"

headers = {
    "Authorization": "Bearer %s" % token,
    "Content-type": "application/json",
}


for record in pending:
    record_url = url + record + "/draft"
    response = requests.get(record_url, headers=headers)
    if response.status_code != 200:
        print(f"record {record} not found")
    data = response.json()

    is_dupe(data, 0)

records = get_records_from_date()
for rec in records:
    is_dupe(rec, 1)
