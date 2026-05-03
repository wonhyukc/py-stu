import csv
import collections
import os

input_file = "/home/hyuk/nvme_data/prj/stu/eval/python - score.csv"

# Moodle Paste from spreadsheet 기능을 위한 설정
SCORE_ITEM_NAME = "week07"


def convert_scores(csv_path):
    # 트랙별 데이터 저장: track -> { student_id: total_score }
    track_scores = collections.defaultdict(lambda: collections.defaultdict(float))

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            student_id = row["학번"].strip()
            if not student_id:
                continue

            # 점수 파싱 (문자열 등 예외 처리)
            try:
                score = float(row["점수"])
            except ValueError:
                score = 0.0

            # 파일의 모든 데이터를 K-track Python (481) 트랙으로 강제 지정
            track = "481"

            track_scores[track][student_id] += score

    # 트랙별로 결과 파일 생성 (복사-붙여넣기 용이하도록 tsv 포맷 및 탭 구분자 사용)
    for track, scores in track_scores.items():
        output_filename = f"moodle_score_track_{track}.tsv"
        output_path = os.path.join(os.path.dirname(csv_path), output_filename)

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["id", "score"])
            for student_id, total_score in sorted(scores.items()):
                # 소수점 둘째 자리까지 표현
                writer.writerow([student_id, f"{total_score:.2f}"])

        print(
            f"[{track} 트랙] {len(scores)}명의 성적 데이터가 {output_filename}에 저장되었습니다."
        )


if __name__ == "__main__":
    convert_scores(input_file)
