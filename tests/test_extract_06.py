import os
import sys
from datetime import datetime
import csv
import io
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bin import extract_06_emails

def test_extract_06_emails():
    # Mock students
    mock_name_to_id = {"gildong": "2026111111", "hyanglin": "2026222222"}
    mock_id_to_track = {"2026111111": "py", "2026222222": "wb"}
    
    # Mock emails
    mock_emails_all = [
        # Valid: strict subject, on time, no attachment -> 2 points
        {
            "message_id": "msg1",
            "subject": "과제 0.6 [2026111111]",
            "date_str": "Mon, 13 Apr 2026 08:30:00 +0900",
            "sender": "gildong <gildong@test.com>"
        },
        # Violate 1: strict subject but HAS attachment -> 1 point
        {
            "message_id": "msg2",
            "subject": "assignment 0.6 [2026222222]",
            "date_str": "Mon, 13 Apr 2026 08:59:59 +0900",
            "sender": "hyanglin <hyanglin@test.com>"
        },
        # Violate 2: missing ID in subject, no attachment, mapped -> 1 point
        {
            "message_id": "msg3",
            "subject": "과제 0.6",
            "date_str": "Mon, 13 Apr 2026 08:00:00 +0900",
            "sender": "gildong <gildong@test.com>"
        },
        # Violate 3: no ID, no mapped student -> 0 points
        {
            "message_id": "msg4",
            "subject": "과제 0.6",
            "date_str": "Mon, 13 Apr 2026 08:00:00 +0900",
            "sender": "unknown <unknown@test.com>"
        }
    ]
    
    mock_emails_att = [mock_emails_all[1]] # msg2 has attachment
    
    def side_effect_fetch(query, max_results=1000):
        if "has:attachment" in query:
            return mock_emails_att
        return mock_emails_all
    
    with patch("bin.extract_06_emails.parse_students", return_value=(mock_name_to_id, mock_id_to_track)), \
         patch("bin.extract_06_emails.fetch_assignment_emails", side_effect=side_effect_fetch):
         
        # Run main function
        extract_06_emails.main()
        
        # Verify output CSV
        assert os.path.exists("output/mail06.csv")
        with open("output/mail06.csv", "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            assert len(reader) == 4
            
            # msg1
            assert reader[0]["학번"] == "2026111111"
            assert reader[0]["점수"] == "2"
            
            # msg2
            assert reader[1]["학번"] == "2026222222"
            assert reader[1]["점수"] == "1"
            assert "첨부있음" in reader[1]["이유"]
            
            # msg3
            assert reader[2]["학번"] == "2026111111"
            assert reader[2]["점수"] == "1"
            assert "양식오류" in reader[2]["이유"]
            
            # msg4
            assert reader[3]["점수"] == "0"
            assert reader[3]["이유"] == "학번 식별 불가"

if __name__ == '__main__':
    test_extract_06_emails()
