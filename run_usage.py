import requests
from py_dataset import dataset
import os, csv
from ames.harvesters import file_mapping, get_usage
from ames.harvesters import get_caltechdata

if os.path.isdir('data') == False:
    os.mkdir('data')
os.chdir('data')

production = True
collection = 'caltechdata.ds'

#get_caltechdata(collection,production)

mapping_file = 'tindfile_mapping.csv'

mapping = file_mapping(collection,mapping_file)

usage_collection = 'usage.ds'

token = os.environ['MATTOK']

get_usage(collection,usage_collection,mapping,token)

exit()

#Pull download statistics from pimwik/matomo
#get_downloads(True)

url = 'https://data.caltech.edu/api/records'

response = requests.get(url+'/?size=1000&q=subjects:TCCON')
hits = response.json()

collection = 'download_records.ds'
if os.path.isdir(collection) == False:
    os.chdir('data')

results = []
total_sum = 0

for h in hits['hits']['hits']:
    rid = str(h['id'])
    record = h['metadata']

    result = dataset.read(collection,rid)
    result = result[0]

    sumv = 0
    resv = []
    for r in result['downloads']:
        if 'nb_hits' in r:
            resv.append(r['file_name'])
            resv.append(r['nb_hits'])
            sumv = sumv + r['nb_hits']
            total_sum = total_sum + r['nb_hits']
    summary = [sumv,record['doi']]+ resv
    results.append(summary)   

sort_res = sorted(results,key=lambda s: s[0],reverse=True)

csvfile = open('downloads.csv', 'w')
writer = csv.writer(csvfile)

for r in sort_res:
    writer.writerow(r)

print("Total Downloads: ",total_sum)
