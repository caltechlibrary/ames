import os,argparse,csv
import dataset
import random
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

def get_grid(dot_paths,f_name,d_name,keys):
    if dataset.has_frame(d_name, f_name):
        dataset.delete_frame(source, f_name)
    print("Generating frame")
    f, err = dataset.frame(d_name, f_name, keys, dot_paths)
    if err != '':
        log.fatal(f"ERROR: Can't create {f_name} in {c_name}, {err}")
    return f['grid']

def doi_report(file_obj,keys,source,years=None,all_records=True):
    '''Output a report of DOIs '''
    file_obj.writerow(["Eprint ID","DOI","Year","Author ID","Title","Resolver URL"])
    all_metadata = []
    if source.split('.')[-1] == 'ds':
        dot_paths =\
        ['._Key','.doi','.official_url','.date','.related_url','.creators','.title']
        doi_grid = get_grid(dot_paths,'dois',source,keys)
        for entry in doi_grid:
            item = {}
            item['eprint_id'] = entry[0]
            if entry[1] != None:
                item['doi'] = entry[1]
            item['official_url'] = entry[2]
            if entry[3] != None:
                item['date'] = entry[3]
            if entry[4] != None:
                item['related_url'] = entry[4]
            if entry[5] != None:
                item['creators'] = entry[5]
            item['title'] = entry[6]
            all_metadata.append(item)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))

    for metadata in all_metadata:
        if 'date' in metadata:
            year = metadata['date'].split('-')[0]
            if is_in_range(years,year):
                ep = metadata['eprint_id']
                #Handle odd CaltechAUTHORS DOI setup
                if 'related_url' in metadata and 'items' in metadata['related_url']:
                    items = metadata['related_url']['items']
                    for item in items:
                        if 'url' in item:
                            url = item['url'].strip()
                        if 'type' in item:
                            itype = item['type'].strip().lower()
                        if 'description' in item:
                            description = item['description'].strip().lower()
                        if itype == 'doi' and description == 'article':
                            doi = url
                            break
                elif 'doi' not in metadata:
                    doi = ''
                else:
                    doi = metadata['doi'].strip()
                if 'creators' in metadata:
                    if 'id' in metadata['creators']['items'][0]:
                        author = metadata['creators']['items'][0]['id']
                else:
                    author = ''
                    print("Record is missing author identifier")
                if 'title' not in metadata:
                    print("Record is missing Title")
                    exit()
                title = metadata['title']
                url = metadata['official_url']
                if all_records == False:
                    if doi != '':
                        file_obj.writerow([ep,doi,year,author,title,url])
                else:
                    file_obj.writerow([ep,doi,year,author,title,url])

def status_report(file_obj,keys,source):
    '''Output a report of items that have a status other than archive.
    Under normal circumstances this should return no records when run on feeds'''
    file_obj.writerow(["Eprint ID","Resolver URL","Status"])
        
    all_metadata = []
    if source.split('.')[-1] == 'ds':
        dot_paths = ['._Key', '.eprint_status','.official_url']
        file_grid = get_grid(dot_paths,'files',source,keys)
        for entry in file_grid:
            item = {}
            item['eprint_id'] = entry[0]
            item['eprint_status'] = entry[1]
            item['official_url'] = entry[2]
            all_metadata.append(item)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))
        
    for metadata in all_metadata:
        if metadata['eprint_status'] != 'archive':
            ep = metadata['eprint_id']
            status = metadata['eprint_status']
            url = metadata['official_url']
            print("Record matched: ",url)
            file_obj.writerow([ep,url,status])

def file_report(file_obj,keys,source,years=None):
    '''Write out a report of files with potential issues'''
    file_obj.writerow(["Eprint ID","Problem","Impacted Files","Resolver URL"])
    
    all_metadata = []
    if source.split('.')[-1] == 'ds':
        dot_paths = ['._Key', '.documents','.date','.official_url']
        file_grid = get_grid(dot_paths,'files',source,keys)
        for entry in file_grid:
            item = {}
            item['eprint_id'] = entry[0]
            if entry[1] != None:
                item['documents'] = entry[1]
            if entry[2] != None:
                item['date'] = entry[2]
            item['official_url'] = entry[3]
            all_metadata.append(item)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))

    for metadata in all_metadata:
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

def creator_report(file_obj,keys,source,update_only=False):
    creator_ids = []
    creators = {}
    print(f"Processing {len(keys)} eprint records for creators")
    
    if source.split('.')[-1] == 'ds':
        dot_paths = ['._Key', '.creators.items']
        creator_grid = get_grid(dot_paths,'creators',source,keys)
        for metadata in progressbar(creator_grid, redirect_stdout=True):
            key=metadata[0]
            items = metadata[1]
            if items != None:
                find_creators(items,key,creators,creator_ids)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            metadata = get_eprint(source, eprint_id)
            if metadata != None:
                if 'creators' in metadata and 'items' in metadata['creators']:
                    items = metadata['creators']['items']
                    find_creators(items,eprint_id,creators,creator_ids)
    
    creator_ids.sort()
    file_obj.writerow(["creator_id","orcid","existing_ids","update_ids"])
    for creator_id in creator_ids:
        creator = creators[creator_id]
        #print(creator)
        write = False
        if update_only:
            if creator['update_ids']:
                write=True
        else:
            write=True
        if write==True:
            orcid = "|".join(creator['orcids'])
            eprint_ids = "|".join(creator['eprint_ids'])
            update_ids = "|".join(creator['update_ids'])
            print(f"Writing: {creator_id},{orcid},{eprint_ids},{update_ids}")
            file_obj.writerow([creator_id,orcid,eprint_ids,update_ids])
    print("All Done!")

def find_creators(items,eprint_id,creators,creator_ids):
    '''Take a item list and return creators'''
    for item in items:
        if 'id' in item:
            creator_id = item['id']
            orcid = ''
            if 'orcid' in item:
                orcid = item['orcid']
            if creator_id in creators:
                if orcid != '':
                    if not orcid in creators[creator_id]['orcids']:
                        creators[creator_id]['orcids'].append(orcid)
                elif orcid == "" and len(creators[creator_id]['orcids']) > 0:
                    creators[creator_id]['update_ids'].append(eprint_id)
                else:
                    creators[creator_id]['eprint_ids'].append(eprint_id)
            else:
                # We have a new creator
                creators[creator_id] = {}
                creators[creator_id]['eprint_ids'] = [eprint_id]
                creators[creator_id]['update_ids'] = []
                if orcid != '':
                    creators[creator_id]['orcids'] = [orcid]
                else:
                    creators[creator_id]['orcids'] = []
                creator_ids.append(creator_id)

if __name__ == '__main__':
    if os.path.isdir('data') == False:
        os.mkdir('data')
    os.chdir('data')

    parser = argparse.ArgumentParser(description=\
        "Run a report on CODA repositories")
    parser.add_argument('report_name', help=\
        'report name (options: doi_report,file_report,status_report,creator_report)')
    parser.add_argument('repository', help=\
        'options: thesis, authors, test (if using eprints source)')
    parser.add_argument('-source', default='feeds',help=\
        'options: feeds (default), eprints')
    parser.add_argument('output', help=\
        'output tsv name')
    parser.add_argument('-years', help='format: 1939 or 1939-1940')
    parser.add_argument('-username', help='Eprints username')
    parser.add_argument('-password', help='Eprints password')
    parser.add_argument('-sample', help='Number of records if you want a random sample')

    args = parser.parse_args()

    if args.source == 'feeds':
        source = get_caltechfeed(args.repository)
        keys = dataset.keys(source)
        keys.remove('captured')
    elif args.source == 'eprints':
        if args.username:
            source = 'https://'+args.username+':'+args.password+'@'
        else:
            source = 'https://'
        if args.repository == 'authors':
            source += 'authors.library.caltech.edu'
        elif args.repository == 'thesis':
            source += 'thesis.library.caltech.edu'
        elif args.repository =='test':
            if args.username:
                source = 'http://'+args.username+':'+args.password+'@'
            else:
                source = 'http://'
            source += 'authorstest.library.caltech.edu'
        else:
            print('Repository not known')
            exit()
        keys = get_eprint_keys(source)
    else:
        print('Source is not feeds or eprints, exiting')
        exit()

    if args.sample != None:
        keys = random.sample(keys, int(args.sample))
    keys.sort(key=int, reverse = True)


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
            creator_report(file_out,keys,source,update_only=True)
        elif args.report_name == 'status_report':
            status_report(file_out,keys,source)
        elif args.report_name == 'doi_report':
            doi_report(file_out,keys,source,years,all_records=True)
        else:
            print(args.report_name,' is not known')

