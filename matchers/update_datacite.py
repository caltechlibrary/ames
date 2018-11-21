import os,subprocess,json
import dataset
import requests
from datetime import date, datetime

def update_datacite_media(username,password):
    collection = 'caltechdata.ds'
    keys = dataset.keys(collection)
    result = dataset.has_key(collection,'mediaupdate')
    if result == True:
        update,err = dataset.read(collection,'mediaupdate')
        update = date.fromisoformat(update)
    else:
        #Arbitrary old date - everythign will be updated
        update = date(2011,1,1)
    for k in keys:
        print(k)
        existing,err = dataset.read(collection,k)
        if err !="":
            print(f"Unexpected error on read: {err}")
        print(existing['updated'])
        record_update = datetime.fromisoformat(existing['updated']).date()
        if record_update > update:
            print("UPDATE")
        #Should have some sensible update check
        if 'electronic_location_and_access' in existing:
            print("YES")
            exit()
            for file_met in existing['electronic_location_and_access']:
                if file_met['electronic_name'][0].split('.')[-1] == 'nc':
                    url = 'https://mds.datacite.org/media/'+existing['doi'] 
                    data =\
                    'application/x-netcdf='+file_met['uniform_resource_identifier']
                    headers = {'Content-Type':'application/txt;charset=UTF-8'}
                    print(data)
                    r = requests.post(url, data = data.encode('utf-8'),\
                            auth=(username,password),headers=headers)  
                    print(r)

