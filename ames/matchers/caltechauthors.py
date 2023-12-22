import csv, json
import requests
from caltechdata_api import caltechdata_edit


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


def edit_author_identifier(record, token, old_identifier, new_identifier, test=False):
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

    for creator in data["metadata"]["creators"]:
        block = creator["person_or_org"]
        if "identifiers" in block:
            for idv in block["identifiers"]:
                if idv["identifier"] == old_identifier:
                    idv["identifier"] = new_identifier
    caltechdata_edit(
        record,
        metadata=data,
        token=token,
        production=True,
        publish=True,
        authors=True,
    )


def add_group(record, token, group_identifier, test=False):
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

    if "custom_fields" in data and "caltech:groups" in data["custom_fields"]:
        data["custom_fields"]["caltech:groups"].append({"id": group_identifier})
    elif "custom_fields" in data:
        data["custom_fields"]["caltech:groups"] = [{"id": group_identifier}]}
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
        print(f"DOI {data['pids']['doi']['identifier']} already assigned to this record")
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
