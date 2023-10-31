import os, csv
import requests
from ames.harvesters import get_pending_requests
from ames.matchers import add_journal_metadata

token = os.environ["CTATOK"]

community = "aedd135f-227e-4fdf-9476-5b3fd011bac6"

pending = get_pending_requests(token, community)
for p in pending:
    url = f" https://authors.library.caltech.edu/api/requests/{p}/timeline"
    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error getting comments for request {p}")
    comments = response.json()["hits"]["hits"]
    for c in comments:
        c_value = c["payload"]["content"]
        if "rdmutil" in c_value:
            print(p)
            url = (
                f"https://authors.library.caltech.edu/api/requests/{p}/actions/decline"
            )
            response = requests.post(url, headers=headers)
            print(response)
