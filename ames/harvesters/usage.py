import os,json,csv,subprocess
import requests
import pandas as pd
from datetime import datetime
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

#Views and unique views
#https://stats.tind.io/index.php?module=API&method=API.getProcessedReport&idSite=1161&period=day&date=yesterday&apiModule=Actions&apiAction=getPageUrls&showTimer=1&format=JSON&flat=1&token_auth=
#Downloads and unique downloads
#https://stats.tind.io/?module=API&method=Actions.getDownloads&format=json&idSite=1161&period=range&date=2018-05-01,2018-05-31&flat=1&token_auth=
#Visit info
# https://stats.tind.io/index.php?module=API&method=Live.getLastVisitsDetails&idSite=1161&period=day&date=yesterday&format=JSON&token_auth=

#Plan - build structure
#Build mappling of file ID to record

def file_mapping(source_collection,mapping_file):
    '''Return a dictionary that maps /tindfiles/serve urls to records.
    Expects either an existing csv file dictionary or a file name
    to save a new dictionary.''' 
    
    available = os.path.isfile(mapping_file)
    #If we have an existing file
    if available == True:
        mapping = {}
        reader=csv.reader(open(mapping_file))
        for row in reader:
            mapping[row[0]] = row[1]
    else:
        mapping = {}

    keys = dataset.keys(source_collection)
    for k in keys:
        record,err = dataset.read(source_collection,k)

        #Ignore embargoed records
        if 'electronic_location_and_access' in record:
            for filev in record['electronic_location_and_access']:
                url = filev['uniform_resource_identifier']
                name = filev['electronic_name'][0]
                if url not in mapping:
                    mapping[url] = k
    
    with open(mapping_file,'w') as f:
        w = csv.writer(f)
        w.writerows(mapping.items())
    
    return mapping

def get_usage(caltechdata_collection,usage_collection,mapping,token):
    '''Build up a usage object for items in CaltechDATA'''
    
    if not os.path.isdir(usage_collection):
        ok = dataset.init(usage_collection)
        if ok == False:
            print("Dataset failed to init collection")
            exit()
        #Write date to start collecting statistics for new collection
        dataset.create(usage_collection,'end-date',{'end-date':'2017-02-01'})
    
    #Build out structure
    ids = dataset.keys(caltechdata_collection)
    for k in ids:
        #Do we have a usage object?
        if dataset.has_key(usage_collection,k)==False:
            metadata,err = dataset.read(caltechdata_collection,k)
            #When record was submitted to CaltechDATA:
            rdate = None
            for date in metadata['dates']:
                if date['dateType']=='Submitted':
                    rdate = date['date']
                if date['dateType']=='Updated':
                    if rdate == None:
                        rdate = date['date']
            report_data = {'dataset-id':[{'type':'doi',
            'value':metadata['identifier']['identifier']}],
            'uri': 'https://data.caltech.edu/records/'+k,
            'publisher':'CaltechDATA','yop':metadata['publicationYear'],
            'data-type':metadata['resourceType']['resourceTypeGeneral'],
            'begin-date':rdate,'performance':[]}
            err = dataset.create(usage_collection,k,report_data)
            if err != '':
                print("Error on write ",err)
                exit()
        #else:
        #    report_data,err = dataset.read(usage_collection,k)
        #    if err != '':
        #        print("Error on read ",err)
        #        exit()

    #Find time periods
    datev,err = dataset.read(usage_collection,'end-date')
    new_start = datetime.fromisoformat(datev['end-date'])
    #Always start at the beginning of a month
    if new_start.day != 1:
        new_start = new_start.year+'-'+new_start.month+'-01'
    today = datetime.today().date().isoformat()
    start_list = pd.date_range(new_start,today,freq='MS').strftime('%Y-%m-%d').to_list()
    end_list = pd.date_range(new_start,today,freq='M').strftime('%Y-%m-%d').to_list()
    #If today isn't the last day in the month, add end date
    if len(start_list) == len(end_list) + 1:
        end_list.append(today)
    
    view_url_base =\
    'https://stats.tind.io/index.php?module=API&method=Actions.getPageUrl&idSite=1161&period=range&format=JSON'
    dl_url_base =\
    'https://stats.tind.io/?module=API&method=Actions.getDownloads&format=json&idSite=1161&period=range&flat=1'

    for i in range(len(start_list)):
        end_date = datetime.fromisoformat(end_list[i])
        token_s = '&token_auth='+token
        view_url = view_url_base + '&date='+start_list[i]+','+end_list[i]+token_s
        for k in ids:
            report_data,err = dataset.read(usage_collection,k)
            record_date = datetime.fromisoformat(report_data['begin-date'])
            #If the record existed at this date
            if record_date < end_date:
                view_url = view_url + '&pageUrl=https://data.caltech.edu/records/'+k
                response = requests.get(view_url)
                r_data = response.json()
                if r_data != []:
                    visits = r_data[0]['nb_visits']
                else:
                    visits = 0
                print(k,visits)
        exit()

    #dataset.update(usage_collection,'end-date',{'end-date':today})


