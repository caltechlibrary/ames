import os
import csv
import requests
from ames.harvesters import (
    classify_link,
    extract_https_links,
    clean_link,
    extract_filename_from_link,
    is_file_present
)

base_url = "https://authors.library.caltech.edu/api/records?q=metadata.additional_descriptions.type.id%3A%22data-availability%22&size=25&sort=bestmatch"
base_file_url_template = "https://authors.library.caltech.edu/api/records/{record_id}/files"

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
    print(f"Error: Unable to fetch records from the API. Status code: {response.status_code}")
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

            results.append({
                "record_id": record_id,
                "original_link": link,
                "classification": classification,
                "cleaned_link": cleaned,
                "filename": filename,
                "file_present": file_present
            })

if results:
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Test results written to {output_file}")
else:
    print("No results to write.")
