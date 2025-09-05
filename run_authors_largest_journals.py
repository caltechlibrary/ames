import csv
from ames.harvesters import get_records_pub_date


years = [2021, 2022, 2023, 2024, 2025]

journals = {}

for year in years:

    records = get_records_pub_date(f"{year}-01-01", f"{year}-12-31")

    for record in records:
        custom_fields = record.get("custom_fields")
        if "journal:journal" in custom_fields:
            journal = custom_fields["journal:journal"].get("title")
            if journal not in journals:
                journals[journal] = {
                    "count": 1,
                    "publisher": record["metadata"].get("publisher"),
                }
            else:
                journals[journal]["count"] += 1


# Write the results to a CSV file
with open("authors_publication_report.csv", "w", newline="") as csvfile:
    fieldnames = ["Journal", "Publisher", "Count"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for journal, data in journals.items():
        writer.writerow(
            {"Journal": journal, "Count": data["count"], "Publisher": data["publisher"]}
        )
