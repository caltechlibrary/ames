import requests
import re
from datetime import datetime
from progressbar import progressbar
from ames.harvesters import get_eprint
from ames.harvesters import get_records


def replace_string(metadata, field, from_str, to_str):
    """Replace part of a string in given metadata field"""
    new = None
    if from_str in metadata[field]:
        new = metadata[field].replace(from_str, to_str)
    return new


def resolver_links(source, keys, outfile=None):
    if source.split(".")[-1] == "ds":
        dot_paths = [".eprint_id", ".official_url"]
        labels = ["eprint_id", "official_url"]
        all_metadata = get_records(dot_paths, "official", source, keys, labels)
        for meta in all_metadata:
            new = replace_string(meta, "official_url", "http://", "https://")
            if new:
                outfile.writerow([meta["eprint_id"], meta["official_url"], new])
    else:
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
