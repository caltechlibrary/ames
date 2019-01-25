import os,argparse,csv
import dataset
from ames.harvesters import get_caltechfeed

def is_in_range(year_arg,year):
    #Is a given year in the range of a year argument YEAR-YEAR or YEAR?
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
                    if 'id' in metadata['creators']['items'][0]:
                        author = metadata['creators']['items'][0]['id']
                    else:
                        author = ''
                        print("Record is missing author identifier")
                    title = metadata['title']
                    url = metadata['official_url']
                    print("Record matched: ",url)
                    tsvout.writerow([ep,doi,year,author,title,url])

def file_report(fname,collection,years=None):
    with open(fname,'w') as fout:
        tsvout = csv.writer(fout,delimiter='\t')
        tsvout.writerow(["Eprint ID","Problem","Impacted Files","Resolver URL"])
        keys = dataset.keys(collection)
        for k in keys:
            metadata,err = dataset.read(collection,k)
            if 'date' in metadata:
                year = metadata['date'].split('-')[0]
                if is_in_range(years,year):
                    if 'documents' in metadata:
                        for d in metadata['documents']:
                            if 'files' in d:
                                for f in d['files']:
                                    filename = f['filename']
                                    extension = filename.split('.')[-1]
                                    if extension == 'html':
                                        ep = metadata['eprint_id']
                                        url = metadata['official_url']
                                        print("HTML: ",url)
                                        tsvout.writerow([ep,'HTML File',filename,url])
                                    if extension == 'htm':
                                        ep = metadata['eprint_id']
                                        url = metadata['official_url']
                                        print("HTM: ",url)
                                        tsvout.writerow([ep,'HTML File',filename,url])
                                    if len(filename) > 200:
                                        ep = metadata['eprint_id']
                                        url = metadata['official_url']
                                        print("Length: ",url)
                                        tsvout.writerow([ep,'File Name Length',filename,url])

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

    if args.years != None:
        years = args.years[0]
    else:
        years = None

    if args.report_name[0] == 'doi_report':
        doi_report('../'+args.output[0],collection,years)
    elif args.report_name[0] == 'file_issues':
        file_report('../'+args.output[0],collection,years)
    else:
        print(args.report_name[0],' is not known')

