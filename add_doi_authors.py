import os, sys
import requests
from ames.matchers import add_doi

token = os.environ["CTATOK"]

record = sys.argv[1]

add_doi(record, token)
