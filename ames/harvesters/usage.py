import os, csv, math
import requests
import pandas as pd
from datetime import datetime
from progressbar import progressbar
from py_dataset import dataset


def file_mapping(source_collection, mapping_file):
    """Return a dictionary that maps /tindfiles/serve urls to records.
    Expects either an existing csv file dictionary or a file name
    to save a new dictionary."""

    available = os.path.isfile(mapping_file)
    # If we have an existing file
    if available == True:
        mapping = {}
        reader = csv.reader(open(mapping_file))
        for row in reader:
            mapping[row[0]] = row[1]
    else:
        mapping = {}

    keys = dataset.keys(source_collection)
    for k in keys:
        # Handle history records where the key is the item and revision
        if "-" in k:
            rec_id = k.split("-")[0]
        else:
            rec_id = k
        record, err = dataset.read(source_collection, k)
        if err != "":
            print(err)
            exit()

        # Ignore embargoed records
        if "electronic_location_and_access" in record:
            for filev in record["electronic_location_and_access"]:
                url = filev["uniform_resource_identifier"]
                # name = filev['electronic_name'][0]
                if url not in mapping:
                    mapping[url] = rec_id

    with open(mapping_file, "w") as f:
        w = csv.writer(f)
        w.writerows(mapping.items())

    return mapping


def build_usage(caltechdata_collection, usage_collection):
    """Build collection of records that contain CaltechDATA usage
    information"""
    if not os.path.isdir(usage_collection):
        ok = dataset.init(usage_collection)
        if ok == False:
            print("Dataset failed to init collection")
            exit()
        # Write date to start collecting statistics for new collection
        dataset.create(usage_collection, "end-date", {"end-date": 1485907200})
    # Build out structure for all CaltechDATA records
    ids = dataset.keys(caltechdata_collection)
    for k in ids:
        if dataset.has_key(usage_collection, k) == False:
            metadata, err = dataset.read(caltechdata_collection, k)
            # When record was submitted to CaltechDATA:
            rdate = None
            submitted = None
            issued = None
            for date in metadata["dates"]:
                if date["dateType"] == "Submitted":
                    rdate = date["date"]
                if date["dateType"] == "Updated":
                    submitted = date["date"]
                if date["dateType"] == "Issued":
                    issued = date["date"]
            if rdate == None:
                if submitted != None:
                    rdate = submitted
                else:
                    rdate = issued
            # Dataset is the only supported type in the spec and we are
            # following the dataset standards for usage
            # All dates are the date added to CaltechDATA, which is
            # the apropriate 'publication' date even if content was available
            # earlier
            record_data = {
                "dataset-id": [
                    {"type": "doi", "value": metadata["identifier"]["identifier"]}
                ],
                "uri": "https://data.caltech.edu/records/" + k,
                "publisher": "CaltechDATA",
                "platform": "CaltechDATA",
                "publisher-id": [{"type": "grid", "value": "grid.20861.3d"}],
                "yop": rdate.split("-")[0],
                "data-type": "dataset",
                "dataset-dates": [{"type": "pub-date", "value": rdate}],
                "dataset-title": metadata["titles"][0]["title"],
                "performance": [],
                "grand-total-unique-investigations": 0,
                "grand-total-unique-requests": 0,
            }
            err = dataset.create(usage_collection, k, record_data)
            if err != "":
                print(err)
                exit()


def process_visits(url, mapping, previous_visit=None):
    response = requests.get(url)
    if response.status_code != 200:
        print(response.text)
        print(url)
    visitors = {}
    merged_visits = {}
    for visit in response.json():
        # We need to group any visits within an hour
        vid = visit["visitorId"]
        visit_id = visit["idVisit"]
        # If this visitor has been here before
        if vid in visitors:
            delta = visitors[vid]["time"] - datetime.fromtimestamp(
                visit["firstActionTimestamp"]
            )
            minutes = int(delta.total_seconds() // 60)
            # Group anything within 60 minutes; may slightly over-combine
            if minutes <= 60:
                old_id = visitors[vid]["visit_id"]
                existing = merged_visits.pop(old_id)
                existing["actionDetails"] += visit["actionDetails"]
                # print(existing)
                merged_visits[old_id] = existing
            else:
                time = datetime.fromtimestamp(visit["firstActionTimestamp"])
                visitors[vid] = {"time": time, "visit_id": visit_id}
                merged_visits[visit_id] = visit
        else:
            time = datetime.fromtimestamp(visit["firstActionTimestamp"])
            visitors[vid] = {"time": time, "visit_id": visit_id}
            merged_visits[visit_id] = visit

    usage = []
    print(len(merged_visits))
    for visit_id in merged_visits:
        visit = merged_visits[visit_id]
        views = set()
        downloads = set()
        for action in visit["actionDetails"]:
            aurl = action["url"]
            if action["type"] == "action":
                if "/records/" in aurl:
                    recid = aurl.split("/records/")[1]
                    # We remove queries and discard other incorrect urls
                    recid = recid.split("?")[0]
                    if recid.isdigit() == True:
                        views.add(recid)
            elif action["type"] == "download":
                if aurl in mapping:
                    record = mapping[aurl]
                    downloads.add(record)
                else:
                    print("ERROR- Missing Url", aurl)
        use = {}
        if len(views) > 0:
            use["views"] = views
        if len(downloads) > 0:
            use["downloads"] = downloads
        if len(use) > 0:
            use["date"] = visit["serverDate"]
            usage.append(use)
    return usage


def get_usage(usage_collection, mapping, token):
    """Collect usage into a usage object for items in CaltechDATA"""

    # Find time periods
    datev, err = dataset.read(usage_collection, "end-date")
    new_start = datetime.fromtimestamp(datev["end-date"])
    now = datetime.now().timestamp()
    # minutes in range
    minutes_diff = math.ceil(
        (datetime.fromtimestamp(now) - new_start).total_seconds() / 60.0
    )

    # Get number of visitors since last harvest
    stats_url_base = "https://stats.tind.io/index.php?module=API&method=Live.getCounters&idSite=1161&format=JSON"

    token_s = "&token_auth=" + token

    stats_url = f"{stats_url_base}{token_s}&lastMinutes={minutes_diff}"
    response = requests.get(stats_url)
    if response.status_code != 200:
        print(response.text)
        print(stats_url)
    visitors = response.json()[0]["visits"]

    print(visitors)
    visit_url_base = "https://stats.tind.io/index.php?module=API&method=Live.getLastVisitsDetails&idSite=1161&format=json&filter_limit=1000"

    print("Getting usage")
    usage = []
    # We will page through visitors in chunks of 1000
    chunks = math.ceil(int(visitors) / 1000)
    if chunks > 1:
        url = visit_url_base + token_s + "&filter_limit=1000"
        process_visits(url, mapping)
        for c in progressbar(range(chunks)):
            url = f"{visit_url_base}{token_s}&filter_limit=1000&filter_offset={c*1000}"
            usage += process_visits(url, mapping)
    else:
        url = f"{visit_url_base}{token_s}&filter_limit={visitors}"
        usage = process_visits(url, mapping)

    print("Writing usage")
    for use in progressbar(usage):
        date = use["date"]
        if "downloads" in use and "views" in use:
            records = use["views"].union(use["downloads"])
        elif "views" in use:
            records = use["views"]
        else:
            records = use["downloads"]
        for rec in records:
            data, err = dataset.read(usage_collection, rec)
            if err == "":
                # We only track usage from live records
                instance = {"instance": [], "period": date}
                if "views" in use:
                    if rec in use["views"]:
                        instance["instance"].append(
                            {
                                "access-method": "regular",
                                "count": 1,
                                "metric-type": "unique-dataset-investigations",
                            }
                        )
                        # print(data,rec)
                        data["grand-total-unique-investigations"] += 1
                if "downloads" in use:
                    if rec in use["downloads"]:
                        instance["instance"].append(
                            {
                                "access-method": "regular",
                                "count": 1,
                                "metric-type": "unique-dataset-requests",
                            }
                        )
                        data["grand-total-unique-requests"] += 1
                data["performance"].append(instance)
                dataset.update(usage_collection, rec, data)

    dataset.update(usage_collection, "end-date", {"end-date": now})


def makereport(collection, start_date, end_date):

    # Find time periods
    datev, err = dataset.read(usage_collection, "end-date")
    new_start = datetime.fromisoformat(datev["end-date"])
    # Always start at the beginning of a month
    if new_start.day != 1:
        new_start = str(new_start.year) + "-" + str(new_start.month) + "-01"
    today = datetime.today().date().isoformat()
    start_list = (
        pd.date_range(new_start, today, freq="MS").strftime("%Y-%m-%d").to_list()
    )
    end_list = pd.date_range(new_start, today, freq="M").strftime("%Y-%m-%d").to_list()
    # If today isn't the last day in the month, add end date
    if len(start_list) == len(end_list) + 1:
        end_list.append(today)

    for i in range(len(start_list)):
        end_date = datetime.fromisoformat(end_list[i])
        print("Collecting usage from ", start_list[i], " to", end_list[i])
        token_s = "&token_auth=" + token
        view_url = (
            view_url_base + "&date=" + start_list[i] + "," + end_list[i] + token_s
        )
        dl_url = dl_url_base + "&date=" + start_list[i] + "," + end_list[i] + token_s
        # Build report structure
        report = {
            "report-header": {
                "report-name": "dataset report",
                "report-id": "DSR",
                "release": "rd1",
                "report-filters": [],
                "report-attributes": [],
                "exceptions": [],
                "created-by": "Caltech Library",
                "created": today,
                "reporting-period": {
                    "begin-date": start_list[i],
                    "end-date": end_list[i],
                },
            },
            "report-datasets": [],
        }

        print("Collecting downloads")
        aggr_downloads = {}
        for m in progressbar(mapping):
            record_date = record_dates[mapping[m]]
            # report_data,err = dataset.read(usage_collection,mapping[m])
            # record_date = datetime.fromisoformat(report_data['begin-date'])
            # If the record existed at this date
            if record_date < end_date:
                # Handle old URL-might not be needed depending on mapping
                d_url = m
                if end_date < datetime.fromisoformat("2017-06-01"):
                    if "caltechdata.tind.io" not in m:
                        d_url = (
                            "https://caltechdata.tind.io"
                            + m.split("data.caltech.edu")[1]
                        )
                url = dl_url + "&downloadUrl=" + d_url
                response = requests.get(url)
                if response.status_code != 200:
                    print(response.text)
                    print(dl_url)
                r_data = response.json()
                recid = mapping[m]
                if r_data != []:
                    downloads = r_data[0]["nb_visits"]
                    if recid in aggr_downloads:
                        aggr_downloads[recid] += downloads
                    else:
                        aggr_downloads[recid] = downloads
                else:
                    if recid not in aggr_downloads:
                        aggr_downloads[recid] = 0
        print("Collecting views")
        for k in progressbar(ids):
            performance = {
                "period": {"begin-date": start_list[i], "end-date": end_list[i]},
                "instance": [],
            }
            # report_data,err = dataset.read(usage_collection,k)
            # record_date = datetime.fromisoformat(report_data['begin-date'])
            record_date = record_dates[k]
            metadata, err = dataset.read(caltechdata_collection, k)
            # If the record existed at this date
            if record_date < end_date:
                url = view_url + "&pageUrl=https://data.caltech.edu/records/" + k
                response = requests.get(url)
                r_data = response.json()
                if r_data != []:
                    visits = r_data[0]["nb_visits"]
                else:
                    visits = 0
                entry = {
                    "count": visits,
                    "metric-type": "unique-dataset-investigations",
                    "access-method": "regular",
                }
                performance["instance"].append(entry)
                # Also add downloads to structure
                if k in aggr_downloads:
                    entry = {
                        "count": aggr_downloads[k],
                        "metric-type": "unique-dataset-requests",
                        "access-method": "regular",
                    }
                performance["instance"].append(entry)
                # Save to report
                report_data = {
                    "dataset-id": [
                        {"type": "doi", "value": metadata["identifier"]["identifier"]}
                    ],
                    "uri": "https://data.caltech.edu/records/" + k,
                    "publisher": "CaltechDATA",
                    "platform": "CaltechDATA",
                    "publisher-id": [{"type": "grid", "value": "grid.20861.3d"}],
                    "yop": metadata["publicationYear"],
                    "data-type": metadata["resourceType"][
                        "resourceTypeGeneral"
                    ].lower(),
                    "dataset-dates": [
                        {"type": "pub-date", "value": record_date.isoformat()}
                    ],
                    "dataset-title": metadata["titles"][0]["title"],
                    "performance": [performance],
                }
                report["report-datasets"].append(report_data)
        rname = start_list[i] + "/" + end_list[i]
        if dataset.has_key(usage_collection, rname):
            err = dataset.update(usage_collection, rname, report)
        else:
            err = dataset.create(usage_collection, rname, report)
        if err != "":
            print(err)
            exit()
        dataset.update(usage_collection, "end-date", {"end-date": end_list[i]})
