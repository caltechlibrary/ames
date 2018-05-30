import requests
import dataset
import os, csv
from harvesters import get_downloads

#Pull download statistics from pimwik/matomo
get_downloads(True)

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
