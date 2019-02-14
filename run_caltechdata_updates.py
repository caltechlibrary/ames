import os
from ames.harvesters import get_caltechdata
from ames.matchers import add_citation

if os.path.isdir('data') == False:
    os.mkdir('data')
os.chdir('data')

token = os.environ['TINDTOK']

production = False
collection = 'caltechdata-test.ds'

get_caltechdata(collection,production)
add_citation(collection,token,production)
