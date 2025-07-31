import argparse, csv
from ames.harvesters import get_author_records

parser = argparse.ArgumentParser(
    prog="authors_name_report",
    description="Generate a report for a name identifier",
)

parser.add_argument("name_identifier", type=str, help="The name identifier")

args = parser.parse_args()
name_identifier = args.name_identifier
outfile = f"{name_identifier}_report.csv"
with open(outfile, "w", newline="") as csvfile:
    fieldnames = [
        "record_id",
        "DOI",
        "pub_date",
        "title",
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    records = get_author_records(args.name_identifier, all_metadata=True)
    for record in records:
        date = record["metadata"].get("publication_date")
        doi = record["pids"].get("doi")
        if doi:
            doi = doi["identifier"]
        else:
            identifiers = record["metadata"].get("identifiers", [])
            for identifier in identifiers:
                if identifier["scheme"] == "doi":
                    doi = identifier["identifier"]
                    break
        writer.writerow(
            {
                "record_id": record["id"],
                "DOI": doi,
                "pub_date": date,
                "title": record["metadata"]["title"],
            }
        )
