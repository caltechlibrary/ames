import os, shutil, datetime
import requests
from py_dataset import dataset


def get_crossref_refs(prefix, done=False, new=True):
    # New=True will download everything from scratch and delete any existing records

    collection = "crossref_refs.ds"

    if new == True:
        if os.path.exists(collection) == True:
            shutil.rmtree(collection)

    if os.path.isdir(collection) == False:
        if not dataset.init(collection):
            print("Dataset failed to init collection")
            exit()

    base_url = (
        "https://api.eventdata.crossref.org/v1/events?mailto=data@caltech.edu&source=crossref&obj-id.prefix="
        + prefix
    )

    collected = dataset.has_key(collection, "captured")

    cursor = ""
    count = 0
    while cursor != None:
        if collected == True:
            date, err = dataset.read(collection, "captured")
            if err != "":
                print("error on read: " + err)
            date = date["captured"]
            print(date)
            url = base_url + "&from-collected-date=" + date
        else:
            url = base_url
        if cursor != "":
            url = url + "&cursor=" + cursor
        print(url)
        r = requests.get(url)
        records = r.json()
        if records["status"] == "failed":
            print(records)
            break
        for rec in records["message"]["events"]:
            # Save results in dataset
            print(count, rec["id"])
            count = count + 1  # Just for prettyness
            if not dataset.create(collection, rec["id"], rec):
                err = dataset.error_message()
                print("Error in saving record: " + err)

        if cursor == records["message"]["next-cursor"]:
            # Catches bug where we get the same curser back at end of results
            break
        if records["message"]["total-results"] > count:
            cursor = records["message"]["next-cursor"]
        else:
            cursor = None

    if collected == True:
        date, err = dataset.read(collection, "captured")
        if err != "":
            print("Error in reading date: " + err)
        date = date["captured"]

        # Check Deleted
        cursor = ""
        while cursor != None:
            del_url = "https://api.eventdata.crossref.org/v1/events/deleted?mailto=data@caltech.edu&source=crossref"
            full = del_url + "&from-collected-date=" + date + "&cursor=" + cursor
            r = requests.get(full)
            records = r.json()
            for rec in records["message"]["events"]:
                # Delete results in dataset
                print("Deleted: ", rec["id"])
                if not dataset.delete(collection, rec["id"]):
                    err = dataset.error_message()
                    print(f"Unexpected error on read: {err}")
            cursor = records["message"]["next-cursor"]

        # Check Edited
        cursor = ""
        while cursor != None:
            del_url = "https://api.eventdata.crossref.org/v1/events/edited?mailto=data@caltech.edu&source=crossref"
            full = del_url + "&from-collected-date=" + date + "&cursor=" + cursor
            r = requests.get(full)
            records = r.json()
            for rec in records["message"]["events"]:
                # Update results in dataset
                print("Update: ", rec["id"])
                if not dataset.update(collection, rec["id"], rec):
                    err = dataset.error_message()
                    print(f"Unexpected error on write: {err}")
            cursor = records["message"]["next-cursor"]

    if done:
        date = datetime.date.today().isoformat()
        record = {"captured": date}
        if dataset.has_key(collection, "captured"):
            if not dataset.update(collection, "captured", record):
                err = dataset.error_message()
                print(f"Unexpected error on update: {err}")
        else:
            if not dataset.create(collection, "captured", record):
                err = dataset.error_message()
                print(f"Unexpected error on create: {err}")
