#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import os
import random
import sys
import unittest

import requests

# Ensure the local project package is importable when the repo root is the CWD.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ames.matchers.caltechauthors import add_related_identifiers_from_csv  # noqa: E402

TOKEN = os.getenv("RDMTOK")
CSV_FILE = "test.csv"

print(f"[init] RDMTOK present: {'YES' if TOKEN else 'NO'} (len={len(TOKEN) if TOKEN else 0})")


def load_test_data(from_csv: bool = True):
    """Return rows for the upload function, from CSV when available."""
    if from_csv and os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="") as fh:
            return list(csv.DictReader(fh))

    doi_stub = random.randint(1000, 9999)
    return [
        {
            "CaltechAUTHORS_ID": "bwww3-z8y74",
            "CaltechAUTHORS_DOI": f"10.1093/mnras/staa{doi_stub}",
            "Related_DOI": "10.22002/D1.1458",
            "Data_ID": "3hqgp-jhw61",
            "Cross_Link": "No",
            "Test_ID": "99s7k-d6f58",
            "resource_type": "publication-article",
        }
    ]


def verify_related_identifiers_on_site(rows, *, test: bool = True):
    """Fetch each record and report which links are present or missing."""
    base = (
        "https://data.caltechlibrary.dev"
        if test
        else "https://data.caltechlibrary.caltech.edu"
    )
    headers = {"Authorization": f"Bearer {TOKEN}"}
    results = []

    for row in rows:
        record_id = row["Test_ID"]
        doi = row["CaltechAUTHORS_DOI"]
        author_link = f"https://authors.library.caltech.edu/records/{row['CaltechAUTHORS_ID']}"

        resp = requests.get(f"{base}/api/records/{record_id}", headers=headers)
        print(f"[verify] {record_id}: {resp.status_code}")
        if resp.status_code != 200:
            print("    Error: could not fetch record from server.")
            results.append((record_id, False))
            continue

        related = resp.json().get("metadata", {}).get("related_identifiers", [])
        has_doi = any(x["identifier"] == doi for x in related)
        has_author = any(x["identifier"] == author_link for x in related)

        status_parts = [
            "DOI link present" if has_doi else "DOI link missing",
            "CaltechAUTHORS link present" if has_author else "CaltechAUTHORS link missing",
        ]
        print("    " + "; ".join(status_parts))

        results.append((record_id, has_doi and has_author))

    return results


class TestCaltechDataUploader(unittest.TestCase):
    @unittest.skipUnless(TOKEN, "needs RDMTOK to hit CaltechDATA API")
    def test_add_and_verify_related_identifiers(self):
        rows = load_test_data(from_csv=False)

        uploads = add_related_identifiers_from_csv(rows, TOKEN, test=True)
        for record_id, ok in uploads:
            self.assertTrue(ok, f"upload failed for {record_id}")

        verifies = verify_related_identifiers_on_site(rows, test=True)
        for record_id, ok in verifies:
            self.assertTrue(ok, f"verification failed for {record_id}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
