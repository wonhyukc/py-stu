import csv
import os

input_file = "/home/hyuk/nvme_data/prj/stu/eval/students_all - all_채점.csv"
tracks = ["468", "761", "762"]

# Open 6 files for writing
files = {}
writers = {}

for t in tracks:
    files[(t, "과제")] = open(
        f"/home/hyuk/nvme_data/prj/stu/eval/track_{t}_과제.csv",
        "w",
        newline="",
        encoding="utf-8-sig",
    )
    writers[(t, "과제")] = csv.writer(files[(t, "과제")])

    files[(t, "수업참여")] = open(
        f"/home/hyuk/nvme_data/prj/stu/eval/track_{t}_수업참여.csv",
        "w",
        newline="",
        encoding="utf-8-sig",
    )
    writers[(t, "수업참여")] = csv.writer(files[(t, "수업참여")])

with open(input_file, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    header = next(reader)

    # write headers
    for w in writers.values():
        w.writerow(header)

    for row in reader:
        if not row:
            continue
        # track is at index 3
        track = row[3].strip() if len(row) > 3 else ""
        if track.endswith(".0"):
            track = track[:-2]

        if track not in tracks:
            continue

        # yuhyeong is at index 5
        yuhyeong = row[5].strip() if len(row) > 5 else ""

        cat = "수업참여" if yuhyeong == "수업참여" else "과제"

        writers[(track, cat)].writerow(row)

for f in files.values():
    f.close()

print("CSV files successfully split into 6 files.")
