import re

input_file = "output/wb02-mid.md"
output_file = "output/tmp.md"

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

output_lines = []
output_lines.append("# 중간고사 평가 결과 (요약)\n")
output_lines.append("| Student ID | 성적 | 코멘트 |\n")
output_lines.append("| :--- | :--- | :--- |\n")

for line in lines:
    line = line.strip()
    if not line or not line.startswith("|"):
        continue
    if "Student ID" in line or "---" in line:
        continue

    parts = [p.strip() for p in line.split("|")]
    if len(parts) >= 8 and parts[2].isdigit():
        student_id = parts[2]
        memo = parts[7]

        # Extract score from memo, e.g. "(4점)" -> "4"
        match = re.search(r"\((\d+)점\)", memo)
        score = match.group(1) if match else ""

        # We can just put the whole memo in the comment, or clean it up.
        # Let's put the extracted score and the full memo.
        output_lines.append(f"| {student_id} | {score} | {memo} |\n")

with open(output_file, "w", encoding="utf-8") as f:
    f.writelines(output_lines)

print(f"Generated {output_file}")
