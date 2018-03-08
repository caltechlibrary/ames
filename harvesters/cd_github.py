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

    collection = 'github_records'

    if new==True:
        os.system('rm -rf '+collection)
        ok = dataset.init_collection(collection)
        print(ok,"HERE")        
        if ok == False:
            print("Dataset failed to init collection")
            exit()

    url = 'https://data.caltech.edu/api/records'

    response = requests.get(url+'/?size=1000&q=subjects:GitHub')
    hits = response.json()

    os.environ["DATASET"] = collection

    for h in hits['hits']['hits']:
        #print('checking',h)
        rid = str(h['id'])
        record = h['metadata']
    
        result = dataset.has_key(collection,rid)
        print(result)
	#result =\
                #subprocess.check_output(['dataset','haskey',rid],universal_newlines=True).rstrip()

        if result == False:
        
            dataset.create_record(collection,rid, record)

            #Save results in dataset
            #outstr = json.dumps(record)

            #Replace single quotes with complicated escape
            #outstr = outstr.replace("'","'\\''")
            #print("Saving record " + str(rid))

            #os.system("dataset create "+rid+'.json'+" '"+outstr+"'")

            fstring = ''

            print("Downloading files for ",rid)

            files = []

            for erecord in record['electronic_location_and_access']:
                f = download_file(erecord,rid)
                files.append(f)
                if f != None:
                    fstring = fstring + f + ' '

                print("Attaching files")

                if fstring != '':
                    os.system("dataset attach "+str(rid)+" "+fstring)
                    os.system("rm "+fstring)


