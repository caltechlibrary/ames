import os, json
from caltechdata_api import caltechdata_edit, get_metadata
from ames import codemeta_to_datacite
from ames.harvesters import get_records
from progressbar import progressbar
from datetime import datetime
import idutils
from py_dataset import dataset
import pandas as pd
import numpy as np
import requests


def edit_subject(record, token, correction_subjects, test=True):
    if test:
        rurl = "https://data.caltechlibrary.dev/api/records/" + record
    else:
        rurl = "https://data.caltechlibrary.dev/api/records/" + record

    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-type": "application/json",
    }

    metadata = get_metadata(
        record,
        production=not test,
    )

    new_subjects = []

    for subject_entry in metadata["subjects"]:   
        
        for correct_subject in correction_subjects.keys():
            if subject_entry["subject"] == correct_subject and "id" not in subject_entry:
                subject_entry["id"] = correction_subjects[correct_subject]
                subject_entry["subject"] = correct_subject
        
        new_subjects.append(subject_entry)

    metadata["subjects"] = new_subjects
    
    print(metadata["subjects"])

    caltechdata_edit(
        record,
        metadata=metadata,
        token=token,
        production=not test,
        publish=True,
    )

    record_metadata = get_metadata(
        record,
        production=False,
        validate=True,
        emails=False,
        schema="43",
        token=False,
        authors=False,
    )

    return record_metadata


def match_cd_refs():
    token = os.environ["RDMTOK"]

    matches = []
    collection = "caltechdata.ds"
    keys = dataset.keys(collection)
    if "mediaupdate" in keys:
        keys.remove("mediaupdate")

    # Get event data results
    event_data = "crossref_refs.ds"
    event_keys = dataset.keys(event_data)
    event_keys.remove("captured")
    f_name = "match_cd_refs"
    dot_paths = [".obj_id", ".id", ".subj_id"]
    labels = ["obj_id", "id", "subj_id"]
    print("Getting Event Data Records")
    if dataset.has_frame(event_data, f_name):
        if not dataset.frame_reframe(event_data, f_name, event_keys):
            err = dataset.error_message()
            print(f"Failed to reframe {f_name} in {event_data}, {err}")
            exit()
    elif not dataset.frame_create(event_data, f_name, event_keys, dot_paths, labels):
        err = dataset.error_message()
        print(f"Failed to create frame {f_name} in {event_data}, {err}")
        exit()
    grid = dataset.frame_grid(event_data, f_name)
    df = pd.DataFrame(np.array(grid), columns=["obj_id", "id", "subj_id"])
    grouped = df.groupby(["obj_id"])
    groups = grouped.groups
    # Look at all CaltechDATA records
    for k in keys:
        # Collect matched new links for the record
        record_matches = []
        metadata, err = dataset.read(collection, k)
        for idv in metadata["identifiers"]:
            if idv["identifierType"] == "oai":
                rdm_id = idv["identifier"].split("oai:data.caltech.edu:")[1]
        if err != "":
            print(f"Unexpected error on read: {err}")
        doi = "https://doi.org/" + k
        if doi in groups:
            hits = grouped.get_group(doi)
            print(hits)
            for index, h in hits.iterrows():
                # Trigger for whether we already have this link
                new = True
                if "relatedIdentifiers" in metadata:
                    for m in metadata["relatedIdentifiers"]:
                        if m["relatedIdentifier"] in h["subj_id"]:
                            new = False
                if new == True:
                    match = h["subj_id"]
                    print(match)
                    print(h["obj_id"])
                    inputv = input("Do you approve this link?  Type Y or N: ")
                    if inputv == "Y":
                        record_matches.append(match)
            # If we have to update record
            if len(record_matches) > 0:
                ids = []
                if "relatedIdentifiers" in metadata:
                    for m in metadata["relatedIdentifiers"]:
                        ids.append(m)
                matches.append([k, record_matches])
                # Now collect identifiers for record
                for match in record_matches:
                    split = match.split("doi.org/")
                    new_id = {
                        "relatedIdentifier": split[1],
                        "relatedIdentifierType": "DOI",
                        "relationType": "IsCitedBy",
                    }
                    ids.append(new_id)
                metadata["relatedIdentifiers"] = ids
                response = caltechdata_edit(
                    rdm_id, metadata, token, production=True, publish=True
                )
                print(response)
    return matches


def match_codemeta():
    collection = "github_records.ds"
    keys = dataset.keys(collection)
    for k in keys:
        existing, err = dataset.read(collection, k)
        if err != "":
            print(f"Unexpected error on read: {err}")
        if "completed" not in existing:
            print("Processing new record ", k)
            if dataset.attachments(collection, k) != "":
                dataset.detach(collection, k)

                # Update CaltechDATA
                token = os.environ["TINDTOK"]

                infile = open("codemeta.json", "r")
                try:
                    meta = json.load(infile)
                except:
                    print("Invalid json file - Skipping forever ", k)
                else:
                    standardized = codemeta_to_datacite(meta)

                    # Check that all records have a GitHub subject tag
                    add = True
                    for s in standardized["subjects"]:
                        if s["subject"] == "Github":
                            add = False
                        if s["subject"] == "GitHub":
                            add = False
                    if add == True:
                        standardized["subjects"].append({"subject": "GitHub"})
                    response = caltechdata_edit(k, standardized, token, {}, {}, True)
                    print(response)
                os.system("rm codemeta.json")

            existing["completed"] = "True"
            if not dataset.update(collection, k, existing):
                err = dataset.error_message()
                print(f"Unexpected error on read: {err}")


def add_usage(collection, token, usage_collection, production=True):
    """Add in usage text in the description field"""
    keys = dataset.keys(collection)
    biggest_views = 0
    biggest_views_record = ""
    biggest_downloads = 0
    biggest_downloads_record = ""
    total_views = 0
    total_downloads = 0
    for k in keys:
        record, err = dataset.read(collection, k)
        if err != "":
            print(err)
            exit()
        usage, err = dataset.read(usage_collection, k)
        views = usage["grand-total-unique-investigations"]
        downloads = usage["grand-total-unique-requests"]
        if views > biggest_views:
            biggest_views = views
            biggest_views_record = k
        if downloads > biggest_downloads:
            biggest_downloads = downloads
            biggest_downloads_record = k
        total_views += views
        total_downloads += downloads
        date = datetime.fromisoformat(usage["dataset-dates"][0]["value"])
        now = datetime.today()
        first = date.strftime("%B %d, %Y")
        last = now.strftime("%B %d, %Y")
        if views > 1:
            u_txt = (
                "<br>Unique Views: "
                + str(views)
                + "<br>Unique Downloads: "
                + str(downloads)
                + "<br> between "
                + first
                + " and "
                + last
                + '<br><a href="https://data.caltech.edu/stats"'
                + ">More info on how stats are collected</a><br>"
            )
            description = record["descriptions"]
            use_exists = False
            for d in description:
                descr_text = d["description"]
                # We always update an existing listing
                if descr_text.startswith("<br>Unique Views:"):
                    d["description"] = u_txt
                    use_exists = True
            # Otherwise we add a new one
            if use_exists == False:
                description.append({"descriptionType": "Other", "description": u_txt})
            response = caltechdata_edit(
                k, {"descriptions": description}, token, {}, {}, production
            )
            print(response)
    print(f"Most downloads {biggest_downloads} for record {biggest_downloads_record}")
    print(f"Most views {biggest_views} for record {biggest_views_record}")
    print(f"Total downloads {total_downloads}")
    print(f"Total views {total_views}")


def add_thesis_doi(data_collection, thesis_collection, token, production=True):
    """Add in theis DOI to CaltechDATA records"""

    # Search across CaltechTHESIS DOIs
    dot_paths = ["._Key", ".doi", ".official_url", ".related_url"]
    labels = ["eprint_id", "doi", "official_url", "related_url"]
    keys = dataset.keys(thesis_collection)
    all_metadata = get_records(dot_paths, "dois", thesis_collection, keys, labels)
    dois = []
    for metadata in progressbar(all_metadata, redirect_stdout=True):
        if "doi" in metadata:
            record_doi = metadata["doi"].strip()
            if "related_url" in metadata and "items" in metadata["related_url"]:
                items = metadata["related_url"]["items"]
                for item in items:
                    if "url" in item:
                        url = item["url"].strip()
                    if "type" in item:
                        itype = item["type"].strip().lower()
                    if itype == "doi":
                        if idutils.is_doi(url):
                            doi = "10." + url.split("10.")[1]
                            prefix = doi.split("/")[0]
                            if prefix == "10.22002":
                                dois.append([doi, record_doi])
                        else:
                            print("Ignoring non-DOI")
                            print(metadata["eprint_id"])
                            print(url.split("10."))
    for doi_link in dois:
        cd_doi = doi_link[0]
        thesis_doi = doi_link[1]
        # Exclude tombstone records
        if cd_doi != "10.22002/D1.1987":
            print("Checking " + cd_doi)
            record, err = dataset.read(data_collection, cd_doi)
            if err != "":
                print(err)
                exit()

            for idv in record["identifiers"]:
                if idv["identifierType"] == "oai":
                    record_number = idv["identifier"].split("data.caltech.edu:")[1]

            done = False
            if "relatedIdentifiers" in record:
                for idv in record["relatedIdentifiers"]:
                    identifier = idv["relatedIdentifier"]
                    if identifier == thesis_doi:
                        done = True
                if done == False:
                    identifiers = record["relatedIdentifiers"]
                    identifiers.append(
                        {
                            "relatedIdentifier": thesis_doi,
                            "relatedIdentifierType": "DOI",
                            "relationType": "IsSupplementTo",
                        }
                    )
                    record["relatedIdentifiers"] = identifiers
            else:
                record["relatedIdentifiers"] = [
                    {
                        "relatedIdentifier": thesis_doi,
                        "relatedIdentifierType": "DOI",
                        "relationType": "IsSupplementTo",
                    }
                ]
            if done == False:
                print("Adding " + thesis_doi + " to " + cd_doi)
                response = caltechdata_edit(
                    record_number, record, token, {}, True, publish=True
                )
                print(response)
