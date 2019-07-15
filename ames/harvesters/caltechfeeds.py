import os, csv, shutil
import requests
from progressbar import progressbar
from datetime import datetime
from py_dataset import dataset
import zipfile


def download_file(url, fname):
    r = requests.get(url + fname, stream=True)
    if r.status_code == 403:
        print("403: File not available.")
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


def get_records(dot_paths, f_name, d_name, keys, labels=None):
    if dataset.has_frame(d_name, f_name):
        dataset.delete_frame(d_name, f_name)
    if labels:
        f, err = dataset.frame(d_name, f_name, keys, dot_paths, labels)
        if err != "":
            print(f"ERROR: Can't create {f_name} in {d_name}, {err}")
    else:
        # If labels arn't provided, just base on dot path
        labels = []
        for d in dot_paths:
            labels.append(d.split(".")[-1])
        f, err = dataset.frame(d_name, f_name, keys, dot_paths, labels)
        if err != "":
            print(f"ERROR: Can't create {f_name} in {d_name}, {err}")
    return dataset.frame_objects(d_name, f_name)


def get_caltechfeed(feed, autoupdate=False):

    url = "https://feeds.library.caltech.edu/" + feed + "/"

    if feed == "authors":
        fname = "CaltechAUTHORS.ds.zip"
        cname = "CaltechAUTHORS.ds"
    elif feed == "thesis":
        fname = "CaltechTHESIS.ds.zip"
        cname = "CaltechTHESIS.ds"
    elif feed == "caltechdata":
        fname = "CaltechDATA.ds.zip"
        cname = "CaltechDATA.ds"
    else:
        raise Exception("Feed {} is not known".format(feed))

    if os.path.isdir(cname) == False:
        # Collection doesn't exist
        print("Downloading " + feed + " Metdata")
        download_file(url, fname)
        print("Extracting " + feed + " Metdata")
        with zipfile.ZipFile(fname, "r") as zip_ref:
            zip_ref.extractall(".")
        os.remove(fname)
    else:
        # We decide whether to update
        datev, err = dataset.read(cname, "captured")
        if err != "":
            print(err)
            exit()
        if datev == {}:
            # No date, collection must be updated
            update = "Y"
        else:
            captured_date = datetime.fromisoformat(datev["captured"])
            print(
                "Local Collection "
                + feed
                + " last updated on "
                + captured_date.isoformat()
            )

            upname = "updated.csv"
            download_file(url, upname)
            with open(upname) as csv_file:
                reader = csv.reader(csv_file, delimiter=",")
                # Drop header
                next(reader)
                record_date = datetime.fromisoformat(next(reader)[1]).replace(
                    tzinfo=None
                )
                count = 0
                while captured_date < record_date:
                    count = count + 1
                    record_date = datetime.fromisoformat(next(reader)[1]).replace(
                        tzinfo=None
                    )
            if count > 0:
                print(str(count) + " Outdated Records")
                if autoupdate == False:
                    update = input("Do you want to update your local copy (Y or N)? ")
                else:
                    update = "Y"
            else:
                print("Collection up to date")
                update = "N"

        if update == "Y":
            shutil.rmtree(cname)
            print("Downloading " + feed + " Metdata")
            download_file(url, fname)
            print("Extracting " + feed + " Metdata")
            with zipfile.ZipFile(fname, "r") as zip_ref:
                zip_ref.extractall(".")
            os.remove(fname)
    return cname
