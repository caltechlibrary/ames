from ames.harvesters import get_github_id
import argparse

parser = argparse.ArgumentParser(description=\
        "Get Markdown for a doi badge from CaltechDATA")
parser.add_argument('repo', help=\
        'Full GitHub repo name (e.g. caltechlibrary/ames)')

args = parser.parse_args()

repo = args.repo
gid = get_github_id(repo)
print(f'[![DOI](https://data.caltech.edu/badge/{gid}.svg)](https://data.caltech.edu/badge/latestdoi/{gid})')
