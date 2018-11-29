from ames.harvesters import get_cd_github
from ames.matchers import match_codemeta
import os,subprocess,json
import requests

get_cd_github(False)
matches = match_codemeta()

