import os
from datetime import datetime, timedelta
from py_dataset import dataset
from ames.harvesters import file_mapping, get_usage, build_usage
from ames.harvesters import build_aggregate, aggregate_usage
from ames.harvesters import get_caltechdata, get_history
from ames.matchers import add_usage, submit_report

if os.path.isdir("data") == False:
    os.mkdir("data")
os.chdir("data")

production = True
collection = "caltechdata.ds"

files = True

if files:
    get_caltechdata(collection, production)
    mapping = file_mapping(collection)

history = True

if history:
    keys = dataset.keys(collection)
    h_collection = "caltechdata_history.ds"
    get_history(h_collection, collection, keys)
    mapping = file_mapping(h_collection)

update = True

usage_collection = "caltechdata_usage.ds"
if update:
    token = os.environ["MATTOK"]
    build_usage(collection, usage_collection)
    get_usage(usage_collection, mapping, token)
    token = os.environ["TINDTOK"]
    add_usage(collection, token, usage_collection, production)

aggregate = True

# Aggregrate usage into month buckets
month_collection = "caltechdata_aggregate.ds"
if aggregate:
    build_aggregate(month_collection)
    aggregate_usage(usage_collection, month_collection)

# keys = dataset.keys(month_collection)
today = datetime.today()
last_month = today.replace(day=1) - timedelta(days=1)
keys = [f"{last_month.year}-{last_month.month:02}"]
token = os.environ["DATACITE_TOKEN"]
submit_report(
    month_collection, keys, token, production, ["10.14291", "10.7907", "10.7909"]
)
token = os.environ["DATACITE_TIND_TOKEN"]
submit_report(month_collection, keys, token, production, ["10.22002"], "CaltechDATA")
