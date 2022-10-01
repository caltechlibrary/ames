import os
from ames.harvesters import get_caltechdata
from py_dataset import dataset

if os.path.isdir("data") == False:
    os.mkdir("data")
os.chdir("data")

token = os.environ["TINDTOK"]

production = True
collection = "caltechdata.ds"

get_caltechdata(collection, production)


# If we need to update
# keys = dataset.keys(collection)
# for k in keys:
#    record, err = dataset.read(collection, k)
#    if err != "":
#        print(err)
#        exit()
#    update_citation(record, k, token, production)
