import requests
from progressbar import progressbar
from ames.harvesters import get_eprint
from ames.harvesters import get_records


def replace_string(metadata, field, from_str, to_str):
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
                if meta["eprint_status"] != "deletion":
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


def special_characters(source, keys, outfile=None):
    if source.split(".")[-1] == "ds":
        dot_paths = [".eprint_id", ".title", ".abstract"]
        labels = ["eprint_id", "title", "abstract"]
        all_metadata = get_records(dot_paths, "official", source, keys, labels)
        outfile.writerow(
            [
                "eprints_id",
                "Current Title",
                "Updated Title",
                "Current Abstract",
                "Updated Abstract",
            ]
        )
        for meta in all_metadata:
            newtitle = replace_string(meta, "title", "_2", "₂")
            if "abstract" in meta:
                newabstract = replace_string(meta, "abstract", "_2", "₂")
            else:
                newabstract = None
            if newtitle or newabstract:
                row = [meta["eprint_id"]]
                if newtitle:
                    row += [meta["title"], newtitle]
                else:
                    row += [" ", " "]
                if newabstract:
                    row += [meta["abstract"], newabstract]
                outfile.writerow(row)
