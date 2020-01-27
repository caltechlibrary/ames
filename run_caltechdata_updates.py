import os
from ames.harvesters import get_caltechdata
from ames.matchers import add_citation
from ames.matchers import update_citation

if os.path.isdir("data") == False:
    os.mkdir("data")
os.chdir("data")

token = os.environ["TINDTOK"]

production = True
collection = "caltechdata.ds"

get_caltechdata(collection, production)
update_citation(collection, token, production)
