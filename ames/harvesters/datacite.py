import requests


def get_datacite_codemeta(doi):
    # Removing normalization until idutils (isbn) depdencies get fixed
    # doi = idutils.normalize_doi(doi)
    citation_link = "https://data.datacite.org/application/vnd.codemeta.ld+json/"
    codemeta = requests.get(citation_link + doi).json()
    return codemeta


def get_datacite_dois(prefix):
    api_link = "https://api.datacite.org/dois?query=prefix:"
    dois = requests.get(api_link + prefix).json()
    return dois
