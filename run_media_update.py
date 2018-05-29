from harvesters import get_cd_media
from matchers import update_datacite_media

token = os.environ['DATACITE']

get_cd_media(False)
update_datacite_media('CALTECH.LIBRARY',token)

