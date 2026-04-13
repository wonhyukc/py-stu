import os
import sys
from datetime import datetime
import csv
import io
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bin import extract_06_emails

def generate_robust_mock_emails(name_to_id, id_to_track):
    import random
    random.seed(42) # Reproducible robust tests
    
    mock_emails_all = []
    mock_emails_att = []
    
    student_ids = list(id_to_track.keys())
    
    # 1. Generate normal valid 0.6 emails for 30 students (2 points)
    for i in range(30):
        s_id = student_ids[i]
        mock_emails_all.append({
            "message_id": f"msg_valid_{i}",
            "subject": f"과제 0.6 [{s_id}]",
            "date_str": "Mon, 13 Apr 2026 08:30:00 +0900",
            "sender": f"Student{s_id} <student{s_id}@test.com>"
        })
        
    # 2. Generate assignment 0.6 with ID but HAS ATTACHMENT (1 point) -> 10 students
    for i in range(30, 40):
        s_id = student_ids[i]
        msg = {
            "message_id": f"msg_att_{i}",
            "subject": f"assignment 0.6 ({s_id})",
            "date_str": "Sun, 12 Apr 2026 15:30:00 +0900",
            "sender": f"Student{s_id} <student{s_id}@test.com>"
        }
        mock_emails_all.append(msg)
        mock_emails_att.append(msg)
        
    # 3. Generate missing ID in subject but mapped via name (1 point) -> 5 students
    for i in range(40, 45):
        s_id = student_ids[i]
        # To map it, we must use a real known name
        real_name = next(k for k,v in name_to_id.items() if v == s_id)
        mock_emails_all.append({
            "message_id": f"msg_noid_{i}",
            "subject": f"과제 0.6 제출합니다",
            "date_str": "Sun, 12 Apr 2026 09:30:00 +0900",
            "sender": f"{real_name} <student{s_id}@test.com>"
        })
        
    # 4. Generate completely wrong format "과제 0.5" but within timeframe -> mapped (0 point) -> 5 students
    for i in range(45, 50):
        s_id = student_ids[i]
        mock_emails_all.append({
            "message_id": f"msg_wrong_{i}",
            "subject": f"과제 0.5 [{s_id}]",
            "date_str": "Mon, 13 Apr 2026 08:30:00 +0900",
            "sender": f"Student{s_id} <student{s_id}@test.com>"
        })
        
    # 5. Generate unknown student (0 points)
    mock_emails_all.append({
        "message_id": "msg_unknown1",
        "subject": "과제 0.6 [9999999999]",
        "date_str": "Mon, 13 Apr 2026 08:00:00 +0900",
        "sender": "Unknown <unknown@test.com>"
    })
    
    # 6. Generate Google Docs Spam (0 points/Excluded)
    mock_emails_all.append({
        "message_id": "msg_spam1",
        "subject": "Document was edited recently",
        "date_str": "Mon, 13 Apr 2026 08:00:00 +0900",
        "sender": "docs <comments-noreply@docs.google.com>"
    })
    
    # 7. Generate purely personal email (0 points/Excluded)
    mock_emails_all.append({
        "message_id": "msg_personal1",
        "subject": "안녕하세요 교수님 질문있습니다",
        "date_str": "Mon, 13 Apr 2026 08:00:00 +0900",
        "sender": "gildong <gildong@test.com>"
    })
    
    # Total valid to process should be: 30(2) + 10(1) + 5(1) + 5(0) + 1(unknown->0) = 51 in output CSV
    
    return mock_emails_all, mock_emails_att

def test_extract_06_emails():
    # Load actual students to ensure edge cases work with thousands of mappings
    from bin.extract_06_emails import parse_students
    real_name_to_id, real_id_to_track = parse_students()
    
    if len(real_id_to_track) < 50:
        print(f"Warning: Only {len(real_id_to_track)} students found. Test might fail due to index errors.")
        return
        
    mock_emails_all, mock_emails_att = generate_robust_mock_emails(real_name_to_id, real_id_to_track)
    
    def side_effect_fetch(query, max_results=1000):
        if "has:attachment" in query:
            return mock_emails_att
        return mock_emails_all
    
    with patch("bin.extract_06_emails.fetch_assignment_emails", side_effect=side_effect_fetch):
        extract_06_emails.main()
        
        assert os.path.exists("output/mail06.csv")
        with open("output/mail06.csv", "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            
            print(f"\\n--- Verification Results ---")
            print(f"Total emails injected into mock stream: {len(mock_emails_all)}")
            print(f"Total rows correctly written to CSV (filtered): {len(reader)}")
            
            count_2 = sum(1 for row in reader if row["점수"] == "2")
            count_1 = sum(1 for row in reader if row["점수"] == "1")
            count_0 = sum(1 for row in reader if row["점수"] == "0")
            
            print(f"- 2 points (Perfect format, no attach): {count_2} (Expected: 30)")
            print(f"- 1 points (Format violation / attachment): {count_1} (Expected: 15)")
            print(f"- 0 points (Wrong week / Unknown ID): {count_0} (Expected: 6)")
            print(f"Total expected processed: 51")
            
            assert len(reader) == 51
            assert count_2 == 30
            assert count_1 == 15
            assert count_0 == 6
            print("=> All counts matched perfectly!")

if __name__ == '__main__':
    test_extract_06_emails()
