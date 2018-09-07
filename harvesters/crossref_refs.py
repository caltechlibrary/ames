import os,shutil,json,subprocess, datetime
import requests
import dataset

def get_crossref_refs(new=True):
    #New=True will download everything from scratch and delete any existing records

    collection = 'crossref_refs.ds'

    if new==True:
        if os.path.exists(collection)==True:
            shutil.rmtree(collection)

    if os.path.isdir(collection) == False:
        ok = dataset.init(collection)
        if ok == False:
            print("Dataset failed to init collection")
            exit()

    base_url = 'https://api.eventdata.crossref.org/v1/events?mailto=data@caltech.edu&source=crossref'

    collected = dataset.has_key(collection,"captured")

    cursor = ''
    count = 0
    while cursor != None:
        if collected == True:
            date = dataset.read(collection,"captured")
            date = date[0]['captured']
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
            print(count,rec['id'])
            count = count + 1 #Just for prettyness
            err = dataset.create(collection,rec['id'],rec)
            if err != '':
                print("Error in saving record: "+err)

        if cursor == records['message']['next-cursor']: 
        # Catches bug where we get the same curser back at end of results
            break
        cursor = records['message']['next-cursor']

    if collected == True:
    
        date = dataset.read(collection,"captured")
        date = date[0]['captured']

        #Check Deleted
        cursor = ''
        while cursor != None:
            del_url = 'https://api.eventdata.crossref.org/v1/events/deleted?mailto=data@caltech.edu&source=crossref'
            full = del_url + '&from-collected-date=' +date+ '&cursor='+cursor
            r = requests.get(full)
            for rec in records['message']['events']:
                #Delete results in dataset
                print("Deleted: ",rec['id'])
                err = dataset.delete(collection,rec['id'],rec)
                if err !="":
                    print(f"Unexpected error on read: {err}")
            cursor = records['message']['next-cursor']

        #Check Edited
        cursor = ''
        while cursor != None:
            del_url = 'https://api.eventdata.crossref.org/v1/events/edited?mailto=data@caltech.edu&source=crossref'
            full = del_url + '&from-collected-date=' +date+ '&cursor='+cursor
            r = requests.get(full)
            for rec in records['message']['events']:
                #Delete results in dataset
                print("Update: ",rec['id'])
                dataset.update(collection,rec['id'],rec)
            cursor = records['message']['next-cursor']

    date = datetime.date.today().isoformat()
    record = {"captured":date}
    if dataset.has_key(collection,"captured"):
        err = dataset.update(collection,'captured',record)
        if err !="":
            print(f"Unexpected error on update: {err}")
    else:
        err = dataset.create(collection,'captured',record)
        if err !="":
            print(f"Unexpected error on create: {err}")
    err = dataset.indexer(collection,collection+'.bleve','../harvesters/crossref_refs.json')
    if err !="":
            print(f"Unexpected error on index: {err}")

