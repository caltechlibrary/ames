import os
from harvesters import get_cd_media
from matchers import update_datacite_media

password = os.environ['DATACITE']

get_cd_media(False)
update_datacite_media('CALTECH.LIBRARY',password)

