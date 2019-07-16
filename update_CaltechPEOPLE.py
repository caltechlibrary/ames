import os
from py_dataset import dataset
from ames.harvesters import get_caltechfeed, get_records

if __name__ == "__main__":

    import_coll = "imported.ds"
    sheet = "1ZI3-XvQ_3rLcKrF-4FBa2tEInIdQfOnGJ9L_NmhmoGs"
    os.system("rm -rf imported.ds")
    dataset.init(import_coll)
    err = dataset.import_gsheet(import_coll, sheet, "CaltechPEOPLE", 4, "A:AA")
    if err != "":
        print(err)

    people_list = dataset.keys(import_coll)
    people = []
    for p in people_list:
        record, err = dataset.read(import_coll, p)
        people.append(record)

    # Profiles collection from feeds
    profile_ds = "profiles.ds"
    keys = dataset.keys(profile_ds)
    labels = ["orcid", "creator_id"]
    dot_paths = [".orcid", ".creator_id"]

    all_metadata = get_records(dot_paths, "profile", profile_ds, keys, labels)
    for profile in all_metadata:
        if "creator_id" in profile:
            idv = profile["creator_id"]
        else:
            print("ERROR", profile)
        for person in people:
            if person["Authors_ID"] != "":
                if person["Authors_ID"] == idv:
                    if person["ORCID"] == "":
                        person["ORCID"] = profile["orcid"]
                        dataset.update(import_coll, person["CL_PEOPLE_ID"], person)
                        print("Updated ", person["CL_PEOPLE_ID"])
                    elif person["ORCID"] != profile["orcid"]:
                        print(
                            "Inconsistent ORCIDS for ",
                            person["CL_PEOPLE_ID"],
                            person["ORCID"],
                            "CaltechAUTHORS",
                            profile["orcid"],
                        )

    # TODO - port to python
    # Run on command line
    # dataset frame -all imported.ds gsheet-sync ._Key .ORCID
    # dataset frame-labels imported.ds gsheet-sync "CL_PEOPLE_ID" "ORCID"
    # dataset sync-send imported.ds gsheet-sync 1ZI3-XvQ_3rLcKrF-4FBa2tEInIdQfOnGJ9L_NmhmoGs CaltechPEOPLE
