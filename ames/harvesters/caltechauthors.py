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


def get_request_id_title(token, request):
    url = f" https://authors.library.caltech.edu/api/requests/{request}"
    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error getting comments for request {p}")
    response = response.json()
    date = response["updated"].split("T")[0]
    return response["topic"]["record"], response["title"], date


def get_request_comments(token, request):
    url = f" https://authors.library.caltech.edu/api/requests/{request}/timeline"
    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error getting comments for request {p}")
    comments = response.json()["hits"]["hits"]
    cleaned = []
    for c in comments:
        cleaned.append(c["payload"]["content"])
    return cleaned


def get_author_records(token, author_identifier, year=None, test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = f'?q=metadata.creators.person_or_org.identifiers.identifier%3A"{author_identifier}"'

    if year:
        query += (
            f"%20AND%20metadata.publication_date%3A%5B{year}-01-01%20TO%20%2A%20%5D"
        )

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    url = url + query
    response = requests.get(url, headers=headers)
    total = response.json()["hits"]["total"]
    print(total)
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


def get_group_records(group_identifier, test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = f'?q=custom_fields.caltech%5C%3Agroups.id%3D"{group_identifier}"'

    url = url + query
    response = requests.get(url) 
    total = response.json()["hits"]["total"]
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in range(1, pages + 1):
        chunkurl = f"{url}&size=1000&page={c}"
        response = requests.get(chunkurl).json()
        hits += response["hits"]["hits"]

    return hits


def get_restricted_records(token, test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = "?q=access.status:restricted"

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

    return hits


def get_records_from_date(date="2023-08-25", test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = f"?q=created:[{date} TO *]"

    url = url + query
    response = requests.get(url)
    total = response.json()["hits"]["total"]
    print(f"Found {total} Records")
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in range(1, pages + 1):
        chunkurl = f"{url}&size=1000&page={c}"
        response = requests.get(chunkurl).json()
        hits += response["hits"]["hits"]

    return hits
