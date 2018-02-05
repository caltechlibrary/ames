import os,shutil,json,subprocess, datetime
import requests

def get_crossref_refs(new=True):
    #New=True will download everything from scratch and delete any existing records

    collection = 'crossref_refs'

    if new==True:
        if os.path.exists(collection)==True:
            shutil.rmtree(collection)
        os.system("dataset init "+collection)
        
    os.environ['DATASET']=collection
    
    base_url = 'https://query.eventdata.crossref.org/events?rows=100&filter=source:crossref'

    cursor = ''
    count = 0
    while cursor != None:
        collected = subprocess.check_output(["dataset","haskey","captured"],universal_newlines=True)
        if collected == 'true\n':
            date = subprocess.check_output(["dataset","read","captured"],universal_newlines=True)
            #strip newline
            date = date[:-1]
            url = base_url + ',from-collected-date:' +date+ '&cursor='+cursor
        else:
            url = base_url + '&cursor='+cursor
        r = requests.get(url)
        records = r.json()
        if records['status'] == 'failed':
            print(records)
            break
        for rec in records['message']['events']:
            #Save results in dataset
            if rec['message_action'] != 'create':
                print("Deleted record",rec['id'])
                subprocess.run(['dataset','delete',rec['id']])
            else:
                event = json.dumps(rec)

                print(count,rec['id'])
                count = count + 1 #Just for prettyness
                subprocess.run(['dataset','-i','-','create',\
                    str(rec['id'])],input=event,universal_newlines=True)
        cursor = records['message']['next-cursor']

    date = datetime.date.today().isoformat()
    subprocess.run(['dataset','-i','-','create','captured'],input=date,universal_newlines=True)

    subprocess.run(['dsindexer','-update','harvesters/crossref_refs.json',collection+'.bleve'])

