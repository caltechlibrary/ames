import requests


def get_github_id(repo):
    api_link = "https://api.github.com/repos/"
    idv = requests.get(api_link + repo).json()["id"]
    return idv
