import os,json,subprocess
import requests
from clint.textui import progress
from caltechdata_api import decustomize_schema
import dataset

def download_file(erecord,rid):
    r = requests.get(erecord["uniform_resource_identifier"],stream=True)
    fname = erecord['electronic_name'][0]
    if r.status_code == 403:
        print("It looks like this file is embargoed.  We can't access until after the embargo is lifted")
    else:
        with open(fname, 'wb') as f:
            total_length = int(r.headers.get('content-length'))
            for chunk in \
progress.bar(r.iter_content(chunk_size=1024),expected_size=(total_length/1024) + 1):
                if chunk:
                    f.write(chunk)
                    #f.flush()
        return fname

def get_cd_github(new=True):

    collection = 'github_records.ds'
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

    response = requests.get(url+'/?size=1000&q=subjects:GitHub')
    hits = response.json()

    for h in hits['hits']['hits']:
        rid = str(h['id'])
        record = h['metadata']
    
        result = dataset.has_key(collection,rid)

        if result == False:
        
            dataset.create(collection,rid, record)

            print("Downloading files for ",rid)

            codemeta = False

            for erecord in record['electronic_location_and_access']:
                f = download_file(erecord,rid)

                # We're just looking for the zip file
                if f.split('.')[-1] == 'zip':
                    zip_files =\
                subprocess.check_output(['unzip','-l',f.rstrip()],universal_newlines=True).splitlines()
                    i = 4 #Ignore header
                    line = zip_files[i]
                    while line[0] != '-':
                        split = line.split('/')
                        fname = split[-1]
                        if fname == 'codemeta.json':
                            path = ''
                            sp = line.split('   ')[-1]
                            os.system('unzip -j '+f.rstrip()+' '+sp+' -d .')
                            codemeta = True
                        i = i+1
                        line = zip_files[i]
                        #Does not sensibly handle repos with multiple codemeta
                        #files

                #Trash downloaded files - extracted codemeta.json not impacted
                print("Trash "+f)
                os.system('rm '+f)

            if codemeta == True:
                print(collection,rid)
                response = dataset.attach(collection,rid,['codemeta.json'])
                print("Attachment ",response)
                os.system('rm codemeta.json')
                print("Trash codemeta.json")

