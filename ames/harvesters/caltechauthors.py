import requests


def get_pending_requests(token, community=None):
    url = "https://authors.caltechlibrary.dev/api/requests"

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    if community:
        url += "?receiver.community=" + community
    r = requests.get(url, headers=headers)
    data = r.json()
    req = []
    for item in data["hits"]["hits"]:
        if item["is_open"] == True:
            req.append(item["id"])
    return req
