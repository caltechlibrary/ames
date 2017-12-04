import os,subprocess,json,re
from caltechdata_api import caltechdata_edit

def match_cd_refs():
    
    os.environ['AWS_SDK_LOAD_CONFIG']="1"
    token = os.environ['TINDTOK']

    matches = []

    keys =\
    subprocess.check_output(["dataset","-c","s3://dataset.library.caltech.edu/CaltechDATA","keys"],universal_newlines=True).splitlines()
    for k in keys:
        metadata =\
        subprocess.check_output(["dataset","-c","s3://dataset.library.caltech.edu/CaltechDATA","read",k],universal_newlines=True)
        metadata = json.loads(metadata)['metadata']
        results =\
                subprocess.check_output(["dsfind",'-json',"crossref_refs.bleve","+obj_id:*"+metadata['doi']],universal_newlines=True)
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
