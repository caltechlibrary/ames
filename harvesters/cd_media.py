import os,json,subprocess
import requests
from clint.textui import progress
from caltechdata_api import decustomize_schema
import dataset

def get_cd_media(new=True):

    collection = 'media_records.ds'
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

    response = requests.get(url+'/?size=1000&q=subjects:TCCON')
    hits = response.json()

    for h in hits['hits']['hits']:
        rid = str(h['id'])
        record = h['metadata']
    
        result = dataset.has_key(collection,rid)

        if result == False:
        
            dataset.create(collection,rid, record)

