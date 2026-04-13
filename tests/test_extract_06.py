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
    mock_emails = [
        # Valid: exact subject, on time (2 points)
        {
            "subject": "과제 0.6",
            "date_str": "Mon, 13 Apr 2026 08:30:00 +0900",
            "sender": "gildong <gildong@test.com>"
        },
        # Valid: assignment 0.6 with ID, on time (2 points)
        {
            "subject": "assignment 0.6 [2026222222]",
            "date_str": "Mon, 13 Apr 2026 08:59:59 +0900",
            "sender": "hyanglin <hyanglin@test.com>"
        },
        # Invalid: late
        {
            "subject": "과제 0.6",
            "date_str": "Mon, 13 Apr 2026 09:00:01 +0900",
            "sender": "gildong <gildong@test.com>"
        },
        # Valid but wrong week: formatting issue, gets 0 points
        {
            "subject": "과제 0.5",
            "date_str": "Mon, 13 Apr 2026 08:00:00 +0900",
            "sender": "gildong <gildong@test.com>"
        },
        # Invalid: ignores "was edited" docs updates
        {
            "subject": "Document was edited recently",
            "date_str": "Sun, 12 Apr 2026 08:00:00 +0900",
            "sender": "docs <comments-noreply@docs.google.com>"
        }
    ]
    
    with patch("bin.extract_06_emails.parse_students", return_value=(mock_name_to_id, mock_id_to_track)), \
         patch("bin.extract_06_emails.fetch_assignment_emails", return_value=mock_emails):
         
        # Run main function
        extract_06_emails.main()
        
        # Verify output CSV
        assert os.path.exists("output/mail06.csv")
        with open("output/mail06.csv", "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            assert len(reader) == 3 # includes the 0.5 one!
            
            # Correct week 0.6 formats
            assert reader[0]["학번"] == "2026111111"
            assert reader[0]["유형"] == "0.6"
            assert reader[0]["점수"] == "2"
            
            assert reader[1]["학번"] == "2026222222"
            assert reader[1]["점수"] == "2"
            
            # Wrong week, but assignment related
            assert reader[2]["점수"] == "0"
            assert reader[2]["유형"] == "기타"
            assert reader[2]["이름"] == "gildong"

if __name__ == '__main__':
    test_extract_06_emails()
