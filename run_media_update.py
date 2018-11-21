import os
from matchers import update_datacite_media

password = os.environ['DATACITE']

os.chdir('data')

update_datacite_media('CALTECH.LIBRARY',password)

