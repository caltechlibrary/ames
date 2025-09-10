import os, subprocess, shutil, math
import requests
from py_dataset import dataset
from progressbar import progressbar
from datetime import date, datetime
from caltechdata_api import get_metadata


def get_caltechdata(
    query=None, production=True, full=False, token=False, date=None, datacite=True
):
    """Harvest all records from CaltechDATA"""

    if production == True:
        url = "https://data.caltech.edu/api/records"
    else:
        url = "https://data.caltechlibrary.dev/api/records"

    if query:
        if date:
            query_string = f"?q={query}+AND+updated:[{date}+TO+*]"
        else:
            query_string = f"?q={query}"
    else:
        if full:
            query_string = "?&sort=newest"
        elif date:
            # Exclude HTE and tomograms for efficiency
            query_string = f'?q=updated:[{date} TO *]-metadata.related_identifiers.identifier%3A"10.25989%2Fes8t-kswe"-metadata.identifiers.scheme%3Atiltid&sort=newest'
        else:
            # Exclude HTE and tomograms for efficiency
            query_string = 'q=-metadata.related_identifiers.identifier%3A"10.25989%2Fes8t-kswe"-metadata.identifiers.scheme%3Atiltid&sort=newest'

    response = requests.get(f"{url}{query_string}")
    print(f"{url}{query_string}")
    total = response.json()["hits"]["total"]
    pages = math.ceil(int(total) / 1000)
    hits = []
    records = []
    print("Total records " + str(total))
    for c in progressbar(range(1, pages + 1)):
        chunkurl = f"{url}{query_string}&size=1000&page={c}"
        response = requests.get(chunkurl).json()
        hits += response["hits"]["hits"]

    if datacite:
        for h in progressbar(hits):
            rid = h["id"]
            metadata = get_metadata(rid, production, validate=False, token=token)
            metadata["id"] = rid
            records.append(metadata)

        return records
    else:
        return hits


def get_caltechdata_files(record, production=True, token=False):
    """Get files from CaltechDATA."""

    if production == True:
        url = "https://data.caltech.edu/api/records"
    else:
        url = "https://data.caltechlibrary.dev/api/records"

    rid = str(record["id"])
    files = {"files": []}
    # Capture external files:
    metadata = record["metadata"]
    if "additional_descriptions" in metadata:
        for desc in metadata["additional_descriptions"]:
            if "type" in desc and desc["type"]["id"] == "files":
                description = desc["description"]
                chunks = description.split('href="')[1:]
                for c in chunks:
                    files["files"].append({"url": c.split('"')[0]})

    if token:
        headers = {
            "Authorization": "Bearer %s" % token,
            "Content-type": "application/json",
        }
    else:
        headers = {
            "Content-type": "application/json",
        }

    response = requests.get(f"{url}/{rid}/files", headers=headers)
    if response.status_code == 200:
        if "entries" in response.json():
            files["files"] += response.json()["entries"]

    return files


def get_cd_github(new=True):
    collection = "github_records.ds"

    if new == True:
        os.system("rm -rf " + collection)

    if os.path.isdir(collection) == False:
        if not dataset.init(collection):
            print("Dataset failed to init collection")
            exit()

    url = "https://data.caltech.edu/api/records"

    response = requests.get(url + "?size=1000&q=metadata.subjects.subject%3A'GitHub'")
    hits = response.json()

    for h in hits["hits"]["hits"]:
        rid = str(h["id"])
        record = h["metadata"]

        result = dataset.has_key(collection, rid)

        if result == False:
            dataset.create(collection, rid, record)

            print("Downloading files for ", rid)

            codemeta = False

            print("NOT IMPLEMENTED")

            for erecord in record["electronic_location_and_access"]:
                f = download_file(erecord, rid)

                # We're just looking for the zip file
                if f.split(".")[-1] == "zip":
                    zip_files = subprocess.check_output(
                        ["unzip", "-l", f.rstrip()], universal_newlines=True
                    ).splitlines()
                    i = 4  # Ignore header
                    line = zip_files[i]
                    while line[0] != "-":
                        split = line.split("/")
                        fname = split[1]
                        if fname == "codemeta.json":
                            sp = line.split("   ")[-1]
                            os.system("unzip -j " + f.rstrip() + " " + sp + " -d .")
                            codemeta = True
                        i = i + 1
                        line = zip_files[i]
                        # Will only identify codemeta files in root of repo

                # Trash downloaded files - extracted codemeta.json not impacted
                print("Trash " + f)
                os.system("rm " + f)

            if codemeta == True:
                print(collection, rid)
                response = dataset.attach(collection, rid, ["codemeta.json"])
                print("Attachment ", response)
                os.system("rm codemeta.json")
                print("Trash codemeta.json")
