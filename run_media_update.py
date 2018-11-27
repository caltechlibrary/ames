import os
from harvesters import get_caltechdata
from matchers import update_datacite_media

password = os.environ['DATACITE']

os.chdir('data')

collection = 'caltechdata.ds'

get_caltechdata(collection)
update_datacite_media('CALTECH.LIBRARY',password,collection)

