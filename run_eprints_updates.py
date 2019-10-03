import os, argparse, csv
from py_dataset import dataset
from ames.harvesters import get_caltechfeed, get_records
from ames.harvesters import get_eprint_keys
from ames.matchers import resolver_links

if __name__ == "__main__":
    if os.path.isdir("data") == False:
        os.mkdir("data")
    os.chdir("data")

    parser = argparse.ArgumentParser(description="Run updates on Eprints repositories")
    parser.add_argument("update_type", help="update type (options: resolver)")
    parser.add_argument(
        "repository",
        help="options: thesis, authors; others including test only work if using eprints source)",
    )
    parser.add_argument(
        "-test",
        help="Uses feeds data and writes report of what would be changed, but makes no changes. Provide output file name",
    )
    parser.add_argument("-username", help="Eprints username")
    parser.add_argument("-password", help="Eprints password")

    args = parser.parse_args()

    if args.test:
        source = get_caltechfeed(args.repository)
        keys = dataset.keys(source)
        keys.remove("captured")
        with open("../" + args.test, "w", newline="\n", encoding="utf-8") as fout:
            file_out = csv.writer(fout)
            resolver_links(source, keys, file_out)
    else:
        if args.repository in ["authors", "thesis", "caltechcampuspubs"]:
            source = "https://"
        else:
            source = "http://"
        if args.username:
            source = source + args.username + ":" + args.password + "@"
        source = source + args.repository + ".library.caltech.edu"
        keys = get_eprint_keys(source)
        new = []
        for k in keys:
            if int(k) > 76000:
                new.append(k)
        resolver_links(source, new)
