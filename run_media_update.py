import os
from ames.harvesters import get_caltechdata
from ames.matchers import update_datacite_media

password = os.environ['DATACITE']

os.chdir('data')

collection = 'caltechdata.ds'
prefix = '10.14291'

get_caltechdata(collection)
update_datacite_media('CALTECH.LIBRARY',password,collection,prefix)

