from harvesters import get_cd_github
from matchers import match_codemeta
import os,subprocess,json
import requests

get_cd_github(True)
matches = match_codemeta()

