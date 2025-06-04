#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extended-logging version of tests/test_matchers.py
Adds prints so you can see where the flow dies.
"""

import os
import unittest
import csv
import random
import requests
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ames.matchers.caltechauthors import add_related_identifiers_from_csv

token = os.environ.get("RDMTOK")
CSV_FILE = "test.csv"

print(f"[debug] RDMTOK present? {'YES' if token else 'NO'} "
      f"(len={len(token) if token else 0})")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_test_data(from_csv=True):
    print(f"[loader] from_csv={from_csv}")
    if from_csv and os.path.exists(CSV_FILE):
        print(f"[loader] reading {CSV_FILE}")
        with open(CSV_FILE, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"[loader] loaded {len(rows)} rows")
            return rows
    else:
        dummy = {
            "CaltechAUTHORS_ID": "bwww3-z8y74",
            "CaltechAUTHORS_DOI": f"10.1093/mnras/staa{random.randint(1000, 9999)}",
            "Related_DOI": "10.22002/D1.1458",
            "Data_ID": "3hqgp-jhw61",
            "Cross_Link": "No",
            "Test_ID": "99s7k-d6f58",
            "resource_type": "publication-article",
        }
        print(f"[loader] generated 1 synthetic row -> DOI {dummy['CaltechAUTHORS_DOI']}")
        return [dummy]


def verify_related_identifiers_on_site(data_rows, test=True):
    base_url = (
        "https://data.caltechlibrary.dev"
        if test
        else "https://data.caltechlibrary.caltech.edu"
    )
    headers = {"Authorization": f"Bearer {token}"}
    results = []

    for row in data_rows:
        record_id = row["Test_ID"]
        doi = row["CaltechAUTHORS_DOI"]
        caltech_author_id = row["CaltechAUTHORS_ID"]
        author_url = f"https://authors.library.caltech.edu/records/{caltech_author_id}"

        url = f"{base_url}/api/records/{record_id}"
        print(f"[verify] GET {url}")
        r = requests.get(url, headers=headers)
        print(f"[verify] status={r.status_code}")
        if r.status_code != 200:
            print(f"❌ Could not fetch record {record_id}: {r.text[:300]}")
            results.append((record_id, False))
            continue

        metadata = r.json().get("metadata", {})
        related = metadata.get("related_identifiers", [])
        print(f"[verify] related_identifiers → {related}")

        found_doi = any(x["identifier"] == doi for x in related)
        found_author = any(x["identifier"] == author_url for x in related)

        if found_doi and found_author:
            print(f"✅ Verified: {record_id}")
            results.append((record_id, True))
        else:
            print(f"❌ Verification failed: {record_id} "
                  f"(doi={found_doi}, author={found_author})")
            results.append((record_id, False))

    return results


# ---------------------------------------------------------------------------
# Unit-test
# ---------------------------------------------------------------------------

class TestCaltechDataUploader(unittest.TestCase):

    def test_add_and_verify_related_identifiers(self):
        test_data = load_test_data(from_csv=False)  # flip flag to change source

        print("[test] calling add_related_identifiers_from_csv ...")
        upload_results = add_related_identifiers_from_csv(
            test_data, token, test=True
        )
        print(f"[test] upload_results → {upload_results}")

        for record_id, success in upload_results:
            print(f"[test] upload {record_id}: {'OK' if success else 'FAIL'}")
            self.assertTrue(success, f"❌ Upload failed for record {record_id}")

        print("[test] verifying on server ...")
        verify_results = verify_related_identifiers_on_site(test_data, test=True)
