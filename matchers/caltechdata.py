import os,subprocess,json,re
from caltechdata_api import caltechdata_edit
import dataset

def match_cd_refs():
    
    os.environ['AWS_SDK_LOAD_CONFIG']="1"
    token = os.environ['TINDTOK']

    matches = []

    keys =\
    subprocess.check_output(["dataset","-c","s3://dataset.library.caltech.edu/CaltechDATA","keys"],universal_newlines=True).splitlines()
    for k in keys:
        print(k)
        metadata =\
        subprocess.check_output(["dataset","-c","s3://dataset.library.caltech.edu/CaltechDATA","read",k],universal_newlines=True)
        metadata = json.loads(metadata)['metadata']
        results =\
                subprocess.check_output(["dataset","-json","find","crossref_refs.bleve","+obj_id:*"+metadata['doi']],universal_newlines=True)
        results = json.loads(results)
        for h in results['hits']:
            new = True
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
                            ids.append({"relatedIdentifier":m['relatedIdentifier'],\
                                "relatedIdentifierType":m['relatedIdentifierScheme'],\
                                "relationType":m["relatedIdentifierRelation"]})
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
        existing = dataset.read(collection,k)
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
            dataset.update(collection,k,existing)

