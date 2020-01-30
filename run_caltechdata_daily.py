import os
from ames.harvesters import get_caltechdata, get_caltechfeed
from ames.matchers import add_thesis_doi

if os.path.isdir("data") == False:
    os.mkdir("data")
os.chdir("data")

token = os.environ["TINDTOK"]

production = True
collection = "caltechdata_forthesis.ds"

get_caltechdata(collection, production)
thesis_collection = get_caltechfeed("thesis", autoupdate=True)
add_thesis_doi(collection, thesis_collection, token, production)
