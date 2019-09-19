import getpass
import os, argparse, csv
from py_dataset import dataset
from progressbar import progressbar
from asnake.client import ASnakeClient


def is_in_range(year_arg, year):
    # Is a given year in the range of a year argument YEAR-YEAR or YEAR?
    if year_arg != None:
        split = year_arg.split("-")
        if len(split) == 2:
            if int(year) >= int(split[0]) and int(year) <= int(split[1]):
                return True
        else:
            if year == split[0]:
                return True
    else:
        return True
    return False


def keep_record(metadata, years, item_type=None, group=None):
    keep = True

    if years:
        # Not implemented for CaltechDATA
        if "date" in metadata:
            year = metadata["date"].split("-")[0]
            if is_in_range(years, year) == False:
                keep = False
        else:
            keep = False

    if item_type:
        # CaltechDATA item
        if "resourceTye" in metadata:
            if metadata["resourceType"]["resourceTypeGeneral"] not in item_type:
                keep = False
        # Eprints item
        elif "type" in metadata:
            if "monograph_type" in metadata:
                # There are records with monograph_type that arn't monographs
                if metadata["type"] == "monograph":
                    if (
                        metadata["monograph_type"] not in item_type
                        and metadata["type"] not in item_type
                    ):
                        keep = False
                else:
                    if metadata["type"] not in item_type:
                        keep = False
            else:
                if metadata["type"] not in item_type:
                    keep = False
        else:
            print("Item type not found in record")
            keep = False

    if group:
        # Not implemented for CaltechDATA
        if "local_group" in metadata:
            match = False
            if isinstance(metadata["local_group"]["items"], list) == False:
                # Deal with single item listings
                metadata["local_group"]["items"] = [metadata["local_group"]["items"]]
            for gname in metadata["local_group"]["items"]:
                if gname in group:
                    match = True
            if match == False:
                keep = False
        else:
            keep = False
    return keep


def break_up_group(metadata, field, val, row):
    """Break up a array in 'field' into a single element with number 'val'"""
    if field in metadata:
        if len(metadata[field]) > val:
            row.append(metadata[field][val])
        else:
            # This many values are not present, add blank cell
            row.append("")
    else:
        # Metadata not present, add blank cell
        row.append("")
    return row





def doi_report(
    file_obj, keys, source, years=None, all_records=True, item_type=None, group=None
):
    """Output a report of DOIs """
    file_obj.writerow(
        [
            "Eprint ID",
            "DOI",
            "Year",
            "Author ID",
            "Title",
            "Resolver URL",
            "Series Information",
        ]
    )
    all_metadata = []
    if source.split(".")[-1] == "ds":
        dot_paths = [
            "._Key",
            ".doi",
            ".official_url",
            ".date",
            ".related_url",
            ".creators",
            ".title",
            ".local_group",
            ".type",
            ".monograph_type",
            ".other_numbering_system",
            ".series",
            ".number",
        ]
        labels = [
            "eprint_id",
            "doi",
            "official_url",
            "date",
            "related_url",
            "creators",
            "title",
            "local_group",
            "type",
            "monograph_type",
            "other_numbering_system",
            "series",
            "number",
        ]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))

    for metadata in all_metadata:
        doi = ""

        # Determine if we want the record
        if keep_record(metadata, years, item_type, group):

            ep = metadata["eprint_id"]
            # Handle odd CaltechAUTHORS DOI setup
            if "doi" in metadata:
                doi = metadata["doi"].strip()
            elif "related_url" in metadata and "items" in metadata["related_url"]:
                items = metadata["related_url"]["items"]
                for item in items:
                    if "url" in item:
                        url = item["url"].strip()
                    if "type" in item:
                        itype = item["type"].strip().lower()
                    if "description" in item:
                        description = item["description"].strip().lower()
                    if itype == "doi" and description == "article":
                        doi = url
                        break
            else:
                doi = ""
            if "creators" in metadata:
                if "id" in metadata["creators"]["items"][0]:
                    author = metadata["creators"]["items"][0]["id"]
                else:
                    author = ""
                    print("Record " + ep + " is missing author id")

            if "title" not in metadata:
                print("Record " + ep + " is missing Title")
                exit()
            title = metadata["title"]
            url = metadata["official_url"]
            if "date" in metadata:
                year = metadata["date"].split("-")[0]
            else:
                year = ""
            # Series info
            series = ""
            if "other_numbering_system" in metadata:
                num = metadata["other_numbering_system"]
                series = "other numbering:"
                for item in num["items"]:
                    if "id" in item:
                        series += " " + item["name"] + " " + item["id"]
                    else:
                        series += " " + item["name"]
            if "series" in metadata:
                series += "series:"
                if "number" in metadata:
                    series += " " + metadata["series"] + " " + metadata["number"]
                else:
                    series += " " + metadata["series"]
            if all_records == False:
                if doi != "":
                    file_obj.writerow([ep, doi, year, author, title, url, series])
            else:
                file_obj.writerow([ep, doi, year, author, title, url, series])
    print("Report finished!")


def status_report(file_obj, keys, source):
    """Output a report of items that have a status other than archive
    or have metadata visability other than show.
    Under normal circumstances this should return no records when run on feeds"""
    file_obj.writerow(["Eprint ID", "Resolver URL", "Status"])

    all_metadata = []
    if source.split(".")[-1] == "ds":
        dot_paths = ["._Key", ".eprint_status", ".official_url", ".metadata_visibility"]
        labels = ["eprint_id", "eprint_status", "official_url", "metadata_visibility"]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))

    for metadata in all_metadata:
        if metadata["eprint_status"] != "archive":
            ep = metadata["eprint_id"]
            status = metadata["eprint_status"]
            url = metadata["official_url"]
            print("Record matched: ", url)
            file_obj.writerow([ep, url, status])
        if metadata["metadata_visibility"] != "show":
            print(metadata["metadata_visibility"])
            ep = metadata["eprint_id"]
            status = metadata["metadata_visibility"]
            url = metadata["official_url"]
            print("Record matched: ", url)
            file_obj.writerow([ep, url, status])
    print("Report finished!")


def license_report(file_obj, keys, source, item_type=None, rtype="summary"):
    """Write report with license types"""
    if source.split(".")[0] != "CaltechDATA":
        print(source.split(".")[0] + " is not supported for license report")
        exit()
    else:
        all_metadata = []
        dot_paths = [
            "._Key",
            ".rightsList",
            ".resourceType",
            ".creators",
            ".fundingReferences",
        ]
        labels = ["id", "rightsList", "resourceType", "creators", "fundingReferences"]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
        licenses = {}

        if rtype == "summary":

            file_obj.writerow(["License Name", "Number of Records", "IDs"])
            for metadata in all_metadata:
                if item_type != None:
                    # Restrict to a specific item type
                    if metadata["resourceType"]["resourceTypeGeneral"] in item_type:
                        lic = metadata["rightsList"][0]["rights"]
                    else:
                        lic = None
                # Otherwise we always save license
                else:
                    lic = metadata["rightsList"]["rights"]

                if lic != None:
                    if lic in licenses:
                        licenses[lic]["count"] += 1
                        licenses[lic]["ids"].append(metadata["id"])
                    else:
                        new = {}
                        new["count"] = 1
                        new["ids"] = [metadata["id"]]
                        licenses[lic] = new

            for lic in licenses:
                file_obj.writerow([lic, licenses[lic]["count"], licenses[lic]["ids"]])

        else:

            file_obj.writerow(["CaltechDATA ID", "Authors", "License", "Funders"])
            for metadata in all_metadata:
                write = False
                if item_type != None:
                    # Restrict to a specific item type
                    if metadata["resourceType"]["resourceTypeGeneral"] in item_type:
                        write = True
                # Otherwise we always save license
                else:
                    write = True

                if write == True:
                    creators = ""
                    for c in metadata["creators"]:
                        if creators != "":
                            creators += ";"
                        creators += c["creatorName"]
                    funders = ""
                    if "fundingReferences" in metadata:
                        for c in metadata["fundingReferences"]:
                            if funders != "":
                                funders += ";"
                            funders += c["funderName"]
                    if "rightsList" not in metadata:
                        print("record ", metadata["id"], " is missing license")
                        exit()
                    file_obj.writerow(
                        [
                            metadata["id"],
                            creators,
                            metadata["rightsList"][0]["rights"],
                            funders,
                        ]
                    )


def file_report(file_obj, keys, source, years=None):
    """Write out a report of files with potential issues"""
    file_obj.writerow(["Eprint ID", "Problem", "Impacted Files", "Resolver URL"])
    all_metadata = []
    if source.split(".")[-1] == "ds":
        dot_paths = ["._Key", ".documents", ".date", ".official_url"]
        labels = ["eprint_id", "documents", "date", "official_url"]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))

    for metadata in all_metadata:
        if "date" in metadata:
            year = metadata["date"].split("-")[0]
            if is_in_range(years, year):
                if "documents" in metadata:
                    for d in metadata["documents"]:
                        if "files" in d:
                            for f in d["files"]:
                                filename = f["filename"]
                                extension = filename.split(".")[-1]
                                if extension == "html":
                                    ep = metadata["eprint_id"]
                                    url = metadata["official_url"]
                                    print("HTML: ", url)
                                    file_obj.writerow([ep, "HTML File", filename, url])
                                if extension == "htm":
                                    ep = metadata["eprint_id"]
                                    url = metadata["official_url"]
                                    print("HTM: ", url)
                                    file_obj.writerow([ep, "HTML File", filename, url])
                                if len(filename) > 200:
                                    ep = metadata["eprint_id"]
                                    url = metadata["official_url"]
                                    print("Length: ", url)
                                    file_obj.writerow(
                                        [ep, "File Name Length", filename, url]
                                    )
    print("Report finished!")


def alt_url_report(file_obj, keys, source):
    print(f"Processing {len(keys)} eprint records for alt_url")
    file_obj.writerow(["eprint_id", "alt_url", "related_url", "url_added", "type"])
    if source.split(".")[-1] == "ds":
        dot_paths = ["._Key", ".related_url.items", ".alt_url"]
        labels = ["eprint_id", "items", "alt_url"]
        all_metadata = get_records(dot_paths, "alt", source, keys, labels)
        for metadata in progressbar(all_metadata, redirect_stdout=True):
            key = metadata["eprint_id"]
            if "alt_url" in metadata:
                alt = metadata["alt_url"]
                related = ""
                type_v = "Other"
                new_url = alt
                if is_doi(new_url):
                    type_v = "DOI"
                    new_url = "https://doi.org/" + normalize_doi(new_url)
                if is_arxiv(new_url):
                    type_v = "arXiv"
                if "items" in metadata:
                    for i in metadata["items"]:
                        if i["url"] == new_url:
                            new_url = ""
                        if is_doi(i["url"]):
                            norm_rel = normalize_doi(i["url"])
                            norm = alt
                            # Make sure both are normalized
                            if type_v == "DOI":
                                norm = normalize_doi(norm)
                            if norm == norm_rel:
                                new_url = ""
                        related = related + i["url"] + " ; "
                if new_url == "":
                    type_v = ""
                file_obj.writerow([key, alt, related, new_url, type_v])
        print("Report finished!")
    else:
        print("Not Implemented")


def creator_search(file_obj, keys, source, search_id):
    print(f"Processing {len(keys)} eprint records for creators")
    if source.split(".")[-1] == "ds":
        dot_paths = ["._Key", ".creators.items"]
        labels = ["eprint_id", "items"]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
        matched_keys = []
        for metadata in progressbar(all_metadata, redirect_stdout=True):
            key = metadata["eprint_id"]
            if "items" in metadata:
                for item in metadata["items"]:
                    if "id" in item:
                        if item["id"] == search_id:
                            matched_keys.append(key)
        print(f"Processing {len(matched_keys)} eprint records that match search")
        dot_paths = ["._Key", ".creators.items", ".official_url"]
        labels = ["eprint_id", "items", "resolver"]
        select_metadata = get_records(dot_paths, "dois", source, matched_keys, labels)
        for metadata in progressbar(select_metadata, redirect_stdout=True):
            file_obj.writerow([metadata["eprint_id"]])
            file_obj.writerow([metadata["resolver"]])
            file_obj.writerow(["family", "given", "id", "orcid"])
            for item in metadata["items"]:
                author_record = []
                if "family" in item["name"]:
                    author_record.append(item["name"]["family"])
                else:
                    author_record.append(" ")
                if "given" in item["name"]:
                    author_record.append(item["name"]["given"])
                else:
                    author_record.append(" ")
                if "id" in item:
                    author_record.append(item["id"])
                else:
                    author_record.append(" ")
                if "orcid" in item:
                    author_record.append(item["orcid"])
                else:
                    author_record.append(" ")
                file_obj.writerow(author_record)


def file_report(file_obj, client, subject=None, years=None):
    client.authorize()
    print(f'Requesting digital objects')
    for obj in client.get_paged('/repositories/2/digital_objects'):
        print(json.dumps(obj,indent=1))
        exit()
        timestamp = obj['create_time']
        date_str = timestamp.split('T')[0]
        split = date_str.split('-')
        d = date(int(split[0]),int(split[1]),int(split[2]))
        if d == date.fromisoformat('2019-02-23'):
            out_file.writerow([obj['create_time'],obj['title']])
            print(timestamp)
            print(obj['title'])
    
    
    creator_ids = []
    creators = {}
    print(f"Processing {len(keys)} eprint records for creators")
    if source.split(".")[-1] == "ds":
        dot_paths = ["._Key", ".creators.items"]
        labels = ["eprint_id", "items"]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
        for metadata in progressbar(all_metadata, redirect_stdout=True):
            key = metadata["eprint_id"]
            if "items" in metadata:
                find_creators(metadata["items"], key, creators, creator_ids)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            metadata = get_eprint(source, eprint_id)
            if metadata != None:
                if "creators" in metadata and "items" in metadata["creators"]:
                    items = metadata["creators"]["items"]
                    find_creators(items, eprint_id, creators, creator_ids)

    creator_ids.sort()
    file_obj.writerow(["creator_id", "orcid", "existing_ids", "update_ids"])
    for creator_id in creator_ids:
        creator = creators[creator_id]
        # print(creator)
        write = False
        if update_only:
            if creator["orcids"] and creator["update_ids"]:
                write = True
        else:
            write = True
        if write == True:
            orcid = "|".join(creator["orcids"])
            eprint_ids = "|".join(creator["eprint_ids"])
            update_ids = "|".join(creator["update_ids"])
            if len(creator["orcids"]) > 1:
                # All items will need to be updated if there are multiple orcids
                update_ids = update_ids + "|" + eprint_ids
                eprint_ids = ""
            file_obj.writerow([creator_id, orcid, eprint_ids, update_ids])
    print("Report finished!")


def find_creators(items, eprint_id, creators, creator_ids):
    """Take a item list and return creators"""
    for item in items:
        if "id" in item:
            creator_id = item["id"]
            orcid = ""
            if "orcid" in item:
                orcid = item["orcid"]
            if creator_id in creators:
                # Existing creator
                if orcid != "":
                    if creators[creator_id]["orcids"] == []:
                        # New ORCID
                        creators[creator_id]["orcids"].append(orcid)
                        creators[creator_id]["eprint_ids"].append(eprint_id)
                    elif orcid in creators[creator_id]["orcids"]:
                        # We already have ORCID
                        creators[creator_id]["eprint_ids"].append(eprint_id)
                    else:
                        # Creator has multiple orcids
                        creators[creator_id]["orcids"].append(orcid)
                        creators[creator_id]["update_ids"].append(eprint_id)
                else:
                    # We always want to (potentially) update blank orcids
                    creators[creator_id]["update_ids"].append(eprint_id)
            else:
                # We have a new creator
                creators[creator_id] = {}
                if orcid != "":
                    creators[creator_id]["orcids"] = [orcid]
                    creators[creator_id]["eprint_ids"] = [eprint_id]
                    creators[creator_id]["update_ids"] = []
                else:
                    creators[creator_id]["orcids"] = []
                    creators[creator_id]["eprint_ids"] = []
                    creators[creator_id]["update_ids"] = [eprint_id]
                creator_ids.append(creator_id)


if __name__ == "__main__":
    if os.path.isdir("data") == False:
        os.mkdir("data")
    os.chdir("data")

    parser = argparse.ArgumentParser(description="Run a report on ArchiveSpace")
    parser.add_argument(
        "report_name",
        help="report name (options: accession_report)",
    )
    parser.add_argument("output", help="output file name")
    parser.add_argument("-years", help="format: 1939 or 1939-1940")
    parser.add_argument("-subject", help="Return items that match subject")

    args = parser.parse_args()

    # Initialize the ASnake client
    baseurl = 'https://collections.archives.caltech.edu/staff/api/'

    username = input("Username: ")
    password = getpass.getpass(f"Password for {username}: ")

    client = ASnakeClient(
        baseurl = baseurl,
        username = username,
        password = password
        )

    with open("../" + args.output, "w", newline="\n", encoding="utf-8") as fout:
        if args.output.split(".")[-1] == "tsv":
            file_out = csv.writer(fout, delimiter="\t")
        else:
            file_out = csv.writer(fout)
        if args.report_name == "accession_report":
            file_report(file_out, client, args.subject, args.years)
        else:
            print(args.report_name, " report type is not known")
