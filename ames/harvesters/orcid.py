import requests


def get_orcid_works(orcid):
    orcid_link = "https://orcid.org/"
    headers = {"Accept": "application/json"}
    result = requests.get(orcid_link + orcid, headers=headers).json()
    raw_works = result["activities-summary"]["works"]["group"]
    dois = []
    for work in raw_works:
        idvs = work["work-summary"][0]["external-ids"]["external-id"]
        for idv in idvs:
            if idv["external-id-type"] == "doi":
                dois.append(idv["external-id-value"])
    return dois
