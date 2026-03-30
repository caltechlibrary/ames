import os, sys
from ames.harvesters import get_author_records
from ames.matchers import add_group

token = os.environ["CTATOK"]

name_file = sys.argv[1]
group_identifier = sys.argv[2]
date = sys.argv[3]

input_file = open(name_file, "r", encoding="utf-8-sig")
names = input_file.read().splitlines()
input_file.close()

#import http.client
#http.client.HTTPConnection.debuglevel = 5

#import logging
#import requests
#from urllib3.util.retry import Retry
#from requests.adapters import HTTPAdapter

# Enable urllib3 debug logging
#logging.basicConfig(level=logging.DEBUG)
#urllib3_logger = logging.getLogger('urllib3')
#urllib3_logger.setLevel(logging.DEBUG)

for name in names:
    print(name)
    to_update = get_author_records(name, token, date)
    for record in to_update:
        add_group(record, token, group_identifier)
