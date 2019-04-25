import requests,idutils

def get_datacite_codemeta(doi):
    doi = idutils.normalize_doi(doi)
    citation_link ='https://data.datacite.org/application/vnd.codemeta.ld+json/'
    codemeta = requests.get(citation_link+doi).json()
    return codemeta
