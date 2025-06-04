import csv, json
import requests
import dimcli
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
        print(
            f"Error: Failed to fetch metadata for record {record_id}. Status code: {response.status_code}"
        )
        return None

    try:
        metadata = response.json()
        return metadata
    except ValueError:
        print(f"Error: Unable to parse JSON response for record {record_id}.")
        return None


def grid_to_ror(grid):
    if grid == "grid.451078.f":
        ror = "00hm6j694"
    elif grid == "grid.5805.8":
        ror = "02en5vm52"
    elif grid == "grid.465477.3":
        ror = "00em52312"
    elif grid == "grid.412584.e":
        ror = "0431j1t39"
    else:
        url = f"https://api.ror.org/organizations?query.advanced=external_ids.GRID.all:{grid}"
        results = requests.get(url).json()
        if len(results["items"]) == 0:
            ror = None
        else:
            ror = results["items"][0]["id"]
            ror = ror.split("ror.org/")[1]
    return ror


# function to check and update related identifiers
def update_related_identifiers(metadata, links, source_type):
    related_identifiers = metadata.get("metadata", {}).get("related_identifiers", [])
    updated = False

    for link, classification in links:
        if classification not in ["Other", "DOI"]:
            continue

        if not any(
            identifier.get("identifier") == link for identifier in related_identifiers
        ):
            relation_type = {"id": "issupplementedby"}
            resource_type = {"id": "dataset" if source_type == "data" else "software"}
            scheme = "url" if classification == "Other" else "doi"

            new_identifier = {
                "relation_type": relation_type,
                "identifier": link,
                "scheme": scheme,
                "resource_type": resource_type,
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


def add_related_identifiers_from_csv(data_rows, token, test=False):
    """Reads a CSV file and adds related identifiers to each record using the CaltechDATA API."""

    base_url = (
        "https://data.caltechlibrary.dev"
        if test
        else "https://data.caltechlibrary.caltech.edu"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-type": "application/json",
    }
    results = []
    for row in data_rows:
        record_id = row["Test_ID"]
        doi = row["CaltechAUTHORS_DOI"]
        caltech_author_id = row["CaltechAUTHORS_ID"]
        resource_type = row["resource_type"]

        print(
            f"\nProcessing Test_ID: {record_id} with DOI: {doi} and CaltechAUTHORS_ID: {caltech_author_id}"
        )
        print(f"Using resource_type: {resource_type}")

        # Fetch the current record
        response = requests.get(f"{base_url}/api/records/{record_id}", headers=headers)
        if response.status_code != 200:
            print(f"Error fetching record {record_id}: {response.status_code}")
            continue
        record_data = response.json()

        # Draft check or create
        draft_response = requests.get(
            f"{base_url}/api/records/{record_id}/draft", headers=headers
        )
        if draft_response.status_code == 200:
            record_data = draft_response.json()
        else:
            draft_create_response = requests.post(
                f"{base_url}/api/records/{record_id}/draft", headers=headers
            )
            if draft_create_response.status_code != 201:
                print(f"Error creating draft: {draft_create_response.status_code}")
                continue
            record_data = draft_create_response.json()

        related_identifiers = (
            record_data.get("metadata", {}).get("related_identifiers", []) or []
        )

        doi_exists = any(ri.get("identifier") == doi for ri in related_identifiers)
        author_url = f"https://authors.library.caltech.edu/records/{caltech_author_id}"
        author_url_exists = any(
            ri.get("identifier") == author_url for ri in related_identifiers
        )

        if not doi_exists:
            related_identifiers.append(
                {
                    "relation_type": {"id": "issupplementedby"},
                    "identifier": doi,
                    "scheme": "doi",
                    "resource_type": {"id": resource_type},
                }
            )
            print(f"Adding DOI: {doi}")
        else:
            print(f"DOI already exists")

        if not author_url_exists:
            related_identifiers.append(
                {
                    "relation_type": {"id": "isreferencedby"},
                    "identifier": author_url,
                    "scheme": "url",
                    "resource_type": {"id": resource_type},
                }
            )
            print(f"Adding CaltechAUTHORS link: {author_url}")
        else:
            print(f"CaltechAUTHORS link already exists")

        record_data["metadata"]["related_identifiers"] = related_identifiers

        update_response = requests.put(
            f"{base_url}/api/records/{record_id}/draft",
            headers=headers,
            json=record_data,
        )
        if update_response.status_code != 200:
            print(f"Error updating draft: {update_response.status_code}")
            continue

        publish_response = requests.post(
            f"{base_url}/api/records/{record_id}/draft/actions/publish", headers=headers
        )
        if publish_response.status_code != 202:
            print(
                f"Error publishing record {record_id}: {publish_response.status_code}"
            )
            results.append((record_id, False))
            continue

        print(f"Successfully updated and published {record_id}")
        results.append((record_id, True))
    return results


def process_link_updates(input_csv):
    # read the CSV file and build a dictionary: record_id -> {"links": [(link, classification), ...]}
    records_data = {}
    with open(input_file, newline="") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            record_id = row["record_id"].strip()
            link = row["link"].strip()
            classification = row["classification"].strip()

            if record_id not in records_data:
                records_data[record_id] = {"links": []}
            records_data[record_id]["links"].append((link, classification))

    results = []

    for record_id, record_info in records_data.items():
        print(f"Processing record {record_id}")

        # get metadata for the record
        metadata = get_record_metadata(record_id)
        if not metadata:
            # if we failed to get metadata, record the error and continue
            first_link = record_info["links"][0][0] if record_info["links"] else ""
            results.append(
                {
                    "record_id": record_id,
                    "link": first_link,
                    "doi_check": None,
                    "metadata_updated": False,
                    "notes": "Failed to retrieve metadata",
                }
            )
            continue

        # check existing related identifiers in the record
        related_identifiers = metadata.get("metadata", {}).get(
            "related_identifiers", []
        )

        # run check_doi if a "doi" is present among the links
        doi_check = None
        for lk, ctype in record_info["links"]:
            if ctype.lower() == "doi":
                try:
                    doi_check = check_doi(lk, production=True)
                except Exception as e:
                    doi_check = f"Error: {str(e)}"

        # update related identifiers
        updated_metadata, updated_flag = update_related_identifiers(
            metadata, record_info["links"], source_type="data"
        )
        if updated_flag:
            # saving to local JSON file for reference
            save_metadata_to_file(updated_metadata, record_id)
            pass

        # preparing the final row for the results CSV
        first_link = record_info["links"][0][0] if record_info["links"] else ""
        results.append(
            {
                "record_id": record_id,
                "link": first_link,
                "doi_check": doi_check,
                "metadata_updated": updated_flag,
                "notes": "",
            }
        )
    return results
    
def add_authors_affiliations(record, token, dimensions_key, allowed_identifiers=None):
    # Add dimensions affiliations to a record

    record_id = record["id"]
    if "doi" in record["pids"]:
        doi = record["pids"]["doi"]["identifier"]
    else:
        doi = None
        if "identifiers" in record["metadata"]:
            for idv in record["metadata"]["identifiers"]:
                if idv["scheme"] == "doi":
                    doi = idv["identifier"]
    if doi:
        endpoint = "https://cris-api.dimensions.ai/v3"
        dimcli.login(key=dimensions_key, endpoint=endpoint, verbose=False)
        dsl = dimcli.Dsl()
        res = dsl.query_iterative(
            f"""
        search publications
        where doi = "{doi}"
        return publications[basics+extras+abstract] """,
            verbose=False,
        )
        publication = res.json["publications"]
        update = False
        if len(publication) == 1:
            publication = publication[0]
            dimensions_authors = publication.get("authors", [])
            existing_authors = record["metadata"]["creators"]
            if len(dimensions_authors) == len(existing_authors):
                for position in range(len(dimensions_authors)):
                    author = existing_authors[position]
                    dimensions_author = dimensions_authors[position]
                    if "affiliations" not in author:
                        affiliations = []
                        affiliation_ids = []
                        if dimensions_author["affiliations"] not in [[], None]:
                            for affiliation in dimensions_author["affiliations"]:
                                affil = {}
                                if "id" in affiliation:
                                    if affiliation["id"] is not None:
                                        ror = grid_to_ror(affiliation["id"])
                                        if ror is not None:
                                            if allowed_identifiers is not None:
                                                if ror in allowed_identifiers:
                                                    affil["id"] = ror
                                                else:
                                                    print(
                                                        "ROR %s not in allowed identifiers list"
                                                        % ror
                                                    )
                                        else:
                                            print(
                                                "Missing ROR for affiliation %s"
                                                % affiliation["id"]
                                            )
                                # We have to manually handle incorrectly mapped JPL
                                # affiliations
                                if "raw_affiliation" in affiliation:
                                    raw = affiliation["raw_affiliation"]
                                    affil["name"] = raw
                                    if "91109" in raw:
                                        affil["id"] = "027k65916"
                                    if "Jet Propulsion Laboratory" in raw:
                                        affil["id"] = "027k65916"
                                    if "JPL" in raw:
                                        affil["id"] = "027k65916"
                                # Some dimensions records don't include id values.
                                # We ignore those for now
                                if "id" in affil:
                                    if affil["id"] not in affiliation_ids:
                                        update = True
                                        affiliation_ids.append(affil["id"])
                                        affiliations.append(affil)
                            existing_authors[position]["affiliations"] = affiliations
        if update:
            caltechdata_edit(
                record_id,
                metadata=record,
                token=token,
                production=True,
                publish=True,
                authors=True,
            )
