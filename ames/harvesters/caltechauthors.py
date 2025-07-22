import requests, math
import os
import csv
import re

# base URLs
base_url = "https://authors.library.caltech.edu/api/records?q=metadata.additional_descriptions.type.id%3A%22data-availability%22&size=25&sort=bestmatch"
base_file_url_template = (
    "https://authors.library.caltech.edu/api/records/{record_id}/files"
)

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
    r"https://static-content.springer.com/esm/.*",
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
    "https://www.mdpi.com/": "publisher",
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
    link = link.split("<")[0].rstrip("/")
    return link


# function to extract the filename from the link
def extract_filename_from_link(link):
    return link.split("/")[-1]


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
        print(
            f"Error: Status code {response.status_code} received when checking files for record {record_id}."
        )
        return False

    try:
        data = response.json()
    except ValueError:
        print(f"Error: Unable to parse JSON response for record {record_id}.")
        return False

    files = data.get("entries", data.get("files", []))

    if not isinstance(files, list):
        print(
            f"Error: Unexpected structure for files in record {record_id}. Expected a list, got {type(files)}."
        )
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
        print(f"Error getting data for request {request}")
        exit()
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


def get_authors(token, record, test=False, draft=True):
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
    return response.json()["metadata"].get("creators")


def get_author_records(
    author_identifier, token=None, date=None, test=False, all_metadata=False
):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = f'?q=metadata.creators.person_or_org.identifiers.identifier%3A"{author_identifier}"'

    if date:
        query += f"%20AND%20metadata.publication_date%3A%5B{date}%20TO%20%2A%20%5D"

    if token:
        headers = {
            "Authorization": "Bearer %s" % token,
            "Content-type": "application/json",
        }
    else:
        headers = {
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

    if all_metadata:
        return hits
    else:
        req = []
        for item in hits:
            req.append(item["id"])
        return req


def get_group_records(group_identifier, test=False):
    if test:
        url = "https://authors.caltechlibrary.dev/api/records"
    else:
        url = "https://authors.library.caltech.edu/api/records"

    query = (
        f'?q=custom_fields.caltech%5C%3Agroups.id%3D"{group_identifier}"&sort=newest'
    )

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


def search_resource_type(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "resource_type" and isinstance(v, dict) and "id" in v:
                return v["id"]
            result = search_resource_type(v)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = search_resource_type(item)
            if result:
                return result
    return None


def fetch_resource_type(data):
    return search_resource_type(data) or "N/A"


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

        caltechauthors_doi = (
            metadata.get("pids", {}).get("doi", {}).get("identifier", "")
        )
        resource_type = fetch_resource_type(metadata)

        related_dois = []
        for identifier in metadata.get("metadata", {}).get("related_identifiers", []):
            if identifier.get("scheme") == "doi":
                doi = identifier["identifier"]
                if any(
                    doi.startswith(prefix)
                    for prefix in ["10.22002/", "10.14291/", "10.25989/"]
                ):
                    related_dois.append(doi)

        for doi in related_dois:
            caltechdata_url = doi2url(doi)
            if "data.caltech.edu/records/" in caltechdata_url:
                caltechdata_id = caltechdata_url.split("/records/")[-1]
                caltechdata_metadata = requests.get(
                    f"https://data.caltech.edu/api/records/{caltechdata_id}"
                ).json()

                cross_link = "No"
                for identifier in caltechdata_metadata.get("metadata", {}).get(
                    "related_identifiers", []
                ):
                    if identifier.get("identifier") == caltechauthors_doi:
                        cross_link = "Yes"
                        break

                citations.append(
                    {
                        "CaltechAUTHORS_ID": record_id,
                        "CaltechAUTHORS_DOI": caltechauthors_doi,
                        "Related_DOI": doi,
                        "CaltechDATA_ID": caltechdata_id,
                        "Cross_Link": cross_link,
                        "resource_type": resource_type,
                    }
                )
    return citations


def generate_data_citation_csv():
    prefixes = ["10.22002", "10.14291", "10.25989"]
    all_citations = []

    for prefix in prefixes:
        results = search_records(prefix)
        if results and "hits" in results:
            all_citations.extend(extract_data_citations(results["hits"]["hits"]))

    output_file = "data_citations_with_type.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "CaltechAUTHORS_ID",
                "CaltechAUTHORS_DOI",
                "Related_DOI",
                "CaltechDATA_ID",
                "Cross_Link",
                "resource_type",
            ]
        )
        for citation in all_citations:
            writer.writerow(
                [
                    citation["CaltechAUTHORS_ID"],
                    citation["CaltechAUTHORS_DOI"],
                    citation["Related_DOI"],
                    citation["CaltechDATA_ID"],
                    citation["Cross_Link"],
                    citation["resource_type"],
                ]
            )

    print(f"Saved {len(all_citations)} citations to {output_file}")


def get_data_availability_links(token=None, size=25):
    base_url = "https://authors.library.caltech.edu/api/records?q=metadata.additional_descriptions.type.id%3A%22data-availability%22&size=25&sort=bestmatch"
    base_file_url_template = (
        "https://authors.library.caltech.edu/api/records/{record_id}/files"
    )

    token = os.environ.get("RDMTOK")

    output_file = "test_results_harvesters.csv"

    headers = {}
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-type": "application/json",
        }

    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        print(
            f"Error: Unable to fetch records from the API. Status code: {response.status_code}"
        )
        exit()

    records = response.json().get("hits", {}).get("hits", [])

    if not records:
        print("No records found.")
        exit()

    results = []
    for record in records:
        record_id = record.get("id")
        links = record.get("metadata", {}).get("additional_descriptions", [])

        for link_data in links:
            description = link_data.get("description", "")
            links_in_description = extract_https_links(description)
            for link in links_in_description:
                classification = classify_link(link)
                cleaned = clean_link(link)
                filename = extract_filename_from_link(link)
                file_present = is_file_present(record_id, filename)

                results.append(
                    {
                        "record_id": record_id,
                        "original_link": link,
                        "classification": classification,
                        "cleaned_link": cleaned,
                        "filename": filename,
                        "file_present": file_present,
                    }
                )

    return results
