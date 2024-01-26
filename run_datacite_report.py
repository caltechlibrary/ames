import os, argparse, csv, json
import random
import requests
from progressbar import progressbar
from ames.harvesters import get_datacite_dois


def prefix_report(file_obj, prefix):
    file_obj.writerow(["DOI", "Title", "Year", "URL"])
    data = get_datacite_dois(prefix)["data"]
    for doi in data:
        doi = doi["attributes"]
        file_obj.writerow(
            [doi["doi"], doi["titles"][0]["title"], doi["publicationYear"], doi["url"]]
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a report of DataCite DOIs")
    parser.add_argument(
        "-report_name",
        default="prefix_report",
        help="report name (options: prefix_report)",
    )
    parser.add_argument("-prefix", help="Prefix of interest")
    parser.add_argument("output", help="output csv name")

    args = parser.parse_args()

    with open(args.output, "w", newline="\n", encoding="utf-8") as fout:
        file_out = csv.writer(fout)
        if args.report_name == "prefix_report":
            prefix_report(file_out, args.prefix)
