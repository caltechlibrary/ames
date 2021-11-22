import requests


def doi_in_authors(doi):
    base_url = "http://localhost:8484/caltechauthors/doi/"
    results = requests.get(base_url + doi).json()
    print(results)
    if len(results) == 0:
        return False
    else:
        return True
