import requests, math


def get_pending_requests(token, community=None, return_ids=False, test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/requests?q=is_open:true"
    else:
        url = "https://authors.library.caltech.edu/api/requests?q=is_open:true"

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    if community:
        url += "%20AND%20receiver.community:" + community
    response = requests.get(url, headers=headers)
    print(response)
    total = response.json()["hits"]["total"]
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in range(1, pages + 1):
        chunkurl = f"{url}&size=1000&page={c}"
        response = requests.get(chunkurl, headers=headers).json()
        hits += response["hits"]["hits"]

    req = []
    for item in hits:
        if return_ids:
            req.append(item["topic"]["record"])
        else:
            req.append(item["id"])
    return req


def get_author_records(token, author_identifier, test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = f'?q=metadata.creators.person_or_org.identifiers.identifier%3A"{author_identifier}"'

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    url = url + query
    response = requests.get(url, headers=headers)
    total = response.json()["hits"]["total"]
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in range(1, pages + 1):
        chunkurl = f"{url}&size=1000&page={c}"
        response = requests.get(chunkurl, headers=headers).json()
        hits += response["hits"]["hits"]

    req = []
    for item in hits:
        req.append(item["id"])
    return req
