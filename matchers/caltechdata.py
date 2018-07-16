import os,subprocess,json,re
from caltechdata_api import caltechdata_edit
import dataset

def match_cd_refs():
    
    token = os.environ['TINDTOK']

    matches = []
    collection = "s3://dataset.library.caltech.edu/CaltechDATA"
    keys = dataset.keys(collection)
    for k in keys:
        print(k)
        metadata,err = dataset.read(collection,k)
        if err !="":
            print(f"Unexpected error on read: {err}")
        results,err =\
        dataset.find("crossref_refs.ds.bleve","+obj_id:*"+metadata['identifier']['identifier'])
        if err !="":
            print(f"Unexpected error on find: {err}")
        for h in results['hits']:
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
                    matches.append([match,k])
                    split = match.split('doi.org/')
                    new_id = {"relatedIdentifier":split[1],\
                    "relatedIdentifierType":"DOI",\
                    "relationType":"IsCitedBy"}
                    ids = []
                    if 'relatedIdentifiers' in metadata:
                        for m in metadata['relatedIdentifiers']:
                            ids.append(m)
                    ids.append(new_id)
                    newmetadata =\
                    {"relatedIdentifiers":ids}
                    response = caltechdata_edit(token,k,newmetadata,{},{},True)
                    print(response)
    return matches

def codemeta_to_datacite(metadata):
    datacite = {}
    if 'author' in metadata:
        creators = []
        for a in metadata['author']:
            cre = {}
            cre['creatorName'] = a['familyName']+','+a['givenName']
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

