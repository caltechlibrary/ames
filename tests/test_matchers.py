import os
import unittest
import csv
import random
import requests
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ames.matchers.caltechauthors import add_related_identifiers_from_csv

token = "0UrVehnBSM9c7DQZZCM2EtB4lpuEwbTiLue6rf0Vme3lnzswlMA9whjJbmhX"
CSV_FILE = "test.csv"

def load_test_data(from_csv=True):
    if from_csv and os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        return [{
            "CaltechAUTHORS_ID": "bwww3-z8y74",
            "CaltechAUTHORS_DOI": f"10.1093/mnras/staa{random.randint(1000, 9999)}",
            "Related_DOI": "10.22002/D1.1458",
            "Data_ID": "3hqgp-jhw61",
            "Cross_Link": "No",
            "Test_ID": "99s7k-d6f58",
            "resource_type": "publication-article"
        }]

def verify_related_identifiers_on_site(data_rows, test=False):
    base_url = "https://data.caltechlibrary.dev" if test else "https://data.caltechlibrary.caltech.edu"
    headers = {"Authorization": f"Bearer {token}"}
    results = []

    for row in data_rows:
        record_id = row['Test_ID']
        doi = row['CaltechAUTHORS_DOI']
        caltech_author_id = row['CaltechAUTHORS_ID']
        author_url = f"https://authors.library.caltech.edu/records/{caltech_author_id}"

        r = requests.get(f"{base_url}/api/records/{record_id}", headers=headers)
        if r.status_code != 200:
            print(f"❌ Could not fetch record {record_id}")
            results.append((record_id, False))
            continue

        metadata = r.json().get("metadata", {})
        related = metadata.get("related_identifiers", [])
        found_doi = any(x["identifier"] == doi for x in related)
        found_author = any(x["identifier"] == author_url for x in related)

        if found_doi and found_author:
            print(f"✅ Verified: {record_id}")
            results.append((record_id, True))
        else:
            print(f"❌ Verification failed: {record_id}")
            results.append((record_id, False))

    return results

class TestCaltechDataUploader(unittest.TestCase):

    def test_add_and_verify_related_identifiers(self):
        test_data = load_test_data(from_csv=False)  # <-- change this flag to toggle source
        upload_results = add_related_identifiers_from_csv(test_data, token, test=True)
        for record_id, success in upload_results:
            self.assertTrue(success, f"❌ Upload failed for record {record_id}")

        verify_results = verify_related_identifiers_on_site(test_data, test=True)
        for record_id, success in verify_results:
            self.assertTrue(success, f"❌ Verification failed for record {record_id}")


if __name__ == "__main__":
    unittest.main()
