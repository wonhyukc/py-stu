import re
import csv
import os

input_file = "output/wb02-mid.md"
output_file = "output/moodle-wb02-scores.csv"

scores = []
with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 8 and parts[2].isdigit():
            student_id = parts[2]
            memo = parts[7]
            # Extract score from memo, e.g. "(4점)" -> "4"
            match = re.search(r"\((\d+)점\)", memo)
            if match:
                score = match.group(1)
                scores.append({"id": student_id, "score": score})

with open(output_file, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "score"])
    writer.writeheader()
    writer.writerows(scores)

print(f"Generated {output_file} with {len(scores)} records.")
