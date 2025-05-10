from ames.matchers.caltechauthors import process_link_updates
import csv

input_file = "non_publisher_links.csv"
output_file = "test_results_update_links.csv"

results = process_link_updates(input_file)

if results:
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved update results to {output_file}")
else:
    print("No results.")
