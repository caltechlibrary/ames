import requests

base_url = "http://localhost:8484/"


def doi_in_authors(doi):
    results = []
    results += get_extended("caltechauthors", "doi", doi)
    if len(results) == 0:
        results += get_extended("caltechauthors", "doi", doi.lower())
    if len(results) == 0:
        results += get_extended("caltechauthors", "doi", doi.upper())
    if len(results) == 0:
        return False
    else:
        return True


def get_extended(repository, typev, identifier):
    result = requests.get(base_url + f"{repository}/{typev}/{identifier}").json()
    keys = []
    for key in result:
        keys.append(str(key))
    return keys
