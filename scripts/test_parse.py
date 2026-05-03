import csv

file_path = "/data/hyuk/prj/stu/stu2603/web-output/wb08/웹프로그래밍(E트랙)(2026년도, 1학기, CCS762, 02, U)-Mid-term eval 15 -a-responses.csv"  # noqa: E501

from typing import List, Dict, Any

results: List[Dict[str, Any]] = []
with open(file_path, newline="", encoding="utf-8-sig") as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)

    for row in reader:
        student_id = row[2]
        completed_time = row[8]

        gemini_links = []
        for i, val in enumerate(row):
            if "gemini.google.com/share" in val:
                gemini_links.append((headers[i], val))

        if gemini_links:
            results.append(
                {
                    "student_id": student_id,
                    "completed_time": completed_time,
                    "links": gemini_links,
                }
            )

all_same_column = True
first_col = None

with open("gemini_results.csv", "w", newline="", encoding="utf-8-sig") as out_csv:
    writer = csv.writer(out_csv)
    writer.writerow(["Student ID", "Completed Time", "Column", "Links"])

    for res in results:
        student_id = res["student_id"]
        completed = res["completed_time"]
        for col, link in res["links"]:  # type: ignore
            if first_col is None:
                first_col = col
            if col != first_col:
                all_same_column = False

            # Print to stdout
            print(f"Student ID: {student_id}, Completed: {completed}, Column: {col}")
            print(f"Links:\n{link}")
            print("-" * 40)

            # Write to CSV
            writer.writerow([student_id, completed, col, link])

print(f"\nAll submitted in the same column? {'Yes' if all_same_column else 'No'}")
