import os, csv
from ames.harvesters import get_pending_requests
from ames.matchers import add_journal_metadata

token = os.environ["CTATOK"]

community = "aedd135f-227e-4fdf-9476-5b3fd011bac6"

completed = []
with open("completed_requests.csv", "r") as f:
    reader = csv.reader(f)
    for row in reader:
        completed.append(row[0])

pending = get_pending_requests(token, community)
for p in pending:
    if p not in completed:
        add_journal_metadata(p, token)
        completed.append(p)

with open("completed_requests.csv", "w") as f:
    writer = csv.writer(f)
    for c in completed:
        writer.writerow([c])
