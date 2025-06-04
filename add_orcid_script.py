import csv, os

with open("orcids.csv", "r") as f:
    reader = csv.reader(f)
    orcid_list = list(reader)
    for orcid_data in orcid_list:
        orcid = orcid_data[8]
        clpid = orcid_data[10]
        os.system(
            f"python run_authors_name_update.py {clpid} {orcid} -add -new-scheme orcid"
        )
