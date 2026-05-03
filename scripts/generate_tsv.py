import csv
import os
from typing import Dict

tracks = ["468", "761", "762"]
categories = ["과제", "수업참여"]

for track in tracks:
    for cat in categories:
        input_csv = f"/home/hyuk/nvme_data/prj/stu/eval/track_{track}_{cat}.csv"
        output_tsv = (
            f"/home/hyuk/nvme_data/prj/stu/eval/moodle_score_track_{track}_{cat}.tsv"
        )

        scores: Dict[str, float] = {}

        try:
            with open(input_csv, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # student id
                    student_id = row.get("추정하는학번", "").strip()
                    if not student_id:
                        student_id = row.get("학번", "").strip()
                    if not student_id:
                        continue

                    # score
                    score_str = row.get("점수", "").strip()
                    try:
                        score = float(score_str)
                    except ValueError:
                        score = 0.0

                    scores[student_id] = scores.get(student_id, 0.0) + score

            with open(output_tsv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(["id", "score"])
                for sid, total_score in scores.items():
                    writer.writerow([sid, round(total_score, 2)])
        except FileNotFoundError:
            print(f"File not found: {input_csv}")

print("TSV files created successfully.")
