import os, subprocess, shutil
import requests
from caltechdata_api import decustomize_schema
from py_dataset import dataset
from progressbar import progressbar


def get_caltechdata(collection, production=True, datacite=False):
    """Harvest all records from CaltechDATA .
    Always creates collection from scratch"""
    # Delete existing collection
    if os.path.isdir(collection):
        shutil.rmtree(collection)
    ok = dataset.init(collection)
    if ok == False:
        print("Dataset failed to init collection")
        exit()

    if production == True:
        url = "https://data.caltech.edu/api/records"
    else:
        url = "https://cd-sandbox.tind.io/api/records"

    response = requests.get(url + "/?size=5000")
    hits = response.json()

    for h in progressbar(hits["hits"]["hits"]):
        rid = str(h["id"])
        # Get enriched metadata records (including files)
        if datacite == False:
            metadata = decustomize_schema(h["metadata"], True, True, True)
            metadata["updated"] = h["updated"]
        else:
            # Get just DataCite metadata
            metadata = decustomize_schema(h["metadata"])

        dataset.create(collection, rid, metadata)


def get_history(collection, keys):
    """Harvest the history of records from CaltechDATA .
    Always creates collection from scratch"""
    # Delete existing collection
    if os.path.isdir(collection):
        shutil.rmtree(collection)
    ok = dataset.init(collection)
    if ok == False:
        print("Dataset failed to init collection")
        exit()

    base_url = "https://data.caltech.edu/records/"

    for k in progressbar(keys):
        url = base_url + str(k) + "/revisions"
        response = requests.get(url)
        revisions = response.json()
        for num, metadata in enumerate(revisions):
            dataset.create(collection, str(k) + "-" + str(num), metadata)


def get_multiple_links(input_collection, output_collection):
    keys = dataset.keys(input_collection)
    for k in keys:
        record, err = dataset.read(input_collection, k)
        if err != "":
            print(err)
            exit()
        if "relatedIdentifiers" in record:
            idvs = []
            for idv in record["relatedIdentifiers"]:
                idvs.append(idv["relatedIdentifier"])
            for idv in record["relatedIdentifiers"]:
                count = idvs.count(idv["relatedIdentifier"])
                if count > 1:
                    print("DUPE")
                    print(k)
                    print(idv["relatedIdentifier"])


def download_file(erecord, rid):
    r = requests.get(erecord["uniform_resource_identifier"], stream=True)
    fname = erecord["electronic_name"][0]
    if r.status_code == 403:
        print(
            "It looks like this file is embargoed.  We can't access until after the embargo is lifted"
        )
    else:
        with open(fname, "wb") as f:
            total_length = int(r.headers.get("content-length"))
            for chunk in progressbar(
                r.iter_content(chunk_size=1024), max_value=(total_length / 1024) + 1
            ):
                if chunk:
                    f.write(chunk)
                    # f.flush()
        return fname


def get_cd_github(new=True):

    collection = "github_records.ds"

    if new == True:
        os.system("rm -rf " + collection)

    if os.path.isdir(collection) == False:
        ok = dataset.init(collection)
        if ok == False:
            print("Dataset failed to init collection")
            exit()

    url = "https://data.caltech.edu/api/records"

    response = requests.get(url + "/?size=1000&q=subjects:GitHub")
    hits = response.json()

    for h in hits["hits"]["hits"]:
        rid = str(h["id"])
        record = h["metadata"]

        result = dataset.has_key(collection, rid)

        if result == False:

            dataset.create(collection, rid, record)

            print("Downloading files for ", rid)

            codemeta = False

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
