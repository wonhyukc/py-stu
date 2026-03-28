import os
import sys
import re
import csv
import json
import argparse
from datetime import datetime
import email.utils

# 현재 파일 위치(bin/)의 상위 디렉토리(루트)를 base_dir로 설정
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from modules.mail_fetcher import fetch_assignment_emails
from modules.grader import parse_email_date
from modules.sheet_updater import append_grades_to_sheet

SETTINGS_FILE = os.path.join(base_dir, 'settings.json')

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # 초기 설정 시 디폴트 값
    return {"gmail_search_query": "과제 0.4 | assignment 0.4"}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def extract_grades(query=None):
    settings = load_settings()
    
    if query and query != settings.get("gmail_search_query"):
        settings["gmail_search_query"] = query
        save_settings(settings)
        print(f"📝 settings.json 의 검색 쿼리가 업데이트 되었습니다: '{query}'")
        
    current_query = settings.get("gmail_search_query", "과제 0.4 | assignment 0.4")
    print(f"🔍 다음 쿼리 규칙으로 메일을 수집합니다: [{current_query}]")
    
    deadline_dt = datetime.strptime("2026-03-31 23:59:59", "%Y-%m-%d %H:%M:%S")
    emails = fetch_assignment_emails(current_query, max_results=50)
    
    # 제외할 본인 이메일 (발송한 메일 제외)
    my_email_patterns = ["wonhyukc@stu.ac.kr"]
    
    output_rows = []
    # 이미 처리한 학번을 추적하여 중복 점수 부여를 방지하는 셋(set)
    seen_students = set()
    
    # 헤더
    output_rows.append(["학번", "점수", "이유", "날짜", "이름", "메일제목"])
    
    for email_data in emails:
        subject = email_data.get('subject', '')
        date_str = email_data.get('date_str', '')
        sender_str = email_data.get('sender', '')
        
        # 1. 내가 발송한(답변한) 메일이면 제외
        sender_str_lower = sender_str.lower()
        if any(my_email in sender_str_lower for my_email in my_email_patterns):
            continue
            
        # 2. 메일 제목 20자까지만 자르기
        short_subject = subject[:20]
        
        # 3. 이름 파싱
        name, _ = email.utils.parseaddr(sender_str)
        if not name:
            name = sender_str.split('<')[0].strip(' "')
        
        # 4. 학번 파싱 (이미지의 경우 2026300096 등 10자리 숫자이므로 \d{8,11} 매칭)
        match = re.search(r'\d{8,11}', subject)
        student_id = match.group(0) if match else "학번없음"
        
        # 4.5 중복 제출 확인 (학번이 확인된 경우 1회만 점수 부여)
        if student_id != "학번없음":
            if student_id in seen_students:
                continue # 이미 점수가 기록된 학생의 과거 메일은 스킵
            seen_students.add(student_id)
            
        # 5. 날짜 파싱 및 마감(1점) 처리
        mail_dt = parse_email_date(date_str)
        score = 0
        formatted_date = "알수없음"
        
        # 쿼리에서 과제 번호 추출 (예: '과제 0.4 | assignment 0.4' -> '0.4')
        q_match = re.search(r'\d+(?:\.\d+)?', current_query)
        task_num = q_match.group(0) if q_match else ""
        task_prefix = f"과제{task_num} " if task_num else "과제 "
        
        reason = f"{task_prefix.strip()} 마감시간초과"
        
        if mail_dt:
            # 출력 포맷: 3/27 18:30
            formatted_date = f"{mail_dt.month}/{mail_dt.day} {mail_dt.strftime('%H:%M')}"
            if mail_dt <= deadline_dt:
                score = 1
                reason = f"{task_prefix.strip()} 기간내 제출"
                
        output_rows.append([student_id, score, reason, formatted_date, name, short_subject])
        
    output_path = os.path.join(base_dir, "output", "grades_output.csv")
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(output_rows)
        
    print(f"✅ 총 {len(output_rows) - 1}명의 이메일(본인 발송분 제외)을 분석했습니다.")
    print(f"✅ 저장된 '{output_path}' 파일 미리보기:\n")
    
    for row in output_rows[:15]:
        print(",".join(map(str, row)))
        
    print("\n⬇️ 이제 추출된 데이터를 시트에 실제 기록(Append)합니다 ⬇️")
    # 헤더(첫 번째 행)는 제외하고 순수 데이터만 배열에 담아 넘깁니다.
    data_to_append = output_rows[1:]
    if data_to_append:
        append_grades_to_sheet(data_to_append)
    else:
        print("❗ 시트에 추가할 새로운 메일 데이터가 없습니다.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="구글 메일 기반 과제 성적 자동 추출기")
    parser.add_argument('--query', type=str, default=None, help="검색 쿼리 지정 (지정하지 않으면 settings.json의 마지막 값을 사용)")
    args = parser.parse_args()
    
    extract_grades(query=args.query)
