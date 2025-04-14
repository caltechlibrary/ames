import requests, math
import os
import csv
import re

# base URLs
base_url = "https://authors.library.caltech.edu/api/records?q=metadata.additional_descriptions.type.id%3A%22data-availability%22&size=25&sort=bestmatch"
base_file_url_template = "https://authors.library.caltech.edu/api/records/{record_id}/files"

# authorization token
token = os.environ.get("RDMTOK")

# output for data-availability and code-availability
publisher_output_file = "publisher_links.csv"
rest_output_file = "non_publisher_links.csv"
code_publisher_output_file = "code_publisher_links.csv"
code_rest_output_file = "code_non_publisher_links.csv"

# output for checking file presence
file_present_output_file = "files_present.csv"
file_absent_output_file = "files_absent.csv"

# URL patterns for classifying "supplemental_publisher" links
supplemental_patterns = [
    r"https://journals.aps.org/.*/supplemental/",
    r"https://pubs.acs.org/doi/suppl/",
    r"https://www.science.org/doi/suppl/.*/suppl_file/",
    r"https://static-content.springer.com/esm/.*"  
]

# publisher domains dictionary for classifying "publisher" links
publisher_domains = {
    "https://agupubs.onlinelibrary.wiley.com": "publisher",
    "https://www.nature.com": "publisher",
    "https://www.science.org": "publisher",
    "https://pubs.acs.org": "publisher",
    "https://journals.aps.org": "publisher",
    "https://www.sciencedirect.com": "publisher",  
    "https://journals.plos.org": "publisher",      
    "https://www.pnas.org/doi/": "publisher",     
    "https://iopscience.iop.org/article/": "publisher",  
    "https://febs.onlinelibrary.wiley.com/": "publisher", 
    "https://www.mdpi.com/": "publisher"          
}

# classifying links
def classify_link(link):
    for pattern in supplemental_patterns:
        if re.match(pattern, link):
            return "supplemental_publisher"
    
    for domain in publisher_domains:
        if link.startswith(domain):
            return publisher_domains[domain]
    
    if "doi" in link:
        return "DOI"
    
    return "other"

# extracting all https links from a string
def extract_https_links(description):
    return re.findall(r'https://[^\s"]+', description)

# cleaning up the link
def clean_link(link):
    link = link.split('<')[0].rstrip('/')
    return link

# function to extract the filename from the link
def extract_filename_from_link(link):
    return link.split('/')[-1]

# function to check if the file exists in the record file list
def is_file_present(record_id, filename):
    file_url = base_file_url_template.format(record_id=record_id)
    headers = {}
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-type": "application/json",
        }

    response = requests.get(file_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Status code {response.status_code} received when checking files for record {record_id}.")
        return False

    try:
        data = response.json()
    except ValueError:
        print(f"Error: Unable to parse JSON response for record {record_id}.")
        return False

    files = data.get("entries", data.get("files", []))

    if not isinstance(files, list):
        print(f"Error: Unexpected structure for files in record {record_id}. Expected a list, got {type(files)}.")
        return False

    for file in files:
        if isinstance(file, dict) and file.get("key") == filename:
            return True
    
    return False


def get_pending_requests(token, community=None, return_ids=False, test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/requests?q=is_open:true"
    else:
        url = "https://authors.library.caltech.edu/api/requests?q=is_open:true"

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    if community:
        url += "%20AND%20receiver.community:" + community
    response = requests.get(url, headers=headers)
    total = response.json()["hits"]["total"]
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in range(1, pages + 1):
        chunkurl = f"{url}&size=1000&page={c}"
        response = requests.get(chunkurl, headers=headers).json()
        hits += response["hits"]["hits"]

    req = []
    for item in hits:
        if return_ids:
            req.append(item["topic"]["record"])
        else:
            req.append(item["id"])
    return req


def get_request_id_title(token, request):
    url = f" https://authors.library.caltech.edu/api/requests/{request}"
    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error getting comments for request {request}")
    response = response.json()
    date = response["updated"].split("T")[0]
    return response["topic"]["record"], response["title"], date


def get_request_comments(token, request):
    url = f" https://authors.library.caltech.edu/api/requests/{request}/timeline"
    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error getting comments for request {request}")
    comments = response.json()["hits"]["hits"]
    cleaned = []
    for c in comments:
        cleaned.append(c["payload"]["content"])
    return cleaned


def get_publisher(token, record, test=False, draft=True):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"
    url = url + "/" + record
    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }
    if draft:
        url = url + "/draft"
    response = requests.get(url, headers=headers)
    return response.json()["metadata"].get("publisher")


def get_author_records(token, author_identifier, year=None, test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = f'?q=metadata.creators.person_or_org.identifiers.identifier%3A"{author_identifier}"'

    if year:
        query += (
            f"%20AND%20metadata.publication_date%3A%5B{year}-01-01%20TO%20%2A%20%5D"
        )

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    url = url + query
    response = requests.get(url, headers=headers)
    total = response.json()["hits"]["total"]
    print(total)
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in range(1, pages + 1):
        chunkurl = f"{url}&size=1000&page={c}"
        response = requests.get(chunkurl, headers=headers).json()
        hits += response["hits"]["hits"]

    req = []
    for item in hits:
        req.append(item["id"])
    return req


def get_group_records(group_identifier, test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = f'?q=custom_fields.caltech%5C%3Agroups.id%3D"{group_identifier}"&sort=newest'

    url = url + query
    response = requests.get(url)
    total = response.json()["hits"]["total"]
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in range(1, pages + 1):
        chunkurl = f"{url}&size=1000&page={c}"
        response = requests.get(chunkurl).json()
        hits += response["hits"]["hits"]

    return hits


def get_series_records(series_name, test=False, token=None):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = f'?q=custom_fields.caltech%5C%3Aseries%3D"{series_name}"'

    if token:
        headers = {
            "Authorization": "Bearer %s" % token,
            "Content-type": "application/json",
        }

    url = url + query
    response = requests.get(url)
    total = response.json()["hits"]["total"]
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in range(1, pages + 1):
        chunkurl = f"{url}&size=1000&page={c}"
        response = requests.get(chunkurl).json()
        hits += response["hits"]["hits"]

    return hits


def get_restricted_records(token, test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = "?q=access.status:restricted"

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    url = url + query
    response = requests.get(url, headers=headers)
    total = response.json()["hits"]["total"]
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in range(1, pages + 1):
        chunkurl = f"{url}&size=1000&page={c}"
        response = requests.get(chunkurl, headers=headers).json()
        hits += response["hits"]["hits"]

    return hits


def get_records_from_date(date="2023-08-25", test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = f"?q=created:[{date} TO *]"

    url = url + query
    response = requests.get(url)
    total = response.json()["hits"]["total"]
    print(f"Found {total} Records")
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in range(1, pages + 1):
        chunkurl = f"{url}&size=1000&page={c}"
        response = requests.get(chunkurl).json()
        hits += response["hits"]["hits"]

    return hits


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
