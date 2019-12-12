import os, argparse, csv
from py_dataset import dataset
from ames.harvesters import get_caltechfeed
from ames.harvesters import get_eprint_keys
from ames.matchers import resolver_links, special_characters, update_date

if __name__ == "__main__":
    if os.path.isdir("data") == False:
        os.mkdir("data")
    os.chdir("data")

    parser = argparse.ArgumentParser(description="Run updates on Eprints repositories")
    parser.add_argument(
        "update_type", help="update type (options: resolver, special_characters)"
    )
    parser.add_argument(
        "repository",
        help="options: thesis, authors; others including test only work if using eprints source)",
    )
    parser.add_argument("-recid", help="Eprints recid")
    parser.add_argument(
        "-test",
        help="Uses feeds data and writes report of what would be changed, but makes no changes. Provide output file name",
    )
    parser.add_argument("-username", help="Eprints username")
    parser.add_argument("-password", help="Eprints password")

    parser.add_argument(
            "-keylist", 
            help="A file containing EPrint IDs, one per line."
    )


    args = parser.parse_args()

    if args.test:
        source = get_caltechfeed(args.repository)
        keys = dataset.keys(source)
        keys.remove("captured")
        fout = open("../" + args.test, "w", newline="\n", encoding="utf-8-sig")
        file_out = csv.writer(fout)
    else:
        if args.repository in ["authors", "thesis", "caltechcampuspubs"]:
            source = "https://"
        else:
            source = "http://"
        if args.username:
            source = source + args.username + ":" + args.password + "@"
        source = source + args.repository + ".library.caltech.edu"
        keys = get_eprint_keys(source)
        file_out = None
    if args.update_type == "resolver":
        resolver_links(source, keys, file_out)
    elif args.update_type == "update_date":
        update_date(source, args.recid)
    elif args.update_type == "batch_update_date":
        keys = []
        k_name = args.keylist.strip()
        # Check if this is in the data directory or where we started.
        if os.path.exists(k_name) == False:
            k_name = os.path.join("..", k_name)
        with open(k_name) as f:
            keys = f.readlines()
            for key in keys:
                key = key.strip()
                print(f"Updating date for {key} ", end = '')
                update_date(source, key)
    elif args.update_type == "special_characters":
        special_characters(source, keys, file_out)
    else:
        print(f"Report {args.update_type} not known")
