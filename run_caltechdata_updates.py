import os
from harvesters import get_caltechdata
from matchers import fix_multiple_links

collection = 'caltechdata.ds'
if os.path.isdir('data') == False:
    os.mkdir('data')
os.chdir('data')

token = os.environ['TINDTOK']

get_caltechdata(collection)
fix_multiple_links(collection,token)
