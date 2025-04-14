import csv, json
import requests
from caltechdata_api import caltechdata_edit

# function to get metadata for a record
def get_record_metadata(record_id):
    metadata_url = f"https://authors.library.caltech.edu/api/records/{record_id}"
    headers = {}
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-type": "application/json",
        }

    response = requests.get(metadata_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Failed to fetch metadata for record {record_id}. Status code: {response.status_code}")
        return None
    
    try:
        metadata = response.json()
        return metadata
    except ValueError:
        print(f"Error: Unable to parse JSON response for record {record_id}.")
        return None

# function to check and update related identifiers
def update_related_identifiers(metadata, links, source_type):
    related_identifiers = metadata.get("metadata", {}).get("related_identifiers", [])
    updated = False

    for link, classification in links:
        if classification not in ["Other", "DOI"]:
            continue

        if not any(identifier.get("identifier") == link for identifier in related_identifiers):
            relation_type = {"id": "issupplementedby"}
            resource_type = {"id": "dataset" if source_type == "data" else "software"}
            scheme = "url" if classification == "Other" else "doi"
            
            new_identifier = {
                "relation_type": relation_type,
                "identifier": link,
                "scheme": scheme,
                "resource_type": resource_type
            }
            related_identifiers.append(new_identifier)
            updated = True

    if updated:
        metadata["metadata"]["related_identifiers"] = related_identifiers

    return metadata, updated

# save updated metadata to a file
def save_metadata_to_file(metadata, record_id):
    file_name = f"{record_id}_updated_metadata.json"
    with open(file_name, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata saved to {file_name}")
    

def check_doi(doi, production=True):
    # Returns whether or not a DOI has already been added to CaltechAUTHORS

    if production == True:
        url = "https://authors.library.caltech.edu/api/records"
    else:
        url = "https://authors.caltechlibrary.dev/api/records"

    query = f'?q=pids.doi.identifier:"{doi}"'

    response = requests.get(url + query)
    if response.status_code != 200:
        raise Exception(response.text)
    else:
        metadata = response.json()
        if metadata["hits"]["total"] > 0:
            return metadata["hits"]["total"]
        else:
            return False


def add_journal_metadata(request, token, test=False):
    # For a given request, determine whether we need to add journal metadata

    if test:
        base = "https://authors.caltechlibrary.dev"
    else:
        base = "https://authors.library.caltech.edu"
    request_url = base + "/api/requests/" + request
    record_url = base + "/api/records/"

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }
    response = requests.get(request_url, headers=headers)
    if response.status_code != 200:
        print(f"retures {request} not found")
    data = response.json()
    record = data["topic"]["record"]
    record_url = record_url + record + "/draft"
    response = requests.get(record_url, headers=headers)
    if response.status_code != 200:
        print(f"record {record} not found")
    data = response.json()

    if "custom_fields" in data:
        journals = {}
        if "caltech:journals" in data["custom_fields"]:
            with open("journal-names.tsv") as file:
                reader = csv.reader(file, delimiter="\t")
                for row in reader:
                    journals[row[0]] = {"name": row[1], "publisher": row[2]}
            issn = data["custom_fields"]["caltech:journals"]["id"]
            journal = journals[issn]
            journal_block = {"issn": issn}
            journal_block["title"] = journal["name"]
            data["custom_fields"]["journal:journal"] = journal_block
            data["metadata"]["publisher"] = journal["publisher"]

            # Update record
            response = requests.put(record_url, headers=headers, data=json.dumps(data))
            if response.status_code != 200:
                print(f"Error updating {record} {response}")
            else:
                print(f"Updated {record}")
                comment = f'Ames bot added journal metadata {journal_block} and publisher {journal["publisher"]}'
                comment_data = {"payload": {"content": comment, "format": "html"}}
                response = requests.post(
                    request_url + "/comments",
                    headers=headers,
                    data=json.dumps(comment_data),
                )
                if response.status_code != 201:
                    print(f"Error adding comment to {request} {response}")
                else:
                    print(f"Added comment to {request}")


def edit_author_identifier(
    record,
    token,
    old_identifier,
    new_identifier,
    test=False,
    add=False,
    new_scheme=None,
):
    # For a given record, change the person identifers from the old to the new

    if test:
        rurl = "https://authors.caltechlibrary.dev/api/records/" + record
    else:
        rurl = "https://authors.library.caltech.edu/api/records/" + record

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    data = requests.get(rurl, headers=headers).json()

    update = False
    for creator in data["metadata"]["creators"]:
        block = creator["person_or_org"]
        if "identifiers" in block:
            existing = False
            match = False
            for idv in block["identifiers"]:
                if idv["identifier"] == new_identifier:
                    existing = True
                if idv["identifier"] == old_identifier:
                    match = True
                    if not add:
                        update = True
                        idv["identifier"] = new_identifier
            if add:
                if match == True:
                    if existing == False:
                        update = True
                        done = False
                        for idv in block["identifiers"]:
                            if idv["scheme"] == new_scheme:
                                idv["identifier"] = new_identifier
                                done = True
                        if done == False:
                            block["identifiers"].append(
                                {"identifier": new_identifier, "scheme": new_scheme}
                            )

    if update == True:
        print(record)
        caltechdata_edit(
            record,
            metadata=data,
            token=token,
            production=True,
            publish=True,
            authors=True,
        )


def add_group(record, token, group_identifier, test=False):
    # For a given record, add a Caltech group identifier

    if test:
        rurl = "https://authors.caltechlibrary.dev/api/records/" + record
    else:
        rurl = "https://authors.library.caltech.edu/api/records/" + record

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    data = requests.get(rurl, headers=headers).json()

    if "custom_fields" in data and "caltech:groups" in data["custom_fields"]:
        data["custom_fields"]["caltech:groups"].append({"id": group_identifier})
    elif "custom_fields" in data:
        data["custom_fields"]["caltech:groups"] = [{"id": group_identifier}]
    else:
        data["custom_fields"] = {"caltech:groups": [{"id": group_identifier}]}

    caltechdata_edit(
        record,
        metadata=data,
        token=token,
        production=not test,
        publish=True,
        authors=True,
    )


def add_doi(record, token, test=False):
    # Add a locally minted DOI to a record

    if test:
        rurl = "https://authors.caltechlibrary.dev/api/records/" + record
    else:
        rurl = "https://authors.library.caltech.edu/api/records/" + record

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    data = requests.get(rurl, headers=headers).json()

    if "doi" in data["pids"]:
        print(
            f"DOI {data['pids']['doi']['identifier']} already assigned to this record"
        )
    else:
        data["pids"]["doi"] = {
            "provider": "datacite",
            "identifier": f"10.7907/{record}",
            "client": "datacite",
        }
        caltechdata_edit(
            record,
            metadata=data,
            token=token,
            production=not test,
            publish=True,
            authors=True,
        )


def move_doi(record, token, test=False):
    # Move DOI from alternative identifier to DOI field

    if test:
        rurl = "https://authors.caltechlibrary.dev/api/records/" + record
    else:
        rurl = "https://authors.library.caltech.edu/api/records/" + record

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    data = requests.get(rurl, headers=headers).json()

    doi = None
    identifiers = []

    if "identifiers" in data["metadata"]:
        for idv in data["metadata"]["identifiers"]:
            if idv["scheme"] == "doi":
                doi = idv["identifier"]
            else:
                identifiers.append(idv)

    if doi == None:
        print(f"No DOI found for {record}")
        exit()
    else:
        data["pids"]["doi"] = {
            "provider": "external",
            "identifier": doi,
        }
        data["metadata"]["identifiers"] = identifiers
        caltechdata_edit(
            record,
            metadata=data,
            token=token,
            production=not test,
            publish=True,
            authors=True,
        )


def add_related_identifiers_from_csv(csv_path, test=False):
    """Reads a CSV file and adds related identifiers to each record using the CaltechDATA API."""

    base_url = "https://data.caltechlibrary.dev" if test else "https://data.caltechlibrary.caltech.edu"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-type": "application/json",
    }

    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            record_id = row['Test_ID']
            doi = row['CaltechAUTHORS_DOI']
            caltech_author_id = row['CaltechAUTHORS_ID']
            resource_type = row['resource_type']

            print(f"\nProcessing Test_ID: {record_id} with DOI: {doi} and CaltechAUTHORS_ID: {caltech_author_id}")
            print(f"Using resource_type: {resource_type}")

            # Fetch the current record
            response = requests.get(f"{base_url}/api/records/{record_id}", headers=headers)
            if response.status_code != 200:
                print(f"Error fetching record {record_id}: {response.status_code}")
                continue
            record_data = response.json()

            # Draft check or create
            draft_response = requests.get(f"{base_url}/api/records/{record_id}/draft", headers=headers)
            if draft_response.status_code == 200:
                record_data = draft_response.json()
            else:
                draft_create_response = requests.post(f"{base_url}/api/records/{record_id}/draft", headers=headers)
                if draft_create_response.status_code != 201:
                    print(f"Error creating draft: {draft_create_response.status_code}")
                    continue
                record_data = draft_create_response.json()

            related_identifiers = record_data.get("metadata", {}).get("related_identifiers", []) or []

            doi_exists = any(ri.get("identifier") == doi for ri in related_identifiers)
            author_url = f"https://authors.library.caltech.edu/records/{caltech_author_id}"
            author_url_exists = any(ri.get("identifier") == author_url for ri in related_identifiers)

            if not doi_exists:
                related_identifiers.append({
                    "relation_type": {"id": "issupplementedby"},
                    "identifier": doi,
                    "scheme": "doi",
                    "resource_type": {"id": resource_type}
                })
                print(f"Adding DOI: {doi}")
            else:
                print(f"DOI already exists")

            if not author_url_exists:
                related_identifiers.append({
                    "relation_type": {"id": "isreferencedby"},
                    "identifier": author_url,
                    "scheme": "url",
                    "resource_type": {"id": resource_type}
                })
                print(f"Adding CaltechAUTHORS link: {author_url}")
            else:
                print(f"CaltechAUTHORS link already exists")

            record_data["metadata"]["related_identifiers"] = related_identifiers

            update_response = requests.put(
                f"{base_url}/api/records/{record_id}/draft", headers=headers, json=record_data
            )
            if update_response.status_code != 200:
                print(f"Error updating draft: {update_response.status_code}")
                continue

            publish_response = requests.post(
                f"{base_url}/api/records/{record_id}/draft/actions/publish", headers=headers
            )
            if publish_response.status_code != 202:
                print(f"Error publishing record {record_id}: {publish_response.status_code}")
                continue

            print(f"Successfully updated and published {record_id}")

    print("All records processed.")

def generate_data_citation_csv():
    
    def doi2url(doi):
        if not doi.startswith("10."):
            return doi
        req_url = f"https://doi.org/api/handles/{doi}"
        resp = requests.get(req_url, allow_redirects=True)
        if resp.status_code == 200:
            for v in resp.json().get("values", []):
                if v["type"] == "URL":
                    resolved_url = v["data"]["value"]
                    if "data.caltech.edu/records/" in resolved_url:
                        caltechdata_id = resolved_url.split("/records/")[-1]
                        if caltechdata_id.isdigit():
                            final_resp = requests.get(resolved_url, allow_redirects=True)
                            resolved_url = final_resp.url
                    return resolved_url
        return doi

    def fetch_metadata(record_id):
        url = f"https://authors.library.caltech.edu/api/records/{record_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except:
            return None

    def fetch_resource_type(data):
        def search(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == 'resource_type' and isinstance(v, dict) and 'id' in v:
                        return v['id']
                    result = search(v)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = search(item)
                    if result:
                        return result
            return None
        return search(data) or 'N/A'

    def search_records(prefix):
        base_url = "https://authors.library.caltech.edu/api/records"
        query = f'?q=metadata.related_identifiers.identifier:["{prefix}/0" TO "{prefix}/z"]&size=1000'
        url = base_url + query
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def extract_data_citations(hits):
        citations = []
        for hit in hits:
            record_id = hit["id"]
            metadata = fetch_metadata(record_id)
            if not metadata:
                continue

            caltechauthors_doi = metadata.get("pids", {}).get("doi", {}).get("identifier", "")
            resource_type = fetch_resource_type(metadata)

            related_dois = []
            for identifier in metadata.get("metadata", {}).get("related_identifiers", []):
                if identifier.get("scheme") == "doi":
                    doi = identifier["identifier"]
                    if any(doi.startswith(prefix) for prefix in ["10.22002/", "10.14291/", "10.25989/"]):
                        related_dois.append(doi)

            for doi in related_dois:
                caltechdata_url = doi2url(doi)

                if "data.caltech.edu/records/" in caltechdata_url:
                    caltechdata_id = caltechdata_url.split("/records/")[-1]
                    caltechdata_metadata = requests.get(f"https://data.caltech.edu/api/records/{caltechdata_id}").json()

                    cross_link = "No"
                    for identifier in caltechdata_metadata.get("metadata", {}).get("related_identifiers", []):
                        if identifier.get("identifier") == caltechauthors_doi:
                            cross_link = "Yes"
                            break

                    citations.append({
                        "CaltechAUTHORS_ID": record_id,
                        "CaltechAUTHORS_DOI": caltechauthors_doi,
                        "Related_DOI": doi,
                        "CaltechDATA_ID": caltechdata_id,
                        "Cross_Link": cross_link,
                        "resource_type": resource_type
                    })
        return citations

    prefixes = ["10.22002", "10.14291", "10.25989"]
    all_citations = []

    for prefix in prefixes:
        results = search_records(prefix)
        if results and "hits" in results:
            all_citations.extend(extract_data_citations(results["hits"]["hits"]))

    output_file = "data_citations_with_type.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["CaltechAUTHORS_ID", "CaltechAUTHORS_DOI", "Related_DOI", "CaltechDATA_ID", "Cross_Link", "resource_type"])
        for citation in all_citations:
            writer.writerow([
                citation["CaltechAUTHORS_ID"],
                citation["CaltechAUTHORS_DOI"],
                citation["Related_DOI"],
                citation["CaltechDATA_ID"],
                citation["Cross_Link"],
                citation["resource_type"]
            ])

    print(f"Saved {len(all_citations)} citations to {output_file}")
