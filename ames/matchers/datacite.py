from py_dataset import dataset
import requests
from datacite import DataCiteMDSClient, schema40
from datetime import date, datetime


def delete_datacite_media(username, password, doi):
    # Delete existing media entries in a datacite record
    url = "https://api.datacite.org/dois/" + doi + "/media"
    r = requests.get(url).json()
    for m in r["data"]:
        idv = m["id"]
        headers = {"Content-Type": "text/plain"}
        url = "https://mds.datacite.org/doi/" + doi + "/media/" + idv
        req = requests.delete(url, auth=(username, password), headers=headers)
        print(req)


def update_datacite_media(username, password, collection, prefix):
    keys = dataset.keys(collection)
    result = dataset.has_key(collection, "mediaupdate")
    today = date.today().isoformat()
    if result == True:
        update, err = dataset.read(collection, "mediaupdate")
        update = date.fromisoformat(update["mediaupdate"])
        dataset.update(collection, "mediaupdate", {"mediaupdate": today})
        keys.remove("mediaupdate")
    else:
        # Arbitrary old date - everything will be updated
        update = date(2011, 1, 1)
        dataset.create(collection, "mediaupdate", {"mediaupdate": today})
    for k in keys:
        print(k)
        existing, err = dataset.read(collection, k)
        if err != "":
            print(f"Unexpected error on read: {err}")
        record_update = datetime.fromisoformat(existing["updated"]).date()
        print(record_update)
        if record_update > update:
            if "electronic_location_and_access" in existing:
                doi = existing["identifier"]["identifier"]
                record_prefix = doi.split("/")[0]
                if record_prefix == prefix:
                    delete_datacite_media(username, password, doi)
                    for file_met in existing["electronic_location_and_access"]:
                        if file_met["electronic_name"][0].split(".")[-1] == "nc":
                            url = "https://mds.datacite.org/media/" + doi
                            data = (
                                "application/x-netcdf="
                                + file_met["uniform_resource_identifier"]
                            )
                            headers = {"Content-Type": "application/txt;charset=UTF-8"}
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

            record_doi = metadata["identifier"]["identifier"]

            if record_doi.split("/")[0] == prefix:
                result = schema40.validate(metadata)
                # Debugging if this fails
                if result == False:
                    v = schema40.validator.validate(metadata)
                    errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
                    for error in errors:
                        print(error.message)
                    exit()

                xml = schema40.tostring(metadata)

                response = d.metadata_post(xml)
                print(response)
