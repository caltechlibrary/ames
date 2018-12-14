import os,argparse,csv
import dataset
from ames.harvesters import get_caltechfeed

def is_in_range(year_arg,year):
    if year_arg != None:
        split = year_arg.split('-')
        if len(split)==2:
            if int(year) >= int(split[0]) and int(year) <= int(split[1]):
                return True
        else:
            if year == split[0]:
                return True
    else:
        return True
    return False

def doi_report(fname,collection,years=None):
    with open(fname,'w') as fout:
        tsvout = csv.writer(fout,delimiter='\t')
        tsvout.writerow(["Eprint ID","DOI","Year","Author ID","Title","Resolver URL"])
        keys = dataset.keys(collection)
        for k in keys:
            metadata,err = dataset.read(collection,k)
            if 'date' in metadata:
                year = metadata['date'].split('-')[0]
                if is_in_range(years,year):
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

if __name__ == '__main__':
    if os.path.isdir('data') == False:
        os.mkdir('data')
    os.chdir('data')

    parser = argparse.ArgumentParser(description=\
        "Run a report on CODA repositories")
    parser.add_argument('report_name', nargs=1, help=\
        'report name (options: doi_report,file_issues)')
    parser.add_argument('repository', nargs=1, help=\
        'options: thesis, authors')
    parser.add_argument('output', nargs=1, help=\
        'output tsv name')
    parser.add_argument('-years', nargs=1, help='format: 1939 or 1939-1940')

    args = parser.parse_args()

    collection = get_caltechfeed(args.repository[0])

    print("Running report for ",args.repository[0])

    if args.report_name[0] == 'doi_report':
        doi_report('../'+args.output[0],collection,args.years[0])
    else:
        print(args.report_name[0],' is not known')

