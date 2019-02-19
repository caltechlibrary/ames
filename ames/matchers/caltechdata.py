import os,subprocess,json,re
from caltechdata_api import caltechdata_edit
from ames import codemeta_to_datacite
import dataset
import requests

def match_cd_refs():
    
    token = os.environ['TINDTOK']

    matches = []
    collection = "caltechdata.ds"
    keys = dataset.keys(collection)
    if 'mediaupdate' in keys:
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

def add_citation(collection,token,production=True):
    keys = dataset.keys(collection)
    for k in keys:
        record,err = dataset.read(collection,k)
        if err != '':
            print(err)
            exit()
        description = record['descriptions']
        cite_exists = False
        for d in description:
            descr_text = d['description']
            if descr_text.startswith('<br>Cite this record as:'):
                cite_exists = True
        if cite_exists == False:
            record_doi = record['identifier']['identifier']
            citation_link =\
            'https://data.datacite.org/text/x-bibliography;style=apa/'
            citation = requests.get(citation_link+record_doi).text
            doi_url = 'https://doi.org/'+record_doi.lower()
            if doi_url in citation:
                #Check that we have a citation and not a server error,
                #otherwise wait till next time
                citation = citation.replace(doi_url,'<a href="'+doi_url+'">'+doi_url+'</a>')
                #Replace link text with HTML link
                n_txt = '<br>Cite this record as:<br>'+citation+\
                    '<br> or choose a <a href="https://crosscite.org/?doi='\
                    +record_doi+'"> different citation style</a>'
                description.append({'descriptionType':'Other','description':n_txt})
                response =\
                caltechdata_edit(token,k,{'descriptions':description},{},{},production)
                print(response)
