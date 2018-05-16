import os,subprocess,json,re
import dataset
import requests

def update_datacite_media(username,password):
    collection = 'media_records.ds'
    keys = dataset.keys(collection)
    for k in keys:
        print(k)
        existing,err = dataset.read(collection,k)
        if err !="":
            print(f"Unexpected error on read: {err}")
        
        #Should have some sensible update check
        if 'electronic_location_and_access' in existing:
            for file_met in existing['electronic_location_and_access']:
                if file_met['electronic_name'][0].split('.')[-1] == 'nc':
                    url = 'https://mds.datacite.org/media/'+existing['doi'] 
                    data =\
                    'application/x-netcdf='+file_met['uniform_resource_identifier']
                    headers = {'Content-Type':'application/txt;charset=UTF-8'}
                    r = requests.post(url, data = data.encode('utf-8'),\
                            auth=(username,password),headers=headers)  
                    print(r)

