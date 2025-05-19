from ames.harvesters.caltechauthors import get_data_availability_links
import csv
import os

output_file = "test_results_get_links.csv"
token = os.environ.get("RDMTOK")
results = get_data_availability_links(token=token)

if results:
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved {len(results)} links to {output_file}")
else:
    print("No results.")
