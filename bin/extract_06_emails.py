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
                            clean_eng = re.sub(r"\s+", "", eng_name).lower()
                            if clean_eng:
                                name_to_id[clean_eng] = student_id
                            clean_kor = re.sub(r"\s+", "", kor_name)
                            if clean_kor:
                                name_to_id[clean_kor] = student_id

                            email_addr = cols[5].lower()
                            name_to_id[email_addr] = student_id
    return name_to_id, id_to_track

def main():
    name_to_id, id_to_track = parse_students()
    
    KST = timezone(timedelta(hours=9))
    deadline_06 = datetime(2026, 4, 13, 9, 0, tzinfo=KST)
    
    print("Fetching emails for assignment 0.6...")
    # Add strong rules for fetching
    new_emails = fetch_assignment_emails("after:2026/04/01 (과제 OR assignment) 0.6", max_results=500)
    
    # rule: 과제 or assignment 0.x (specifically 0.6)
    strict_re = re.compile(r"(과제|assignment)\s*0?\.6(?:(?:\[|\()?(\d{10})(?:\]|\))?)?")
    
    new_rows = []
    
    for email_data in new_emails:
        subject = email_data["subject"].strip()
        date_str = email_data["date_str"].strip()
        sender = email_data["sender"].strip()
        
        email_dt = None
        try:
            email_dt = email.utils.parsedate_to_datetime(date_str)
            if email_dt.tzinfo is None:
                email_dt = email_dt.replace(tzinfo=timezone.utc).astimezone(KST)
            else:
                email_dt = email_dt.astimezone(KST)
        except Exception:
            pass
            
        # Only within deadline
        if email_dt is None or email_dt > deadline_06:
            continue
            
        # Strict naming: 과제 or assignment 0.6
        clean_sub = re.sub(r"\s+", "", subject.lower())
        m = strict_re.search(clean_sub)
        if not m:
            continue
            
        est_id = m.group(2) if len(m.groups()) >= 2 and m.group(2) else ""
        if not est_id:
            sender_name = sender.split("<")[0].strip()
            clean_name = re.sub(r"\s+", "", sender_name).lower()
            if clean_name in name_to_id:
                est_id = name_to_id[clean_name]
            else:
                m_id = re.search(r"\d{10}", subject)
                if m_id:
                    est_id = m_id.group(0)
                    
        row = {
            "학번": est_id,
            "추정하는학번": est_id,
            "track": id_to_track.get(est_id, ""),
            "점수": 1,
            "유형": "0.6",
            "이유": "제목양식(+1) 기한내(+1)",
            "날짜": date_str,
            "이름": sender.split("<")[0].strip(),
            "메일제목": subject,
        }
        
        new_rows.append(row)
        
    print(f"Found {len(new_rows)} emails for 0.6.")
    
    if new_rows:
        os.makedirs("output", exist_ok=True)
        fieldnames = ["학번", "추정하는학번", "track", "점수", "유형", "이유", "날짜", "이름", "메일제목"]
        with open("output/mail06.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(new_rows)
        print("Saved to output/mail06.csv")
    else:
        print("No valid emails found to save.")

if __name__ == "__main__":
    main()
