from py_dataset import dataset
import requests
from os import path
from progressbar import progressbar
from datacite import DataCiteMDSClient, schema40
from datetime import date, datetime, timedelta


def delete_datacite_media(username, password, doi):
    # Delete existing media entries in a datacite record
    url = "https://api.datacite.org/dois/" + doi + "/media"
    r = requests.get(url).json()
    if "data" in r:
        for m in r["data"]:
            idv = m["id"]
            headers = {"Content-Type": "text/plain"}
            url = "https://mds.datacite.org/doi/" + doi + "/media/" + idv
            req = requests.delete(url, auth=(username, password), headers=headers)
            print(req)


def update_datacite_media(username, password, collection, collection_files, prefix):
    keys = dataset.keys(collection)

    for k in progressbar(keys, redirect_stdout=True):
        existing, err = dataset.read(collection, k)
        if err != "":
            print(f"Unexpected error on read: {err}")
        atlas = False
        tccon = False
        if "subjects" in existing:
            subjects = existing["subjects"]
            for subject in subjects:
                if (
                    subject["subject"].strip()
                    == "Atlas of Bacterial and Archaeal Cell Structure"
                ):
                    atlas = True
                if subject["subject"].strip() == "TCCON":
                    tccon = True

        files, err = dataset.read(collection_files, k)
        if err == "":
            for idv in existing["identifiers"]:
                if idv["identifierType"] == "DOI":
                    doi = idv["identifier"]
            record_prefix = doi.split("/")[0]
            if record_prefix == prefix:
                delete_datacite_media(username, password, doi)
                for file_met in files["files"]:
                    url = "https://mds.datacite.org/media/" + doi
                    headers = {"Content-Type": "application/txt;charset=UTF-8"}
                    data = {}
                    if "url" in file_met:
                        # We're dealing with an external file
                        file_url = file_met["url"]
                        extension = file_url.split(".")[-1]
                    else:
                        # We have an internal CaltechDATA file
                        extension = file_met["key"].split(".")[-1]
                        base_link = file_met["links"]["self"]
                        file_url = base_link.replace("/api", "")
                    if extension == "nc":
                        data = "application/x-netcdf=" + file_url
                    if extension == "txt":
                        data = "text/plain=" + file_url
                    elif extension == "mp4":
                        if atlas:
                            data = (
                                "video/mp4="
                                + "https://www.cellstructureatlas.org/videos/"
                                + file_met["key"]
                            )
                        else:
                            data = "video/mp4=" + file_url
                    elif extension == "mj2":
                        data = "video/mj2=" + file_url
                    elif extension == "avi":
                        data = "video/avi=" + file_url
                    elif extension == "mov":
                        data = "video/quicktime=" + file_url
                    elif extension == "gz":
                        data = "application/gzip=" + file_url
                    elif extension == "zip":
                        data = "application/zip=" + file_url
                    elif extension == "h5ad":
                        data = "application/octet-stream=" + file_url
                    if data != {}:
                        print(doi)
                        print(data)
                        r = requests.post(
                            url,
                            data=data.encode("utf-8"),
                            auth=(username, password),
                            headers=headers,
                        )
                        print(r)


def update_datacite_metadata(collection, token, access):
    """Access contains username, password, and prefix for DataCite"""
    keys = dataset.keys(collection)
    for a in access:
        username = a["username"]
        password = a["password"]
        prefix = a["prefix"]

        # Initialize the MDS client.
        d = DataCiteMDSClient(
            username=username,
            password=password,
            prefix=prefix,
            url="https://mds.datacite.org",
        )

        for k in keys:
            print(k)
            metadata, err = dataset.read(collection, k)
            if err != "":
                print(err)
                exit()
            # Get rid of Key from dataset
            metadata.pop("_Key")

            if "identifier" in metadata:
                record_doi = metadata["identifier"]["identifier"]

                # Handle records with 4.3 metadata elements
                if "schemaVersion" in metadata:
                    metadata.pop("schemaVersion")
                if "types" in metadata:
                    metadata.pop("types")

                if record_doi.split("/")[0] == prefix:
                    result = schema40.validate(metadata)
                    # Debugging if this fails
                    if result == False:
                        print(metadata)
                        v = schema40.validator.validate(metadata)
                        errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
                        for error in errors:
                            print(error.message)
                        exit()

                    xml = schema40.tostring(metadata)

                    response = d.metadata_post(xml)
                    print(response)


def submit_report(
    month_collection, keys, token, production, prefix=None, org="Caltech_Library"
):
    for k in keys:
        datasets, err = dataset.read(month_collection, k, clean_object=True)
        if err != "":
            print(err)
        datasets = datasets["report-datasets"]
        dates = datasets[0]["performance"][0]["period"]
        if prefix != None:
            filtered = []
            for d in datasets:
                rec_prefix = d["dataset-id"][0]["value"].split("/")[0]
                if rec_prefix in prefix:
                    filtered.append(d)
            datasets = filtered
        # Build report structure
        today = date.today().isoformat()
        report = {
            "report-header": {
                "report-name": "dataset report",
                "report-id": "DSR",
                "release": "rd1",
                "report-filters": [],
                "report-attributes": [],
                "exceptions": [],
                "created-by": org,
                "created": today,
                "reporting-period": {
                    "begin-date": dates["begin-date"],
                    "end-date": dates["end-date"],
                },
            },
            "report-datasets": datasets,
        }
        if production:
            url = "https://api.datacite.org/reports/"
        else:
            url = "https://api.test.datacite.org/reports/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer %s" % token,
        }
        r = requests.post(url, headers=headers, json=report)
        if r.status_code != 201:
            print(r.text)
            print(report)
        else:
            print(r.json()["report"]["id"])
