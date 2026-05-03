import csv
import sys

input_file = "output/wb01-mid.csv"
output_file = "output/wb01-mid.csv"

rows = []
with open(input_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    # The columns we want are "ID number" (index 2) and the last column "Response 16" (index -1)

    # We will rename the headers for clarity
    rows.append(["Student ID", "Links"])

    for row in reader:
        if len(row) >= 3:
            student_id = row[2]
            link = row[-1]
            rows.append([student_id, link])

with open(output_file, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print(f"Processed {len(rows)-1} students.")
