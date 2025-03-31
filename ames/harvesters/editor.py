import csv
import json
import requests
from caltechdata_edit import caltechdata_edit

# Read the CSV file
records = []
with open('output.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        records.append(row)

# Access token for authentication
token = "moaclkv2MHDHoGklIZs7ABF5mmBZNcxKGgmHY4yyHaUAGbCuyO3DNXhehpL7"

# Using the development system (production=False)
production = False
base_url = "https://data.caltechlibrary.dev"

# Set up headers for API requests
headers = {
    "Authorization": f"Bearer {token}",
    "Content-type": "application/json",
}

def add_related_identifier(record_id, doi, caltech_author_id):
    """Add DOI and CaltechAUTHORS_ID to related identifiers directly using the API"""
    print(f"Processing Test_ID: {record_id} with DOI: {doi} and CaltechAUTHORS_ID: {caltech_author_id}")
    
    # First, get the current record
    response = requests.get(f"{base_url}/api/records/{record_id}", headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching record {record_id}: {response.status_code}")
        print(response.text)
        return False
    
    record_data = response.json()
    
    # Check if there's already a draft
    draft_response = requests.get(f"{base_url}/api/records/{record_id}/draft", headers=headers)
    
    if draft_response.status_code == 200:
        # Use the draft if it exists
        record_data = draft_response.json()
    else:
        # Create a draft if it doesn't exist
        draft_create_response = requests.post(
            f"{base_url}/api/records/{record_id}/draft", 
            headers=headers
        )
        
        if draft_create_response.status_code != 201:
            print(f"Error creating draft for {record_id}: {draft_create_response.status_code}")
            print(draft_create_response.text)
            return False
        
        record_data = draft_create_response.json()
    
    # Update the related identifiers
    related_identifiers = record_data.get("metadata", {}).get("related_identifiers", [])
    if related_identifiers is None:
        related_identifiers = []
    
    # Check if DOI already exists
    doi_exists = any(identifier.get("identifier") == doi for identifier in related_identifiers)
    
    # Check if CaltechAUTHORS_ID URL already exists
    author_url = f"https://authors.library.caltech.edu/records/{caltech_author_id}"
    author_url_exists = any(identifier.get("identifier") == author_url for identifier in related_identifiers)
    
    # Add the DOI if it doesn't exist
    if not doi_exists:
        new_doi_identifier = {
            "relation_type": {"id": "issupplementedby"},
            "identifier": doi,
            "scheme": "doi",
            "resource_type": {"id": "publication"}
        }
        related_identifiers.append(new_doi_identifier)
        print(f"Adding DOI related identifier: {doi}")
    else:
        print(f"DOI {doi} already exists in related identifiers")
    
    # Add the CaltechAUTHORS_ID URL if it doesn't exist
    if not author_url_exists:
        new_author_identifier = {
            "relation_type": {"id": "isreferencedby"},
            "identifier": author_url,
            "scheme": "url",
            "resource_type": {"id": "publication"}
        }
        related_identifiers.append(new_author_identifier)
        print(f"Adding CaltechAUTHORS_ID related identifier: {author_url}")
    else:
        print(f"CaltechAUTHORS_ID URL {author_url} already exists in related identifiers")
    
    record_data["metadata"]["related_identifiers"] = related_identifiers
    
    # Update the draft
    update_response = requests.put(
        f"{base_url}/api/records/{record_id}/draft",
        headers=headers,
        json=record_data
    )
    
    if update_response.status_code != 200:
        print(f"Error updating draft for {record_id}: {update_response.status_code}")
        print(update_response.text)
        return False
    
    # Publish the draft
    publish_response = requests.post(
        f"{base_url}/api/records/{record_id}/draft/actions/publish",
        headers=headers
    )
    
    if publish_response.status_code != 202:
        print(f"Error publishing draft for {record_id}: {publish_response.status_code}")
        print(publish_response.text)
        return False
    
    print(f"Successfully added related identifier {doi} to {record_id} and published the changes")
    return True

# Process each record
for record in records:
    test_id = record['Test_ID']
    doi = record['CaltechAUTHORS_DOI']
    caltech_author_id = record['CaltechAUTHORS_ID']
    add_related_identifier(test_id, doi, caltech_author_id)

print("Processing complete")