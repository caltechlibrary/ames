import os,json,subprocess,shutil
import requests
from caltechdata_api import decustomize_schema
import dataset
from progressbar import progressbar

def get_caltechdata(collection,production=True,datacite=False):
    '''Harvest all records from CaltechDATA .
    Always creates collection from scratch'''
    
    #Delete existing collection
    if os.path.isdir(collection):
        shutil.rmtree(collection)
    
    ok = dataset.init(collection)
    if ok == False:
        print("Dataset failed to init collection")
        exit()

    if production == True:
        url = 'https://data.caltech.edu/api/records'
    else:
        url = 'https://cd-sandbox.tind.io/api/records'

    response = requests.get(url+'/?size=5000')
    hits = response.json()

    for h in progressbar(hits['hits']['hits']):
        rid = str(h['id'])
        #Get enriched metadata records (including files)
        if datacite == False:
            metadata = decustomize_schema(h['metadata'],True,True)
            metadata['updated'] = h['updated']
        else:
            #Get just DataCite metadata
            metadata = decustomize_schema(h['metadata'])           

        dataset.create(collection,rid, metadata)
        
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
