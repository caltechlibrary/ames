import os,subprocess,json,re

def match_cd_refs():
    
    os.environ['AWS_SDK_LOAD_CONFIG']="1"

    #out = subprocess.check_output(["dsfind","crossref_refs.bleve","s3://dataset.library.caltech.edu/CaltechDATA","read",k],universal_newlines=True)

    #dsfind crossref_refs.bleve "https://doi.org/10.6084/m9.figshare.156849"
    keys =\
    subprocess.check_output(["dataset","-c","s3://dataset.library.caltech.edu/CaltechDATA","keys"],universal_newlines=True).splitlines()
    for k in keys:
        metadata =\
        subprocess.check_output(["dataset","-c","s3://dataset.library.caltech.edu/CaltechDATA","read",k],universal_newlines=True)
        metadata = json.loads(metadata)['metadata']
        results =\
                subprocess.check_output(["dsfind",'-json',"crossref_refs.bleve","obj_id:*"+metadata['doi']],universal_newlines=True)
        results = json.loads(results)
        for h in results['hits']:
            #print(h['fields']['subj_id'])
            matched = False
            if 'relatedIdentifiers' in metadata:
                for m in metadata['relatedIdentifiers']:
                    if m['relatedIdentifier'] in h['fields']['subj_id']:
                        matched = True
                    #print(re.match(m['relatedIdentifier'],h['fields']['subj_id']))
                    #print(m['relatedIdentifier'])
            if matched == False:
                print(h['fields']['subj_id'])
                print(h['fields']['obj_id'])
