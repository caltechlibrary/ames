from ames.harvesters import get_cd_github
from ames.matchers import match_codemeta
import os

if os.path.isdir('data') == False:
    os.mkdir('data')
os.chdir('data')

get_cd_github(False)
match_codemeta()

