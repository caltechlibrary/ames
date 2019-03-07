import os,argparse,csv
import dataset
import random
from progressbar import progressbar
from ames.harvesters import get_caltechfeed, get_records
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

def keep_record(metadata,years,item_type,group):
    keep = True
    
    if years:
        #Not implemented for CaltechDATA
        if 'date' in metadata:
            year = metadata['date'].split('-')[0]
            if is_in_range(years,year) == False:
                keep = False
        else:
            keep = False

    monograph_types = ["discussion_paper",
            "documentation",
            "manual",
            "other",
            "project_report",
            "report",
            "technical_report",
            "white_paper",
            "working_paper"]

    if item_type:
        #CaltechDATA item
        if 'resourceTye' in metadata:
            if metadata['resourceType']['resourceTypeGeneral'] not in item_type:
                keep = False
        #Eprints item
        elif 'type' in metadata:
            if 'monograph_type' in metadata:
                #There are records with monograph_type that arn't monographs
                if metadata['type'] == 'monograph':
                    if metadata['monograph_type'] not in item_type and\
                    metadata['type'] not in item_type:
                        keep=False 
                else:
                    if metadata['type'] not in item_type:
                        keep=False
            else:
                if metadata['type'] not in item_type:
                    keep=False    
        else:   
            print("Item type not found in record")
            keep=False

    if group:
        #Not implemented for CaltechDATA
        if 'local_group' in metadata:
            match = False
            if isinstance(metadata['local_group']['items'],list) == False:
                #Deal with single item listings
                metadata['local_group']['items'] = [metadata['local_group']['items']]
            for gname in metadata['local_group']['items']:
                if gname in group:
                    match = True
            if match == False:
                keep = False
        else:
            keep = False
    return keep

def doi_report(file_obj,keys,source,years=None,all_records=True,item_type=None,group=None):
    '''Output a report of DOIs '''
    file_obj.writerow(["Eprint ID","DOI","Year","Author ID","Title","Resolver URL"])
    all_metadata = []
    if source.split('.')[-1] == 'ds':
        dot_paths =\
            ['._Key','.doi','.official_url','.date','.related_url','.creators','.title','.local_group','.type','.monograph_type']
        labels=\
            ['eprint_id','doi','official_url','date','related_url','creators','title','local_group','type','monograph_type']
        all_metadata = get_records(dot_paths,'dois',source,keys,labels)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))

    for metadata in all_metadata:
        doi = ''

        #Determine if we want the record
        if keep_record(metadata,years,item_type,group):

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
            if 'date' in metadata:
                year = metadata['date'].split('-')[0]
            else:
                year = ''
            if all_records == False:
                if doi != '':
                    file_obj.writerow([ep,doi,year,author,title,url])
            else:
                file_obj.writerow([ep,doi,year,author,title,url])

def status_report(file_obj,keys,source):
    '''Output a report of items that have a status other than archive
    or have metadata visability other than show.  
    Under normal circumstances this should return no records when run on feeds'''
    file_obj.writerow(["Eprint ID","Resolver URL","Status"])
        
    all_metadata = []
    if source.split('.')[-1] == 'ds':
        dot_paths = ['._Key',
        '.eprint_status','.official_url','.metadata_visibility']
        labels =\
        ['eprint_id','eprint_status','official_url','metadata_visibility']
        all_metadata = get_records(dot_paths,'dois',source,keys,labels)
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
        if metadata['metadata_visibility'] != 'show':
            print(metadata['metadata_visibility'])
            ep = metadata['eprint_id']
            status = metadata['metadata_visibility']
            url = metadata['official_url']
            print("Record matched: ",url)
            file_obj.writerow([ep,url,status])
        
def license_report(file_obj,keys,source,item_type=None):
    '''Write report with license types'''
    file_obj.writerow(["License Name","Number of Records","IDs"])
    if source.split('.')[0] != 'CaltechDATA':
        print(source.split('.')[0]+ " is not supported for license report")
        exit()
    else:
        all_metadata = []
        dot_paths = ['._Key','.rightsList','.resourceType']
        labels = ['id','rightsList','resourceType']
        all_metadata = get_records(dot_paths,'dois',source,keys,labels)
        licenses = {}
        for metadata in all_metadata:
            if item_type != None:
                #Restrict to a specific item type
                if metadata['resourceType']['resourceTypeGeneral'] == item_type:
                    license = metadata['rightsList'][0]['rights']
                else:
                    license = None
            #Otherwise we always save license
            else:
                license = metadata['rightsList']['rights']
            
            if license != None:
                if license in licenses:
                    licenses[license]['count'] += 1
                    licenses[license]['ids'].append(metadata['id']) 
                else:
                    new = {}
                    new['count'] = 1
                    new['ids'] = [metadata['id']]
                    licenses[license] = new

        for license in licenses:
            file_obj.writerow([license,licenses[license]['count'],licenses[license]['ids']])

def file_report(file_obj,keys,source,years=None):
    '''Write out a report of files with potential issues'''
    file_obj.writerow(["Eprint ID","Problem","Impacted Files","Resolver URL"])
    
    all_metadata = []
    if source.split('.')[-1] == 'ds':
        dot_paths = ['._Key', '.documents','.date','.official_url']
        labels = ['eprint_id','documents','date','official_url']
        all_metadata = get_records(dot_paths,'dois',source,keys,labels)
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
        labels = ['eprint_id','items']
        all_metadata = get_records(dot_paths,'dois',source,keys,labels)
        for metadata in progressbar(all_metadata, redirect_stdout=True):
            key=metadata['eprint_id']
            if 'items' in metadata:
                find_creators(metadata['items'],key,creators,creator_ids)
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
            if creator['orcids'] and creator['update_ids']:
                write=True
        else:
            write=True
        if write==True:
            orcid = "|".join(creator['orcids'])
            eprint_ids = "|".join(creator['eprint_ids'])
            update_ids = "|".join(creator['update_ids'])
            if len(creator['orcids']) > 1:
                #All items will need to be updated if there are multiple orcids
                update_ids = update_ids + '|' + eprint_ids
                eprint_ids = ''
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
                #Existing creator
                if orcid != '':
                    if not orcid in creators[creator_id]['orcids']:
                        #Creator has multiple orcids
                        creators[creator_id]['orcids'].append(orcid)
                        creators[creator_id]['update_ids'].append(eprint_id)
                    else:
                        creators[creator_id]['eprint_ids'].append(eprint_id)
                else:
                    #We always want to (potentially) update blank orcids
                    creators[creator_id]['update_ids'].append(eprint_id)
            else:
                # We have a new creator
                creators[creator_id] = {}
                if orcid != '':
                    creators[creator_id]['orcids'] = [orcid]
                    creators[creator_id]['eprint_ids'] = [eprint_id]
                    creators[creator_id]['update_ids'] = []
                else:
                    creators[creator_id]['orcids'] = []
                    creators[creator_id]['eprint_ids'] = []
                    creators[creator_id]['update_ids'] = [eprint_id]
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
        'options: thesis, authors, caltechdata, test (if using eprints source)')
    parser.add_argument('-source', default='feeds',help=\
        'options: feeds (default), eprints')
    parser.add_argument('output', help=\
        'output tsv name')
    parser.add_argument('-years', help='format: 1939 or 1939-1940')
    parser.add_argument('-item', nargs='+', help=\
            'Item type from repository (e.g. Dataset or "technical_report")')
    parser.add_argument('-group', nargs='+', help=\
            'Group from repository (e.g. "Keck Institute for Space Studies")')
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

    with open('../'+args.output,'w',encoding = 'utf-8') as fout:
        if args.output.split('.')[-1] == 'tsv':
            file_out = csv.writer(fout,delimiter='\t')
        else:
            file_out = csv.writer(fout)
        
        if args.report_name == 'file_report':
            file_report(file_out,keys,source,args.years)
        elif args.report_name == 'creator_report':
            creator_report(file_out,keys,source,update_only=True)
        elif args.report_name == 'status_report':
            status_report(file_out,keys,source)
        elif args.report_name == 'doi_report':
            doi_report(file_out,keys,source,years=args.years,all_records=True,item_type=args.item,group=args.group)
        elif args.report_name == 'license_report':
            license_report(file_out,keys,source,item_type=args.item)
        else:
            print(args.report_name,' is not known')

