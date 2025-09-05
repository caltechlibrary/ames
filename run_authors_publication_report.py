import csv
from ames.harvesters import get_records_pub_date

query = 'metadata.publisher:"American Chemical Society"'

records = get_records_pub_date(f"2022-01-01", f"2025-12-31", query=query)

with open("authors_publication_report.csv", "w", newline="") as csvfile:
    fieldnames = [
        "Authors ID",
        "DOI",
        "Pub Date",
        "Journal",
        "NSF Funded",
        "NIH Funded",
        "Groups",
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for record in records:
        idv = record.get("id")
        custom_fields = record.get("custom_fields")
        if "journal:journal" in custom_fields:
            journal = custom_fields["journal:journal"].get("title")
        else:
            journal = "Unknown Journal"
        groups = []
        if "caltech:groups" in custom_fields:
            listv = custom_fields["caltech:groups"]
            for group in listv:
                groups.append(group["title"]["en"])
        pids = record.get("pids", {})
        if "doi" in pids:
            doi = record["pids"]["doi"]["identifier"]
        else:
            doi = "No DOI"
            identifiers = record["metadata"].get("identifiers", [])
            for identifier in identifiers:
                if identifier.get("scheme", "") == "doi":
                    doi = identifier.get("identifier")
        date = record["metadata"].get("publication_date", "No Pub Date")
        funding = record["metadata"].get("funding", [])
        nsf = False
        nih = False
        for fund in funding:
            funder = fund.get("funder", {})
            if "021nxhr62" in funder.get("id", ""):
                nsf = True
            elif "NSF" in funder.get("name", ""):
                nsf = True
            elif "National Science Foundation" in funder.get("name", ""):
                nsf = True
            if "01cwqze88" in funder.get("id", ""):
                nih = True
            elif "NIH" in funder.get("name", ""):
                nih = True
            elif "National Institutes of Health" in funder.get("name", ""):
                nih = True

        writer.writerow(
            {
                "Authors ID": idv,
                "DOI": doi,
                "Pub Date": date,
                "Journal": journal,
                "NSF Funded": nsf,
                "NIH Funded": nih,
                "Groups": "; ".join(groups),
            }
        )
