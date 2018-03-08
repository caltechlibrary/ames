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
                subprocess.check_output(["dsfind","-json","crossref_refs.bleve","+obj_id:*"+metadata['doi']],universal_newlines=True)
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
    collection = 'github_records'
    keys = dataset.keys(collection)
    #keys =\
            #subprocess.check_output(["dataset","-c","github_records","keys"],universal_newlines=True).splitlines()
    for k in keys:
        #Check whether we have looked at this repo

        file_names\
        =subprocess.check_output(["dataset","attachments",k],universal_newlines=True).splitlines()
        os.system("dataset "+" detach "+k)
        codemeta=False
        for f in file_names:
            f = f.split(' ')[0] #Ignoring other file metadata
            if f.split('.')[-1] == 'zip':
                files =\
                subprocess.check_output(['unzip','-l',f.rstrip()],universal_newlines=True).splitlines()
                i = 4 #Ignore header
                line = files[i]
                while line[0] != '-':
                    split = line.split('/')
                    fname = split[-1]
                    if fname == 'codemeta.json':
                        path = ''
                        sp = line.split('   ')[-1]
                        os.system('unzip -j '+f.rstrip()+' '+sp+' -d .')
                        codemeta = True
                    i = i+1
                    line = files[i]
                    #Does not sensibly handle repos with multiple codemeta
                    #files
            os.system('rm '+f)
        
        if codemeta == True:
            token = os.environ['TINDTOK']

            infile = open('codemeta.json','r')
            meta = json.load(infile)
            standardized = codemeta_to_datacite(meta)
            response = caltechdata_edit(token,k,standardized,{},{},True)
            print(response)


