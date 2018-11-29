import os,json,subprocess
import requests
from clint.textui import progress
from caltechdata_api import decustomize_schema
import dataset

def get_caltechdata(collection):

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
        metadata = decustomize_schema(h['metadata'],True,True)
        metadata['updated'] = h['updated']

        result = dataset.has_key(collection,rid)

        if result == False:
            dataset.create(collection,rid, metadata)
        else:
            #Could check update data, but probably not worth it
            dataset.update(collection,rid, metadata)
        
def get_multiple_links(input_collection,output_collection):
    keys = dataset.keys(input_collection)
    for k in keys:
        record,err = dataset.read(input_collection,k)
        if err != '':
            print(err)
            exit()
        if 'relatedIdentifiers' in record:
            idvs = []
            for idv in record['relatedIdentifiers']:
                idvs.append(idv['relatedIdentifier'])
            for idv in record['relatedIdentifiers']:
                count = idvs.count(idv['relatedIdentifier'])
                if count > 1:
                    print("DUPE")
                    print(k)
                    print(idv['relatedIdentifier'])
