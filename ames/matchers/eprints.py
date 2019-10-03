import requests
from progressbar import progressbar
from ames.harvesters import get_eprint
from ames.harvesters import get_records


def replace_link(metadata):
    new = None
    if "http://" in metadata["official_url"]:
        new = metadata["official_url"].replace("http://", "https://")
    return new


def resolver_links(source, keys, outfile=None):
    if source.split(".")[-1] == "ds":
        dot_paths = [".eprint_id", ".official_url"]
        labels = ["eprint_id", "official_url"]
        all_metadata = get_records(dot_paths, "official", source, keys, labels)
        for meta in all_metadata:
            new = replace_link(meta)
            if new:
                outfile.writerow([meta["eprint_id"], meta["official_url"], new])
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            meta = get_eprint(source, eprint_id)
            #Ignore errors where the record doesn't exist
            if meta != None:
                new = replace_link(meta)
                if new:
                    url = source + "/rest/eprint/" + str(eprint_id) + "/official_url.txt"
                    headers = {"content-type": "text/plain"}
                    print(eprint_id)
                    response = requests.put(url, data=new, headers=headers)
                    print(response)
