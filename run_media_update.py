import os
from datetime import date
from py_dataset import dataset
from ames.harvesters import get_caltechdata, get_caltechdata_files
from ames.matchers import update_datacite_media

password = os.environ["DATACITE"]
prefix = "10.14291"
user = "CALTECH.LIBRARY"
token = os.environ["RDMTOK"]

os.chdir("data")

with open("mediaupdate", "r") as infile:
    last_date = infile.readline().strip()

collection = "caltechdata_formedia.ds"
collection_files = "caltechdatafiles.ds"

get_caltechdata(collection, token=token, date=last_date)
get_caltechdata_files(collection_files, token=token, date=last_date)
update_datacite_media(user, password, collection, collection_files, prefix)

password = os.environ["CALTECHDATA_DATACITE"]
prefix = "10.22002"
user = "CALTECH.DATA"

update_datacite_media(user, password, collection, collection_files, prefix)

# Save date in file
today = date.today().isoformat()
with open("mediaupdate", "w") as outfile:
    outfile.write(today)
