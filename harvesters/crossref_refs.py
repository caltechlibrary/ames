import os,shutil,json,subprocess, datetime
import requests
import dataset

def get_crossref_refs(new=True):
    #New=True will download everything from scratch and delete any existing records

    collection = 'crossref_refs.ds'
    if os.path.isdir('data') == False:
        os.mkdir('data')
    os.chdir('data')

    if new==True:
        if os.path.exists(collection)==True:
            shutil.rmtree(collection)

    if os.path.isdir(collection) == False:
        ok = dataset.init(collection)
        if ok == False:
            print("Dataset failed to init collection")
            exit()

    #os.environ['DATASET']=collection
    
    base_url = 'https://api.eventdata.crossref.org/v1/events?mailto=data@caltech.edu&source=crossref'

    cursor = ''
    count = 0
    while cursor != None:
        #collected = subprocess.check_output(["dataset","haskey","captured"],universal_newlines=True)
        collected = dataset.has_key(collection,"captured")
        if collected == True:
            #date = subprocess.check_output(["dataset","read","captured"],universal_newlines=True)
            date = dataset.read(collection,"captured")
            #date = json.loads(date)
            date = date['captured']
            print(date)
            url = base_url + '&from-collected-date=' +date+ '&cursor='+cursor
        else:
            url = base_url + '&cursor='+cursor
        print(url)
        r = requests.get(url)
        records = r.json()
        if records['status'] == 'failed':
            print(records)
            break
        for rec in records['message']['events']:
            #Save results in dataset
            #event = json.dumps(rec)
            print(count,rec['id'])
            count = count + 1 #Just for prettyness
            dataset.create(collection,rec['id'],rec)
            #subprocess.run(['dataset','-i','-','create',\
                    #        str(rec['id'])],input=event,universal_newlines=True)

        if cursor == records['message']['next-cursor']: 
        # Catches bug where we get the same curser back at end of results
            break
        cursor = records['message']['next-cursor']

        #Check Deleted
        #Check Edited

    date = datetime.date.today().isoformat()
    record = {"captured":date}
    if dataset.has_key(collection,"captured"):
        dataset.update(collection,'captured',record)
    else:
        dataset.create(collection,'captured',record)
    #subprocess.run(['dataset','-i','-','update','captured'],input='{"captured":"'+date+'"}',universal_newlines=True)
    #subprocess.run(['rm','-rf',collection+'.bleve'])
    dataset.indexer(collection,collection+'.bleve','../harvesters/crossref_refs.json')
    #subprocess.run(['dataset','indexer','harvesters/crossref_refs.json',collection+'.bleve'])

