import os, argparse, csv
from py_dataset import dataset
from ames.harvesters import get_caltechfeed
from ames.harvesters import get_eprint_keys
from ames.matchers import resolver_links, special_characters, update_date, release_files, update_doi

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

    args = parser.parse_args()

    if args.test:
        source = get_caltechfeed(args.repository)
        keys = dataset.keys(source)
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
    elif args.update_type == "update_doi":
        update_doi(source, keys, file_out)
    elif args.update_type == "release_files":
        #Need to have dataset collection as well
        collection = get_caltechfeed(args.repository)
        fout = open("../thesis_released_files.csv", "w", newline="\n", encoding="utf-8-sig")
        file_out = csv.writer(fout)
        release_files(collection, source, file_out)
    elif args.update_type == "update_date":
        update_date(source, args.recid)
    elif args.update_type == "special_characters":
        special_characters(source, keys, file_out)
    else:
        print(f"Report {args.update_type} not known")
