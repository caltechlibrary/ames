import os,json,subprocess
import requests
from clint.textui import progress
from caltechdata_api import decustomize_schema
import dataset

def get_caltechdata(new=True):

    collection = 'caltechdata.ds'
    if os.path.isdir('data') == False:
        os.mkdir('data')
    os.chdir('data')

    if new==True:
        os.system('rm -rf '+collection)

    if os.path.isdir(collection) == False:
        ok = dataset.init(collection)
        if ok == False:
            print("Dataset failed to init collection")
            exit()

    url = 'https://data.caltech.edu/api/records'

    response = requests.get(url+'/?size=1000')
    hits = response.json()

    print("Saving Records")
    for h in hits['hits']['hits']:
        rid = str(h['id'])
        print(rid)
        metadata = decustomize_schema(h['metadata'])
        metadata['updated'] = h['updated']

        result = dataset.has_key(collection,rid)

        if result == False:
            dataset.create(collection,rid, metadata)
        else:
            #Could check update data, but probably not worth it
            dataset.update(collection,rid, metadata)
        
