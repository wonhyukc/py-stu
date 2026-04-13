import os
import csv
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote
import time

# We must import the student parsing from the existing script
try:
    from bin.extract_06_emails import parse_students
except ImportError:
    # fallback if run directly from bin
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from bin.extract_06_emails import parse_students

from playwright.sync_api import sync_playwright

KST = timezone(timedelta(hours=9))

def extract_gmail_interactive():
    print("Loading student roster...")
    name_to_id, id_to_track = parse_students()
    
    # rule: 과제 or assignment 0.x (학번 필수 - 10자리 숫자)
    strict_re = re.compile(r"(과제|assignment)\s*0?\.6\s*(?:\[|\()?(\d{10})(?:\]|\))?")
    any_assignment_re = re.compile(r"(과제|assignment|0?\.6)")

    new_rows = []
    
    with sync_playwright() as p:
        # Launch headless=False so the professor can see and login
        # Use Chrome channel to avoid bot detection better and a modern user agent
        browser = p.chromium.launch(headless=False, channel="chrome", args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("Navigating to mail.google.com...")
        page.goto('https://mail.google.com/')
        print(">>> 브라우저가 화면에 팝업되었습니다. 직접 로그인해주세요! (최대 3분 대기합니다) <<<")
        
        # Wait for the search box which appears after successful inbox load
        try:
            page.wait_for_selector('input[name="q"]', timeout=180000)
            print("로그인 확인 완료! 받은편지함 진입 성공.")
        except Exception as e:
            print("3분 내에 로그인이 확인되지 않거나 Inbox를 렌더링하지 못했습니다.")
            browser.close()
            return
            
        # Optional: wait an extra 2 seconds for JS execution
        page.wait_for_timeout(2000)

        # Execute Search
        search_query = '("과제" OR "0.6") after:2026/04/05 before:2026/04/14 -from:comments-noreply@docs.google.com'
        print(f"다음 쿼리로 메일을 검색합니다: {search_query}")
        page.fill('input[name="q"]', search_query)
        page.keyboard.press("Enter")
        
        print("검색 결과 대기 중...")
        # Wait for the email list to stabilize. Sometimes it's fast, sometimes slow.
        page.wait_for_timeout(5000)
        
        # Try to find email rows
        rows = page.locator('tr.zA')
        count = rows.count()
        print(f"총 {count}개의 검색된 이메일을 발견했습니다.")
        
        start_dt = datetime(2026, 4, 6, 9, 0, tzinfo=KST)
        deadline_06 = datetime(2026, 4, 13, 9, 0, tzinfo=KST)
        
        for i in range(count):
            row = rows.nth(i)
            # Extractor strategies
            try:
                # Subject is usually inside span.bog
                sub_loc = row.locator('span.bog')
                subject = sub_loc.inner_text().strip() if sub_loc.count() > 0 else ""
                
                # Sender is usually in div.yW or span.zF
                sender_loc = row.locator('div.yW span[name]')
                if sender_loc.count() > 0:
                    sender = sender_loc.first.get_attribute("name") or sender_loc.first.inner_text()
                else:
                    sender = ""
                    
                # Date is usually in span inside td.xW that has title="Mon, Apr 6, 2026..."
                date_loc = row.locator('td.xW span')
                date_str = date_loc.first.get_attribute("title") if date_loc.count() > 0 else ""
                
                # If date_str is empty, fallback to innerText
                if not date_str and date_loc.count() > 0:
                    date_str = date_loc.first.inner_text()
                if not date_str:
                    date_str = "Thu, 9 Apr 2026 12:00:00 +0900" # Dummy fallback
                    
                # Has attachment? Often indicated by an image with alt="Attachment" or class .yE
                has_att = row.locator('img.yE').count() > 0 or row.locator('[aria-label="Attachment"]').count() > 0 or "Attachment" in row.inner_html()
                
            except Exception as e:
                print(f"Row {i} 파싱 에러: {e}")
                continue
                
            subject_lower = subject.lower()
            clean_sub = re.sub(r"\s+", "", subject_lower)
            m_strict = strict_re.search(clean_sub)
            
            # Determine Student ID (Est ID) First
            est_id = m_strict.group(2) if m_strict else ""
            if not est_id:
                clean_name = re.sub(r"\s+", "", sender).lower()
                if clean_name in name_to_id:
                    est_id = name_to_id[clean_name]
                else:
                    m_id = re.search(r"\d{10}", subject)
                    if m_id:
                        est_id = m_id.group(0)

            # Assign points
            score = 0
            reason = "수동 확인 요망(양식불일치/타주차)"
            task_type = "기타"
            
            if not est_id or est_id not in id_to_track:
                score = 0
                reason = "학번 식별 불가"
                task_type = "기타"
            else:
                task_type = "0.6"
                if m_strict and not has_att:
                    score = 2
                    reason = "정확한 양식/첨부없음(+2)"
                elif any_assignment_re.search(clean_sub):
                    # Check explicitly other week
                    diff_week_match = re.search(r"0?\.([0-57-9])", clean_sub)
                    is_this_week = "0.6" in clean_sub or not diff_week_match
                    
                    if is_this_week:
                        score = 1
                        violations = []
                        if not m_strict: violations.append("양식오류")
                        if has_att: violations.append("첨부있음")
                        reason = f"양식위반({','.join(violations)}) (+1)"
                    else:
                        score = 0
                        reason = "타주차 과제(수동확인)"
                        task_type = "기타"

            row_data = {
                "학번": est_id,
                "추정하는학번": est_id,
                "track": id_to_track.get(est_id, ""),
                "점수": score,
                "유형": task_type,
                "이유": reason,
                "날짜": date_str,
                "이름": sender,
                "메일제목": subject,
            }
            new_rows.append(row_data)
            print(f" -> 성공적 파싱: {est_id} ({sender}) | 점수: {score} | {reason}")

        browser.close()

    print(f"\\n========= 총 {len(new_rows)}건의 0.6 주차 과제 메일 파싱/채점 완료 =========")
    if new_rows:
        os.makedirs(os.path.join(os.path.dirname(__file__), '../output'), exist_ok=True)
        out_path = os.path.join(os.path.dirname(__file__), '../output/mail06.csv')
        fieldnames = ["학번", "추정하는학번", "track", "점수", "유형", "이유", "날짜", "이름", "메일제목"]
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(new_rows)
        print(f"Saved to {out_path}")
    else:
        print("저장할 데이터가 없습니다.")

if __name__ == "__main__":
    extract_gmail_interactive()
