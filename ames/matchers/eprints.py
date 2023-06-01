import requests
import re
from idutils import normalize_doi, is_doi
from datetime import datetime
from progressbar import progressbar
from py_dataset import dataset
from ames.harvesters import get_eprint
from ames.harvesters import get_records
from ames.utils import is_in_range


def replace_string(metadata, field, from_str, to_str):
    """Replace part of a string in given metadata field"""
    new = None
    if from_str in metadata[field]:
        new = metadata[field].replace(from_str, to_str)
    return new


def decide_doi_update(metadata):
    if "doi" not in metadata:
        possible = []
        eprint = metadata["eprint_id"]
        if "related_url" in metadata and "items" in metadata["related_url"]:
            items = metadata["related_url"]["items"]
            for item in items:
                description = ""
                if "url" in item:
                    url = item["url"].strip()
                if "type" in item:
                    itype = item["type"].strip().lower()
                if "description" in item:
                    description = item["description"].strip().lower()
                if itype == "doi":
                    if is_doi(url):
                        possible.append([normalize_doi(url), description])
                    else:
                        # Dropping anything without a 10. pattern
                        if "10." in url:
                            doi = "10." + url.split("10.")[1]
                            if is_doi(doi):
                                possible.append([doi, description])
            if len(possible) == 1:
                # Description not really used
                return [eprint, possible[0][0]]
            else:
                return None
        else:
            return None
    else:
        return None


def update_doi(source, keys, to_value=None, outfile=None):
    if source.split(".")[-1] == "ds":
        # This generates report
        dot_paths = [".eprint_id", ".doi", ".related_url"]
        labels = ["eprint_id", "doi", "related_url"]
        all_metadata = get_records(dot_paths, "doi", source, keys, labels)
        for metadata in all_metadata:
            update = decide_doi_update(metadata)
            if update:
                outfile.writerow(update)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            print(eprint_id)
            meta = get_eprint(source, eprint_id)
            # Ignore errors where the record doesn't exist
            if meta != None:
                url = source + "/rest/eprint/" + str(eprint_id) + "/doi.txt"
                headers = {"content-type": "text/plain"}
                if to_value == None:
                    update = decide_doi_update(meta)
                    if update:
                        doi = update[1].replace("\u200b", "")
                        # Handle invisible charaters in ASM DOIs
                        response = requests.put(url, data=doi, headers=headers)
                        print(response)
                else:
                    if "doi" not in meta:
                        response = requests.put(url, data=to_value, headers=headers)
                        print(response)
                    else:
                        print("Skipping because DOI value is already set")


def update_pub_data(source, keys, outfile=None):
    if source.split(".")[-1] == "ds":
        # This generates report
        # dot_paths = [".eprint_id", ".doi", ".related_url"]
        # labels = ["eprint_id", "doi", "related_url"]
        # all_metadata = get_records(dot_paths, "doi", source, keys, labels)
        # for metadata in all_metadata:
        #    update = decide_doi_update(metadata)
        #    if update:
        #        outfile.writerow(update)
        print("Not Implemented")
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            print(eprint_id)
            meta = get_eprint(source, eprint_id)
            # Ignore errors where the record doesn't exist
            if meta != None:
                if "doi" not in meta:
                    print("NO DOI")
                    exit()
                doi = meta["doi"]
                if "volume" not in meta:
                    url = source + "/rest/eprint/" + str(eprint_id) + "/volume.txt"
                    headers = {"content-type": "text/plain"}
                    response = requests.put(url, data="1", headers=headers)
                    print(response)
                if "number" not in meta:
                    url = source + "/rest/eprint/" + str(eprint_id) + "/number.txt"
                    headers = {"content-type": "text/plain"}
                    response = requests.put(url, data="1", headers=headers)
                    print(response)
                if "pagerange" not in meta:
                    url = source + "/rest/eprint/" + str(eprint_id) + "/pagerange.txt"
                    headers = {"content-type": "text/plain"}
                    response = requests.put(url, data="1", headers=headers)
                    print(response)


def update_record_number(source, keys):
    # Update record_number to what is in persistent url field
    if source.split(".")[-1] != "ds":
        # Report version in coda_reports script
        for eprint_id in progressbar(keys, redirect_stdout=True):
            print(eprint_id)
            meta = get_eprint(source, eprint_id)
            resolver = meta["official_url"]
            new = resolver.split("resolver.caltech.edu/")[1]
            url = source + "/rest/eprint/" + str(eprint_id) + "/id_number.txt"
            headers = {"content-type": "text/plain"}
            response = requests.put(url, data=new, headers=headers)
            print(response)


def publisher(source, keys, from_value, to_value, outfile=None):
    if source.split(".")[-1] == "ds":
        # This generates report
        dot_paths = [".eprint_id", ".publisher"]
        labels = ["eprint_id", "publisher"]
        all_metadata = get_records(dot_paths, "official", source, keys, labels)
        for meta in all_metadata:
            if "publisher" in meta:
                if meta["publisher"] == from_value:
                    outfile.writerow([meta["eprint_id"], meta["publisher"], to_value])
    else:
        # This makes changes
        for eprint_id in progressbar(keys, redirect_stdout=True):
            meta = get_eprint(source, eprint_id)
            # Ignore errors where the record doesn't exist
            if meta != None:
                if meta["eprint_status"] not in ["deletion", "inbox"]:
                    if meta["publisher"] == from_value:
                        url = (
                            source + "/rest/eprint/" + str(eprint_id) + "/publisher.txt"
                        )
                        headers = {"content-type": "text/plain"}
                        print(eprint_id)
                        response = requests.put(url, data=to_value, headers=headers)
                        print(response)


def resolver_links(source, keys, outfile=None):
    if source.split(".")[-1] == "ds":
        # This generates report
        dot_paths = [".eprint_id", ".official_url"]
        labels = ["eprint_id", "official_url"]
        all_metadata = get_records(dot_paths, "official", source, keys, labels)
        for meta in all_metadata:
            new = replace_string(meta, "official_url", "http://", "https://")
            if new:
                outfile.writerow([meta["eprint_id"], meta["official_url"], new])
    else:
        # This makes changes
        for eprint_id in progressbar(keys, redirect_stdout=True):
            meta = get_eprint(source, eprint_id)
            # Ignore errors where the record doesn't exist
            if meta != None:
                if meta["eprint_status"] not in ["deletion", "inbox"]:
                    new = replace_string(meta, "official_url", "http://", "https://")
                    if new:
                        url = (
                            source
                            + "/rest/eprint/"
                            + str(eprint_id)
                            + "/official_url.txt"
                        )
                        headers = {"content-type": "text/plain"}
                        print(eprint_id)
                        response = requests.put(url, data=new, headers=headers)
                        print(response)


def thesis_match(metadata):
    if metadata["type"] == "masters":
        return True
    if metadata["type"] == "phd":
        return True
    if metadata["type"] == "engd":
        return True
    else:
        return False


def release_files(source, base_url, outfile=None):
    if source.split(".")[-1] == "ds":
        # This generates report
        dot_paths = [
            ".eprint_id",
            ".documents",
            ".date",
            ".eprint_status",
            ".creators.items[0].name.family",
            ".thesis_type",
            ".full_text_status",
        ]
        labels = [
            "eprint_id",
            "documents",
            "date",
            "status",
            "family",
            "type",
            "full_text",
        ]
        keys = dataset.keys(source)
        all_metadata = get_records(dot_paths, "official", source, keys, labels)
        all_metadata.sort(key=lambda all_metadata: all_metadata["family"])
        all_metadata.sort(key=lambda all_metadata: all_metadata["date"])
        for meta in all_metadata:
            year = meta["date"].split("-")[0]
            if is_in_range("2004-2005", year):
                if thesis_match(meta):
                    files = []
                    fnames = []
                    count = 0
                    for document in meta["documents"]:
                        count = count + 1
                        if document["security"] == "validuser":
                            files.append(count)
                            fnames.append(document["main"])
                    if len(files) > 0:
                        eprint_id = meta["eprint_id"]
                        print(eprint_id)
                        outfile.writerow(
                            [
                                year,
                                meta["family"],
                                eprint_id,
                                meta["status"],
                                meta["full_text"],
                                files,
                                fnames,
                            ]
                        )
                        mixed = False
                        for filen in files:
                            new = "public"
                            # Doc status
                            url = (
                                base_url
                                + "/rest/eprint/"
                                + str(eprint_id)
                                + "/full_text_status.txt"
                            )
                            response = requests.get(url)
                            eprint_status = response.text
                            if eprint_status == "restricted":
                                response = requests.put(url, data=new, headers=headers)
                                print(response)
                            elif eprint_status == "mixed":
                                print("mixed, skipping")
                                mixed = True
                            elif eprint_status != "public":
                                print(eprint_status)
                                print(url)
                                exit()
                            url = (
                                base_url
                                + "/rest/eprint/"
                                + str(eprint_id)
                                + "/documents/"
                                + str(filen)
                                + "/security.txt"
                            )
                            headers = {"content-type": "text/plain"}
                            response = requests.get(url)
                            live_status = response.text
                            if not mixed:
                                if live_status == "validuser":
                                    response = requests.put(
                                        url, data=new, headers=headers
                                    )
                                    print(response)
                                elif live_status != "public":
                                    print(live_status)
                                    print(url)
                                    exit()


def update_date(source, recid):
    url = source + "/rest/eprint/" + str(recid) + "/lastmod.txt"
    now = datetime.utcnow()

    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    print(dt_string)
    headers = {"content-type": "text/plain"}
    response = requests.put(url, data=dt_string, headers=headers)
    print(response)


def replace_character(metadata, field, replacements):
    """replace characters based on a dictionary"""
    new = None
    for rep in replacements:
        # Using re to catch cases like _221, which look weird partially converted
        if re.match(rf".*{re.escape(rep)}[^0-9]", metadata[field]):
            if new:
                new = re.sub(rf"{re.escape(rep)}(?=[^0-9])", replacements[rep], new)
            else:
                new = re.sub(
                    rf"{re.escape(rep)}(?=[^0-9])", replacements[rep], metadata[field]
                )
    return new


def special_characters(source, keys, outfile=None):
    replacements = {
        "_0": "₀",
        "_1": "₁",
        "_2": "₂",
        "_3": "₃",
        "_4": "₄",
        "_5": "₅",
        "_6": "₆",
        "_7": "₇",
        "_8": "₈",
        "_9": "₉",
        "_+": "₊",
        "_-": "₋",
        "_a": "ₐ",
        "_e": "ₑ",
        "_o": "ₒ",
        "_x": "ₓ",
        "^0": "⁰",
        "^1": "¹",
        "^2": "²",
        "^3": "³",
        "^4": "⁴",
        "^5": "⁵",
        "^6": "⁶",
        "^7": "⁷",
        "^8": "⁸",
        "^9": "⁹",
        "^+": "⁺",
        "^-": "⁻",
        "^n": "ⁿ",
        "^i": "ⁱ",
        "’": "'",
        "“": '"',
        "”": '"',
    }
    if source.split(".")[-1] == "ds":
        dot_paths = [".eprint_id", ".title", ".abstract"]
        labels = ["eprint_id", "title", "abstract"]
        all_metadata = get_records(dot_paths, "official", source, keys, labels)
        outfile.writerow(
            [
                "eprints_id",
                # "Current Title",
                "Updated Title",
                # "Current Abstract",
                "Updated Abstract",
            ]
        )
        for meta in all_metadata:
            eprint_id = meta["eprint_id"]
            newtitle = replace_character(meta, "title", replacements)
            if "abstract" in meta:
                newabstract = replace_character(meta, "abstract", replacements)
            else:
                newabstract = None
            if outfile:
                if newtitle or newabstract:
                    row = [eprint_id]
                    if newtitle:
                        row += [newtitle]  # [meta["title"], newtitle]
                    else:
                        row += [" ", " "]
                    if newabstract:
                        row += [newabstract]  # [meta["abstract"], newabstract]
                    outfile.writerow(row)
