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
        # Valid: exact subject, on time
        {
            "subject": "과제 0.6",
            "date_str": "Mon, 13 Apr 2026 08:30:00 +0900",
            "sender": "gildong <gildong@test.com>"
        },
        # Valid: assignment 0.6 with ID, on time
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
        # Invalid: wrong subject
        {
            "subject": "과제 0.5",
            "date_str": "Mon, 13 Apr 2026 08:00:00 +0900",
            "sender": "gildong <gildong@test.com>"
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
            assert len(reader) == 2
            
            assert reader[0]["학번"] == "2026111111"
            assert reader[0]["유형"] == "0.6"
            assert reader[0]["메일제목"] == "과제 0.6"
            
            assert reader[1]["학번"] == "2026222222"
            assert reader[1]["메일제목"] == "assignment 0.6 [2026222222]"
if __name__ == '__main__': test_extract_06_emails()
