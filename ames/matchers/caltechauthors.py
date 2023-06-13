import csv, json
import requests


def add_journal_metadata(request, token):
    # For a given request, determine whether we need to add journal metadata

    request_url = "https://authors.caltechlibrary.dev/api/requests/" + request
    record_url = "https://authors.caltechlibrary.dev/api/records/"

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
