import os,argparse,csv
import dataset
from ames.harvesters import get_caltechfeed

if os.path.isdir('data') == False:
    os.mkdir('data')
os.chdir('data')

parser = argparse.ArgumentParser(description=\
        "Run a report on CODA repositories")
parser.add_argument('report_name', nargs=1, help=\
        'report name (options: doi)')
parser.add_argument('repository', nargs=1, help=\
        'options: thesis, authors')
parser.add_argument('output', nargs=1, help=\
        'output tsv name')
parser.add_argument('-years', nargs=1, help='format: 1939 or 1939-1940')

args = parser.parse_args()

with open('../'+args.output[0],'w') as fout:
    tsvout = csv.writer(fout,delimiter='\t')
    tsvout.writerow(["Eprint ID","DOI","Year","Author ID","Title","Resolver URL"])
    for repo in args.repository:

        collection = get_caltechfeed(repo)

        keys = dataset.keys(collection)
        print("Running report for "+repo)
        for k in keys:
            metadata,err = dataset.read(collection,k)
            if 'date' in metadata:
                year = metadata['date'].split('-')[0]
                keep = False
                if args.years:
                    split = args.years[0].split('-')
                    if len(split)==2:
                        if int(year) >= int(split[0]) and \
                                int(year) <= int(split[1]):
                            keep = True
                    else:
                        if year == split[0]:
                            keep= True
                else:
                    keep = True
                if keep == True:
                    ep = metadata['eprint_id']
                    if 'doi' not in metadata:
                        doi = ''
                    else:
                        doi = metadata['doi']
                    author = metadata['creators']['items'][0]['id']
                    title = metadata['title']
                    url = metadata['official_url']
                    print("Record matched: ",url)
                    tsvout.writerow([ep,doi,year,author,title,url])


