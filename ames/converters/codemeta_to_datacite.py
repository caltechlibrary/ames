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
