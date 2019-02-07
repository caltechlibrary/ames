import os,argparse,csv
import dataset
from progressbar import progressbar
from ames.harvesters import get_caltechfeed
from ames.harvesters import get_eprint_keys, get_eprint

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
    '''Output a report of DOIs (in the DOI field'''
    with open(fname,'w') as fout:
        tsvout = csv.writer(fout,delimiter='\t')
        tsvout.writerow(["Eprint ID","DOI","Year","Author ID","Title","Resolver URL"])
        keys = dataset.keys(collection)
        for k in progressbar(keys, redirect_stdout=True):
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
                    if 'title' not in metadata:
                        print(metadata)
                        exit()
                    title = metadata['title']
                    url = metadata['official_url']
                    print("Record matched: ",url)
                    tsvout.writerow([ep,doi,year,author,title,url])

def status_report(fname,collection):
    '''Output a report of items in feeds that have a status other than archive.
    Under normal circumstances this should return no records'''
    with open(fname,'w') as fout:
        tsvout = csv.writer(fout,delimiter='\t')
        tsvout.writerow(["Eprint ID","Resolver URL","Status"])
        keys = dataset.keys(collection)
        for k in progressbar(keys, redirect_stdout=True):
            if k != 'captured':
                metadata,err = dataset.read(collection,k)
                if metadata['eprint_status'] != 'archive':
                    ep = metadata['eprint_id']
                    status = metadata['eprint_status']
                    url = metadata['official_url']
                    print("Record matched: ",url)
                    tsvout.writerow([ep,url,status])


def file_report(file_obj,keys,source,years=None):
    '''Write out a report of files with potential issues'''
    file_obj.writerow(["Eprint ID","Problem","Impacted Files","Resolver URL"])
    
    for k in progressbar(keys, redirect_stdout=True):
        if source.split('.')[-1] == 'ds':
            metadata,err = dataset.read(source,k)
        else:
            metadata = get_eprint(source, k)
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
                                    file_obj.writerow([ep,'HTML File',filename,url])
                                if extension == 'htm':
                                    ep = metadata['eprint_id']
                                    url = metadata['official_url']
                                    print("HTM: ",url)
                                    file_obj.writerow([ep,'HTML File',filename,url])
                                if len(filename) > 200:
                                    ep = metadata['eprint_id']
                                    url = metadata['official_url']
                                    print("Length: ",url)
                                    file_obj.writerow([ep,'File Name Length',filename,url])

def creator_report(file_obj,keys,source):
    creators = {}
    creator_ids = []
    i = 0
    j = 0
    print(f"Processing {len(keys)} eprint records for creators")
    for eprint_id in progressbar(keys, redirect_stdout=True):
        if source.split('.')[-1] == 'ds':
            metadata,err = dataset.read(source,eprint_id)
        else:
            metadata = get_eprint(source, eprint_id)
        if metadata != None:
            if 'creators' in metadata and 'items' in metadata['creators']:
                items = metadata['creators']['items']
                for item in items:
                    if 'id' in item:
                        creator_id = item['id']
                        orcid = ''
                        if 'orcid' in item:
                            orcid = item['orcid']
                        if creator_id in creators:
                            creators[creator_id]['eprint_ids'].append(eprint_id)
                            if orcid != '':
                                if not orcid in creators[creator_id]['orcids']:
                                    creators[creator_id]['orcids'].append(orcid)
                            elif orcid == "" and len(creators[creator_id]['orcids']) > 0:
                                creators[creator_id]['update_ids'].append(eprint_id)
                        else:
                            # We have a new creator
                            j += 1
                            creators[creator_id] = {}
                            creators[creator_id]['eprint_ids'] = [eprint_id]
                            creators[creator_id]['update_ids'] = []
                            if orcid != '':
                                creators[creator_id]['orcids'] = [orcid]
                            else:
                                creators[creator_id]['orcids'] = []
                            creator_ids.append(creator_id)
        i += 1
        if (i % 100) == 0:
            print(f"Processed {i} eprints, found {j} creators, last eprint id processed {eprint_id}")
    print(f"Processed {i} eprints, found {j} creators, total")

    creator_ids.sort()
    file_obj.writerow(["creator_id","orcid","eprint_id","update_ids"])
    for creator_id in creator_ids:
        creator = creators[creator_id]
        orcid = "|".join(creator['orcids'])
        eprint_ids = "|".join(creator['eprint_ids'])
        update_ids = "|".join(creator['update_ids'])
        print(f"Writing: {creator_id},{orcid},{eprint_ids},{update_ids}")
        file_obj.writerow([creator_id,orcid,eprint_ids,update_ids])
    print("All Done!")

if __name__ == '__main__':
    if os.path.isdir('data') == False:
        os.mkdir('data')
    os.chdir('data')

    parser = argparse.ArgumentParser(description=\
        "Run a report on CODA repositories")
    parser.add_argument('report_name', help=\
        'report name (options: doi_report,file_report,status_report)')
    parser.add_argument('repository', help=\
        'options: thesis, authors')
    parser.add_argument('-source', default='feeds',help=\
        'options: feeds (default), eprints')
    parser.add_argument('output', help=\
        'output tsv name')
    parser.add_argument('-years', help='format: 1939 or 1939-1940')
    parser.add_argument('-username', help='Eprints username')
    parser.add_argument('-password', help='Eprints password')

    args = parser.parse_args()

    if args.source == 'feeds':
        source = get_caltechfeed(args.repository)
        keys = dataset.keys(source)
    elif args.source == 'eprints':
        if args.username:
            source = 'https://'+args.username+':'+args.password+'@'
        else:
            source = 'https://'
        if args.repository == 'authors':
            source += 'authors.library.caltech.edu'
        elif args.repository == 'thesis':
            source += 'thesis.library.caltech.edu'
        else:
            print('Repository not known')
            exit()
        keys = get_eprint_keys(source)
    else:
        print('Source is not feeds or eprints, exiting')
        exit()

    print("Running report for ",args.repository)

    if args.years != None:
        years = args.years
    else:
        years = None

    with open('../'+args.output,'w',encoding = 'utf-8') as fout:
        if args.output.split('.')[-1] == 'tsv':
            file_out = csv.writer(fout,delimiter='\t')
        else:
            file_out = csv.writer(fout)
        
        if args.report_name == 'file_report':
            file_report(file_out,keys,source,years)
        elif args.report_name == 'creator_report':
            creator_report(file_out,keys,source)
        #elif args.report_name == 'file_report':
        #    file_report(file_out,collection,years)
        #elif args.report_name == 'status_report':
        #    status_report(file_out,collection)
        else:
            print(args.report_name,' is not known')

