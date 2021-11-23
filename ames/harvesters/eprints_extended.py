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
    return requests.get(base_url + f"{repository}/{typev}/{identifier}").json()
