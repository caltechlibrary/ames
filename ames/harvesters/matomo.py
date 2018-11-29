import os,json,subprocess
import requests
from clint.textui import progress
from caltechdata_api import decustomize_schema
import dataset

def get_downloads(new=True):

    token = os.environ['MATTOK']

    collection = 'download_records.ds'
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

    matomo =\
    'https://piwik.tind.io/?module=API&method=Actions.getDownload&format=json&idSite=1161&period=range&date=2018-05-01,2018-05-30&&period=range'
    matomo = matomo + '&token_auth='+token


    response = requests.get(url+'/?size=5000')
    hits = response.json()

    for h in hits['hits']['hits']:
        rid = str(h['id'])
        print(rid)
        record = h['metadata']
        downloads = []

        #Ignore embargoed records
        if 'electronic_location_and_access' in record:
            for filev in record['electronic_location_and_access']:
                data = requests.get(matomo +\
                    '&downloadUrl='+filev['uniform_resource_identifier'])
                data = data.json()
                if data == []:
                    data = {'file_name':filev['electronic_name'][0]}
                else:
                    data = data[0]
                    data['file_name']=filev['electronic_name'][0]
                downloads.append(data)

            result = dataset.has_key(collection,rid)
            if result == False:
                err = dataset.create(collection,rid,{'downloads':downloads})
                if err !="":
                    print(f"Unexpected error on create: {err}")
            else:
                err = dataset.update(collection,rid,{'downloads':downloads})
                if err !="":
                    print(f"Unexpected error on create: {err}")

if __name__ == "__main__":
    get_downloads(new=False)

