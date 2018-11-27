import os,subprocess,json,re
from caltechdata_api import caltechdata_edit
import dataset

def match_cd_refs():
    
    token = os.environ['TINDTOK']

    matches = []
    collection = "caltechdata.ds"
    keys = dataset.keys(collection)
    keys.remove('mediaupdate')
    for k in keys:
        #Collect matched new links for the record
        record_matches = []
        print(k)
        metadata,err = dataset.read(collection,k)
        if err !="":
            print(f"Unexpected error on read: {err}")
        results,err =\
        dataset.find("crossref_refs.ds.bleve","+obj_id:*"+metadata['identifier']['identifier'])
        if err !="":
            print(f"Unexpected error on find: {err}")
        for h in results['hits']:
            #Trigger for whether we already have this link
            new = True
            print(h)
            if 'relatedIdentifiers' in metadata:
                for m in metadata['relatedIdentifiers']:
                    if m['relatedIdentifier'] in h['fields']['subj_id']:
                        new = False
                    #print(re.match(m['relatedIdentifier'],h['fields']['subj_id']))
                    #print(m['relatedIdentifier'])
            if new == True:
                match = h['fields']['subj_id']
                print(match)
                print(h['fields']['obj_id'])
                inputv = input("Do you approve this link?  Type Y or N: ")
                if inputv == 'Y':
                    record_matches.append(match)
        #If we have to update record
        if len(record_matches) > 0:
            ids = []
            if 'relatedIdentifiers' in metadata:
                for m in metadata['relatedIdentifiers']:
                    ids.append(m)
            matches.append([k,record_matches])
            #Now collect identifiers for record
            for match in record_matches:            
                #matches.append([match,k])
                split = match.split('doi.org/')
                new_id = {"relatedIdentifier":split[1],\
                    "relatedIdentifierType":"DOI",\
                    "relationType":"IsCitedBy"}
                ids.append(new_id)
            newmetadata ={"relatedIdentifiers":ids}
            response = caltechdata_edit(token,k,newmetadata,{},{},True)
            print(response)
    return matches

def codemeta_to_datacite(metadata):
    datacite = {}
    if 'author' in metadata:
        creators = []
        for a in metadata['author']:
            cre = {}
            cre['creatorName'] = a['familyName']+', '+a['givenName']
            cre['familyName'] = a['familyName']
            cre['givenName'] = a['givenName']
            if '@id' in a:
                idv = a['@id']
                split = idv.split('/')
                idn = split[-1]
                cre['nameIdentifiers']=[{\
                        'nameIdentifier':idn,'nameIdentifierScheme':'ORCID','schemeURI':'http://orcid.org'}]
                #Should check for type and remove hard code URI
            if 'affiliation' in a:
                cre['affiliations'] = [a['affiliation']]
                #Should check if can support multiple affiliations
            creators.append(cre)
        datacite['creators'] = creators
    if 'license' in metadata:
        #Assuming uri to name conversion, not optimal
        uri = metadata['license']
        name = uri.split('/')[-1]
        datacite['rightsList'] = [{'rights':name,'rightsURI':uri}]
    if 'keywords' in metadata:
        sub = []
        for k in metadata['keywords']:
            sub.append({"subject":k})
        datacite['subjects']=sub
    if 'funder' in metadata:
        #Kind of brittle due to limitations in codemeta
        fund_list = []
        grant_info = ''
        if 'funding' in metadata:
            grant_info = metadata['funding'].split(',')
        if isinstance(metadata['funder'],list):
            count = 0
            for f in metadata['funder']:
                entry = {'funderName':funder['name']}
                if '@id' in funder:
                    element = {}
                    element['funderIdentifier']=funder['@id']
                    element['funderIdentifierType']='Crossref Funder ID'
                    entry['funderIdentifier']=element
                if grant_info != '':
                    split = grant_info[count].split(';')
                    entry['awardNumber']={'awardNumber':split[0]}
                    if len(split) > 1:
                        entry['awardTitle'] = split[1]
                count = count + 1
        else:
            funder = metadata['funder']
            entry = {'funderName':funder['name']}
            if '@id' in funder:
                element = {}
                element['funderIdentifier']=funder['@id']
                element['funderIdentifierType']='Crossref Funder ID'
                entry['funderIdentifier']=element
            if grant_info != '':
                split = grant_info[0].split(';')
                entry['awardNumber']={'awardNumber':split[0]}
                if len(split) > 1:
                    entry['awardTitle'] = split[1]
            fund_list.append(entry)
            
        datacite['fundingReferences'] = fund_list
    return datacite

def match_codemeta():
    collection = 'github_records.ds'
    keys = dataset.keys(collection)
    for k in keys:
        existing,err = dataset.read(collection,k)
        if err !="":
            print(f"Unexpected error on read: {err}")
        if 'completed' not in existing:
            print('Processing new record')
            if dataset.attachments(collection,k) != '':
                dataset.detach(collection,k)

                #Update CaltechDATA
                token = os.environ['TINDTOK']

                infile = open('codemeta.json','r')
                meta = json.load(infile)
                standardized = codemeta_to_datacite(meta)
                response = caltechdata_edit(token,k,standardized,{},{},True)
                print(response)
                os.system('rm codemeta.json')

            existing['completed'] = 'True'
            err = dataset.update(collection,k,existing)
            if err !="":
                print(f"Unexpected error on read: {err}")

def fix_multiple_links(input_collection,token):
    keys = dataset.keys(input_collection)
    for k in keys:
        record,err = dataset.read(input_collection,k)
        if err != '':
            print(err)
            exit()
        if 'relatedIdentifiers' in record:
            idvs = []
            new = []
            dupes = []
            replace = False
            record_doi = record['identifier']['identifier']
            for idv in record['relatedIdentifiers']:
                idvs.append(idv['relatedIdentifier'])
            for idv in record['relatedIdentifiers']:
                identifier = idv['relatedIdentifier']
                if identifier == record_doi:
                    #Having a related identifier that is the same as the record
                    #doi doesn't make any sense
                    replace = True
                    dupes.append(identifier)
                else:
                    count = idvs.count(identifier)
                    if count > 1:
                        replace = True
                        if identifier not in dupes:
                            #We need to save the first duplicate
                            new.append(idv)
                            #Add to list of those already saved
                            dupes.append(identifier)
                        else:
                            #This will be deleted
                            dupes.append(identifier)
                    else:
                        #Save all unique ids
                        new.append(idv)
            if replace == True:
                print("Duplicate links found in record ",k)
                print("Will delete these links",dupes)
                response = input("Do you approve this change? Y or N")
                new_metadata = {'relatedIdentifiers':new}
                if response == 'Y':
                    response = caltechdata_edit(token,k,new_metadata,{},{},True)
                    print(response)

