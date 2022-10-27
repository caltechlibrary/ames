import os, subprocess, shutil, math
import requests
from py_dataset import dataset
from progressbar import progressbar
from datetime import date, datetime
from caltechdata_api import get_metadata

def get_caltechdata(collection, production=True, full=False):
    """Harvest all records from CaltechDATA .
    Always creates collection from scratch"""
    # Delete existing collection
    if os.path.isdir(collection):
        shutil.rmtree(collection)
    if not dataset.init(collection):
        print("Dataset failed to init collection")
        exit()

    if production == True:
        url = "https://data.caltech.edu/api/records"
    else:
        url = "https://data.caltechlibrary.dev/api/records"

    #if datacite == True:
    #    headers = {
    #        "accept": "application/vnd.datacite.datacite+json",
    #    }

    if full == True:
        query = '?&sort=newest'
    else:
        #Exclude HTE for efficiency
        query ='?q=-metadata.related_identifiers.identifier%3A"10.25989%2Fes8t-kswe"&sort=newest'

    response = requests.get(f"{url}{query}").json()
    total = 0
    if ("hits" in response) and ("total" in response):
        total = response["hits"]["total"]
    pages = math.ceil(int(total) / 1000)
    hits = []
    for c in progressbar(range(1, pages + 1)):
        chunkurl = (
            f"{url}{query}&size=1000&page={c}"
        )
        response = requests.get(chunkurl).json()
        if ("hits" in response) and ("hits" in response["hits"]):
            hits += response["hits"]["hits"]

    for h in progressbar(hits):
        rid = str(h["id"])
        metadata = get_metadata(rid,production, validate=False)
        if not dataset.create(collection, rid, metadata):
            err = dataset.error_message()
            print(err)



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

            print('NOT IMPLEMENTED')


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
