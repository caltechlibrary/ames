from harvesters import get_cd_github
from matchers import match_codemeta
import os,subprocess,json
import requests

get_cd_github(False)
matches = match_codemeta()

