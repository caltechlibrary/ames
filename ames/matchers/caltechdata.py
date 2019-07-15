import os, json, re
from caltechdata_api import caltechdata_edit
from ames import codemeta_to_datacite
from ames.harvesters import get_records
from progressbar import progressbar
from datetime import datetime
import idutils
from py_dataset import dataset
import requests


def match_cd_refs():
    token = os.environ["TINDTOK"]

    matches = []
    collection = "caltechdata.ds"
    keys = dataset.keys(collection)
    if "mediaupdate" in keys:
        keys.remove("mediaupdate")
    for k in keys:
        # Collect matched new links for the record
        record_matches = []
        print(k)
        metadata, err = dataset.read(collection, k)
        if err != "":
            print(f"Unexpected error on read: {err}")
        results, err = dataset.find(
            "crossref_refs.ds.bleve", "+obj_id:*" + metadata["identifier"]["identifier"]
        )
        if err != "":
            print(f"Unexpected error on find: {err}")
        for h in results["hits"]:
            # Trigger for whether we already have this link
            new = True
            print(h)
            if "relatedIdentifiers" in metadata:
                for m in metadata["relatedIdentifiers"]:
                    if m["relatedIdentifier"] in h["fields"]["subj_id"]:
                        new = False
                    # print(re.match(m['relatedIdentifier'],h['fields']['subj_id']))
                    # print(m['relatedIdentifier'])
            if new == True:
                match = h["fields"]["subj_id"]
                print(match)
                print(h["fields"]["obj_id"])
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
                # matches.append([match,k])
                split = match.split("doi.org/")
                new_id = {
                    "relatedIdentifier": split[1],
                    "relatedIdentifierType": "DOI",
                    "relationType": "IsCitedBy",
                }
                ids.append(new_id)
            newmetadata = {"relatedIdentifiers": ids}
            response = caltechdata_edit(token, k, newmetadata, {}, {}, True)
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
            print("Processing new record")
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
                    response = caltechdata_edit(token, k, standardized, {}, {}, True)
                    print(response)
                os.system("rm codemeta.json")

            existing["completed"] = "True"
            err = dataset.update(collection, k, existing)
            if err != "":
                print(f"Unexpected error on read: {err}")


def fix_multiple_links(input_collection, token):
    keys = dataset.keys(input_collection)
    for k in keys:
        record, err = dataset.read(input_collection, k)
        if err != "":
            print(err)
            exit()
        if "relatedIdentifiers" in record:
            idvs = []
            new = []
            dupes = []
            replace = False
            record_doi = record["identifier"]["identifier"]
            for idv in record["relatedIdentifiers"]:
                idvs.append(idv["relatedIdentifier"])
            for idv in record["relatedIdentifiers"]:
                identifier = idv["relatedIdentifier"]
                if identifier == record_doi:
                    # Having a related identifier that is the same as the record
                    # doi doesn't make any sense
                    replace = True
                    dupes.append(identifier)
                else:
                    count = idvs.count(identifier)
                    if count > 1:
                        replace = True
                        if identifier not in dupes:
                            # We need to save the first duplicate
                            new.append(idv)
                            # Add to list of those already saved
                            dupes.append(identifier)
                        else:
                            # This will be deleted
                            dupes.append(identifier)
                    else:
                        # Save all unique ids
                        new.append(idv)
            if replace == True:
                print("Duplicate links found in record ", k)
                print("Will delete these links", dupes)
                response = input("Do you approve this change? Y or N")
                new_metadata = {"relatedIdentifiers": new}
                if response == "Y":
                    response = caltechdata_edit(token, k, new_metadata, {}, {}, True)
                    print(response)


def add_citation(collection, token, production=True):
    """Add in example citation text in the description field"""
    keys = dataset.keys(collection)
    for k in keys:
        record, err = dataset.read(collection, k)
        if err != "":
            print(err)
            exit()
        description = record["descriptions"]
        cite_exists = False
        for d in description:
            descr_text = d["description"]
            if descr_text.startswith("<br>Cite this record as:"):
                cite_exists = True
        if cite_exists == False:
            record_doi = record["identifier"]["identifier"]
            citation_link = "https://data.datacite.org/text/x-bibliography;style=apa/"
            citation = requests.get(citation_link + record_doi).text
            doi_url = "https://doi.org/" + record_doi.lower()
            if doi_url in citation:
                # Check that we have a citation and not a server error,
                # otherwise wait till next time
                citation = citation.replace(
                    doi_url, '<a href="' + doi_url + '">' + doi_url + "</a>"
                )
                # Replace link text with HTML link
                n_txt = (
                    "<br>Cite this record as:<br>"
                    + citation
                    + '<br> or choose a <a href="https://crosscite.org/?doi='
                    + record_doi
                    + '"> different citation style.</a><br>'
                    + '<a href="https://data.datacite.org/application/x-bibtex/'
                    + record_doi
                    + '">Download Citation</a><br>'
                )
                description.append({"descriptionType": "Other", "description": n_txt})
                response = caltechdata_edit(
                    token, k, {"descriptions": description}, {}, {}, production
                )
                print(response)


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
        record_doi = record["identifier"]["identifier"]
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
                token, k, {"descriptions": description}, {}, {}, production
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
        print("Checking " + cd_doi)
        if "D1" in cd_doi:
            record_number = cd_doi.split("D1.")[1]
        if "d1" in cd_doi:
            record_number = cd_doi.split("d1.")[1]
        record, err = dataset.read(data_collection, record_number)
        if err != "":
            print(err)
            exit()

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
                new_metadata = {"relatedIdentifiers": identifiers}
        else:
            new_metadata = {
                "relatedIdentifiers": [
                    {
                        "relatedIdentifier": thesis_doi,
                        "relatedIdentifierType": "DOI",
                        "relationType": "IsSupplementTo",
                    }
                ]
            }
        if done == False:
            print("Adding " + thesis_doi + " to " + cd_doi)
            response = caltechdata_edit(
                token, record_number, new_metadata, {}, {}, True
            )
            print(response)
