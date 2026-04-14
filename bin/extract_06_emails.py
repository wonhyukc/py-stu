import sys
import os
import csv
import re
from datetime import datetime, timezone, timedelta
import email.utils

sys.path.append(os.getcwd())
from modules.mail_fetcher import fetch_assignment_emails


def parse_students():
    name_to_id = {}
    id_to_track = {}
    id_to_names = {}
    for filepath in ["input/students/py-students.md", "input/students/wb-students.md"]:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line.startswith("|") or "---" in line or "학번" in line:
                        continue
                    cols = [c.strip() for c in line.split("|")]
                    if len(cols) > 8:
                        track = cols[1]
                        student_id = cols[3]
                        eng_name = cols[4]
                        kor_name = cols[8]

                        if student_id.isdigit():
                            id_to_track[student_id] = track
                            id_to_names[student_id] = {"eng": eng_name, "kor": kor_name}

                            clean_eng = re.sub(r"\s+", "", eng_name).lower()
                            if clean_eng:
                                name_to_id[clean_eng] = student_id
                            clean_kor = re.sub(r"\s+", "", kor_name)
                            if clean_kor:
                                name_to_id[clean_kor] = student_id

                            email_addr = cols[5].lower()
                            name_to_id[email_addr] = student_id
    return name_to_id, id_to_track, id_to_names


def main():
    name_to_id, id_to_track, id_to_names = parse_students()

    KST = timezone(timedelta(hours=9))
    start_dt = datetime(2026, 4, 6, 9, 0, tzinfo=KST)
    deadline_06 = datetime(2026, 4, 13, 9, 0, tzinfo=KST)

    print("Fetching emails from 2026/04/06 09:00 to 2026/04/13 09:00...")
    search_base = (
        "after:2026/04/05 before:2026/04/14 -from:comments-noreply@docs.google.com"
    )
    new_emails = fetch_assignment_emails(search_base, max_results=1000)

    emails_with_att = fetch_assignment_emails(
        search_base + " has:attachment", max_results=1000
    )
    att_msg_ids = set(e["message_id"] for e in emails_with_att)

    # rule: 과제 or assignment 0.x (학번 필수 - 10자리 숫자)
    strict_re = re.compile(r"(과제|assignment)\s*0?\.6\s*(?:\[|\()?(\d{10})(?:\]|\))?")
    any_assignment_re = re.compile(r"(과제|assignment|0?\.6)")

    new_rows = []

    for email_data in new_emails:
        subject = email_data["subject"].strip()
        date_str = email_data["date_str"].strip()
        sender = email_data["sender"].strip()
        msg_id = email_data["message_id"]
        has_att = msg_id in att_msg_ids

        email_dt = None
        try:
            email_dt = email.utils.parsedate_to_datetime(date_str)
            if email_dt.tzinfo is None:
                email_dt = email_dt.replace(tzinfo=timezone.utc).astimezone(KST)
            else:
                email_dt = email_dt.astimezone(KST)
        except Exception:
            pass

        # Ignore if missing date
        if email_dt is None:
            continue

        # Rule 1: Limit strictly to Last Mon 09:00 - Today 09:00
        if not (start_dt <= email_dt <= deadline_06):
            continue

        # Rule 2 & 3: Blacklist strings
        subject_lower = subject.lower()
        if "was edited" in subject_lower:
            continue
        if "comments-noreply@docs.google.com" in sender.lower():
            continue

        clean_sub = re.sub(r"\s+", "", subject_lower)
        m_strict = strict_re.search(clean_sub)

        # Determine Student ID (Est ID) First
        # If strict matches, it has the ID in group 2
        est_id = m_strict.group(2) if m_strict else ""
        if not est_id:
            sender_name = sender.split("<")[0].strip()
            clean_name = re.sub(r"\s+", "", sender_name).lower()
            if clean_name in name_to_id:
                est_id = name_to_id[clean_name]
            else:
                m_id = re.search(r"\d{10}", subject)
                if m_id:
                    est_id = m_id.group(0)

        # Check if it even is an assignment (filter out pure personal/spam emails)
        if not any_assignment_re.search(clean_sub) and not est_id:
            continue

        # Determine Point & Type
        score = 0
        reason = "수동 확인 요망(양식불일치/타주차)"
        task_type = "기타"

        # Rule: 학생을 찾을 수 없으면 0점 처리
        if not est_id or est_id not in id_to_track:
            score = 0
            reason = "학번 식별 불가"
            task_type = "기타"
        else:
            task_type = "0.6"  # It's matched to a student within the assignment block
            # Rule: 0.6 strict match AND no attachments -> 2 points
            if m_strict and not has_att:
                score = 2
                reason = "정확한 양식/첨부없음(+2)"
            elif any_assignment_re.search(clean_sub):
                # Check if it mentions explicitly a DIFFERENT week (e.g. 0.5, 0.4, 0.7)
                diff_week_match = re.search(r"0?\.([0-57-9])", clean_sub)
                is_this_week = "0.6" in clean_sub or not diff_week_match

                if is_this_week:
                    # Valid but rule violated (missing ID in subject, has attachment, or just says "과제/0.6")
                    score = 1
                    violations = []
                    if not m_strict:
                        violations.append("양식오류")
                    if has_att:
                        violations.append("첨부있음")
                    reason = f"양식위반({','.join(violations)}) (+1)"
                else:
                    # Mentions another week explicitly
                    score = 0
                    reason = "타주차 과제(수동확인)"
                    task_type = "기타"

        row = {
            "학번": est_id,
            "추정하는학번": est_id,
            "track": id_to_track.get(est_id, ""),
            "점수": score,
            "유형": task_type,
            "이유": reason,
            "날짜": date_str,
            "이름": sender.split("<")[0].strip(),
            "메일제목": subject,
        }

        new_rows.append(row)

    print(f"Found {len(new_rows)} relevant emails in the specified range.")

    if new_rows:
        os.makedirs("output", exist_ok=True)
        fieldnames = [
            "학번",
            "추정하는학번",
            "track",
            "점수",
            "유형",
            "이유",
            "날짜",
            "이름",
            "메일제목",
        ]
        with open("output/mail06.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(new_rows)
        print("Saved to output/mail06.csv")
    else:
        print("No valid emails found to save.")


if __name__ == "__main__":
    main()
