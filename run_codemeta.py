from ames.harvesters import get_cd_github
from ames.matchers import match_codemeta
import os,subprocess,json
import requests

if os.path.isdir('data') == False:
    os.mkdir('data')
os.chdir('data')

get_cd_github(False)
matches = match_codemeta()

