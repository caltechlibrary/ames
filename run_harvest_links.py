import os
import csv
import json
import requests

from ames.matchers.caltechauthors import (
    get_record_metadata,
    update_related_identifiers,
    save_metadata_to_file,
    check_doi,
)


def main():
    input_file = "non_publisher_links.csv"
    output_file = "test_results_matchers.csv"

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


if __name__ == "__main__":
    main()
