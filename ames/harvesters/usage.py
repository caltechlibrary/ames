import os,json,csv
import requests
import pandas as pd
from datetime import datetime
from progressbar import progressbar
from py_dataset import dataset

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
        if err != '':
            print(err)
            exit()

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
    
    #Build out dict for record creation
    ids = dataset.keys(caltechdata_collection)
    record_dates = {}
    for k in ids:
        metadata,err = dataset.read(caltechdata_collection,k)
        #When record was submitted to CaltechDATA:
        rdate = None
        for date in metadata['dates']:
            if date['dateType']=='Submitted':
                rdate = date['date']
            if date['dateType']=='Updated':
                if rdate == None:
                    rdate = date['date']
        record_dates[k] = datetime.fromisoformat(rdate)

    #Find time periods
    datev,err = dataset.read(usage_collection,'end-date')
    new_start = datetime.fromisoformat(datev['end-date'])
    #Always start at the beginning of a month
    if new_start.day != 1:
        new_start = str(new_start.year)+'-'+str(new_start.month)+'-01'
    today = datetime.today().date().isoformat()
    start_list = pd.date_range(new_start,today,freq='MS').strftime('%Y-%m-%d').to_list()
    end_list = pd.date_range(new_start,today,freq='M').strftime('%Y-%m-%d').to_list()
    #If today isn't the last day in the month, add end date
    if len(start_list) == len(end_list) + 1:
        end_list.append(today)
    
    view_url_base =\
    'https://stats.tind.io/index.php?module=API&method=Actions.getPageUrl&idSite=1161&period=range&format=JSON'
    dl_url_base =\
    'https://stats.tind.io/?module=API&method=Actions.getDownload&idSite=1161&period=range&format=JSON'

    for i in range(len(start_list)):
        end_date = datetime.fromisoformat(end_list[i])
        print('Collecting usage from ',start_list[i],' to',end_list[i])
        token_s = '&token_auth='+token
        view_url = view_url_base + '&date='+start_list[i]+','+end_list[i]+token_s
        dl_url = dl_url_base + '&date='+start_list[i]+','+end_list[i]+token_s
        #Build report structure
        report = {'report-header': {'report-name':"dataset report",
                'report-id': "DSR",
                "release": "rd1",
                "created-by": "Caltech Library",
                'created': today,
                "reporting-period":{'begin-date':start_list[i],'end-date':end_list[i]}},
                "report-datasets":[]}

        print('Collecting downloads')
        aggr_downloads = {}
        for m in progressbar(mapping):
            record_date = record_dates[mapping[m]]
            #report_data,err = dataset.read(usage_collection,mapping[m])
            #record_date = datetime.fromisoformat(report_data['begin-date'])
            #If the record existed at this date
            if record_date < end_date:
                #Handle old URL-might not be needed depending on mapping
                d_url = m
                if end_date < datetime.fromisoformat('2017-06-01'):
                    d_url = 'https://caltechdata.tind.io'+m.split('data.caltech.edu')[1]
                url = dl_url + '&downloadUrl='+d_url
                response = requests.get(url)
                if response.status_code != 200:
                    print(response.text)
                    print(dl_url)
                r_data = response.json()
                recid = mapping[m]
                if r_data != []:
                    downloads = r_data[0]['nb_visits']
                    if recid in aggr_downloads:
                        aggr_downloads[recid] += downloads
                    else:
                        aggr_downloads[recid] = downloads
                else:
                    if recid not in aggr_downloads:
                        aggr_downloads[recid] = 0
        print('Collecting views')
        for k in progressbar(ids):
            performance ={'period':
                {'begin-date':start_list[i],'end-date':end_list[i]},'instance':[]}
            #report_data,err = dataset.read(usage_collection,k)
            #record_date = datetime.fromisoformat(report_data['begin-date'])
            record_date = record_dates[k]
            metadata,err = dataset.read(caltechdata_collection,k)
            #If the record existed at this date
            if record_date < end_date:
                url = view_url + '&pageUrl=https://data.caltech.edu/records/'+k
                response = requests.get(url)
                r_data = response.json()
                if r_data != []:
                    visits = r_data[0]['nb_visits']
                else:
                    visits = 0
                entry =\
                {'count':visits,'metric-type':'unique-dataset-investigations','access-method':'regular'}
                performance['instance'].append(entry)
                #Also add downloads to structure
                if k in aggr_downloads:
                    entry =\
                    {'count':aggr_downloads[k],'metric-type':'unique-dataset-requests','access-method':'regular'}
                performance['instance'].append(entry)
                #Save to report
                report_data = {'dataset-id':[{'type':'doi',
                'value':metadata['identifier']['identifier']}],
                'uri': 'https://data.caltech.edu/records/'+k,
                'publisher':'CaltechDATA',
                'publisher-id':[{'type':'grid','value':'grid.20861.3d'}],
                'yop':metadata['publicationYear'],
                'data-type':metadata['resourceType']['resourceTypeGeneral'],
                'dataset-dates':[{"type":"pub-date","value":record_date.isoformat()}],
                'dataset-title':metadata['titles'][0]['title'],
                'performance':[performance]}
                report['report-datasets'].append(report_data)
        rname = start_list[i]+'/'+end_list[i]
        if dataset.has_key(usage_collection,rname):
             err = dataset.update(usage_collection,rname,report)
        else:
            err = dataset.create(usage_collection,rname,report)
        if err != '':
            print(err)
            exit()
        dataset.update(usage_collection,'end-date',{'end-date':end_list[i]})


