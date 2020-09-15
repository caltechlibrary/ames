import os, csv, math, shutil, calendar
import requests
import pandas as pd
from datetime import datetime
from progressbar import progressbar
from py_dataset import dataset
from ames.harvesters import get_records


def file_mapping(source_collection):
    """Return a dictionary that maps /tindfiles/serve urls to records."""

    mapping = {}

    dot_paths = [".electronic_location_and_access", "._Key"]
    keys = dataset.keys(source_collection)
    metadata = get_records(dot_paths, "files", source_collection, keys)

    for record in metadata:
        # Handle history records where the key is the item and revision
        k = record["_Key"]
        if "-" in k:
            rec_id = k.split("-")[0]
        else:
            rec_id = k

        # Ignore embargoed records
        if "electronic_location_and_access" in record:
            for filev in record["electronic_location_and_access"]:
                url = filev["uniform_resource_identifier"]
                # name = filev['electronic_name'][0]
                if url not in mapping:
                    mapping[url] = rec_id

    return mapping


def build_usage(caltechdata_collection, usage_collection):
    """Build collection of records that contain CaltechDATA usage
    information"""
    if not os.path.isdir(usage_collection):
        if not dataset.init(usage_collection):
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
            if "dates" in metadata:
                doi = metadata["identifier"]["identifier"]
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
            else:
                # Dummy values for junk records
                rdate = "2020-04-01"
                doi = ""
            # Dataset is the only supported type in the spec and we are
            # following the dataset standards for usage
            # All dates are the date added to CaltechDATA, which is
            # the apropriate 'publication' date even if content was available
            # earlier
            record_data = {
                "dataset-id": [{"type": "doi", "value": doi}],
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
            if not dataset.create(usage_collection, k, record_data):
                err = dataset.error_message()
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


def build_aggregate(collection):
    """Build a collection for usage by month.
    Always creates collection from scratch"""
    # Delete existing collection
    if os.path.isdir(collection):
        shutil.rmtree(collection)
    if not dataset.init(collection):
        print("Dataset failed to init collection")
        exit()

    # Find time periods
    start = datetime.fromisoformat("2017-01-01")
    today = datetime.today().date().isoformat()
    date_list = pd.date_range(start, today, freq="MS").strftime("%Y-%m").to_list()

    for month in date_list:
        if not dataset.create(collection, month, {"report-datasets": []}):
            err = dataset.error_message()
            print(err)


def get_month_day_range(date):
    """
    From fletom https://gist.github.com/waynemoore/1109153
    For a date 'date' returns the start and end date for the month of 'date'.

    Month with 31 days:
    >>> date = datetime.date(2011, 7, 27)
    >>> get_month_day_range(date)
    (datetime.date(2011, 7, 1), datetime.date(2011, 7, 31))

    Month with 28 days:
    >>> date = datetime.date(2011, 2, 15)
    >>> get_month_day_range(date)
    (datetime.date(2011, 2, 1), datetime.date(2011, 2, 28))
    """
    first_day = date.replace(day=1)
    last_day = date.replace(day=calendar.monthrange(date.year, date.month)[1])
    return first_day, last_day


def aggregate_usage(usage_collection, month_collection):
    keys = dataset.keys(usage_collection)
    keys.remove("end-date")
    for k in progressbar(keys):
        record, err = dataset.read(usage_collection, k)
        if err != "":
            print(err)
        use = {}
        views = {}
        for usage in record["performance"]:
            split = usage["period"].split("-")
            month = split[0] + "-" + split[1]
            for u in usage["instance"]:
                metric = u["metric-type"]
                if metric == "unique-dataset-requests":
                    if month in use:
                        use[month] += u["count"]
                    else:
                        use[month] = u["count"]
                if metric == "unique-dataset-investigations":
                    if month in views:
                        views[month] += u["count"]
                    else:
                        views[month] = u["count"]
        # Strip non-counter stuff
        record.pop("_Key")
        record.pop("grand-total-unique-requests")
        record.pop("grand-total-unique-investigations")
        # go across months
        for view in views:
            split = view.split("-")
            date_obj = datetime(int(split[0]), int(split[1]), 1)
            d_range = get_month_day_range(date_obj)
            performance = [
                {
                    "period": {
                        "begin-date": d_range[0].date().isoformat(),
                        "end-date": d_range[1].date().isoformat(),
                    },
                    "instance": [],
                }
            ]
            v = views[view]
            performance[0]["instance"].append(
                {
                    "count": v,
                    "metric-type": "unique-dataset-investigations",
                    "access-method": "regular",
                }
            )
            # Handle when we have both views and uses in a given month
            if view in use:
                u = use[view]
                performance[0]["instance"].append(
                    {
                        "count": u,
                        "metric-type": "unique-dataset-requests",
                        "access-method": "regular",
                    }
                )
            existing, err = dataset.read(month_collection, view)
            if err != "":
                print(err)
            record["performance"] = performance
            existing["report-datasets"].append(record)
            if not dataset.update(month_collection, view, existing):
                err = dataset.error_message()
                print(err)
        for use_date in use:
            # We only have use-only records left to handle
            if use_date not in views:
                u = use[use_date]
                split = use_date.split("-")
                date_obj = datetime(int(split[0]), int(split[1]), 1)
                d_range = get_month_day_range(date_obj)
                performance = [
                    {
                        "period": {
                            "begin-date": d_range[0].date().isoformat(),
                            "end-date": d_range[1].date().isoformat(),
                        },
                        "instance": [
                            {
                                "count": u,
                                "metric-type": "unique-dataset-requests",
                                "access-method": "regular",
                            }
                        ],
                    }
                ]
                existing, err = dataset.read(month_collection, view)
                if err != "":
                    print(err)
                record["performance"] = performance
                existing["report-datasets"].append(record)
                if not dataset.update(month_collection, view, existing):
                    err = dataset.error_message()
                    print(err)
