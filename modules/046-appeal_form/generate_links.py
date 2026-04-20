import csv
import urllib.parse
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 폼 기본 주소
BASE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc8UKgE5AXO9PzmzRuhcCE6C6rtFpD_F_dTRrwfAiPNdCrTMg/viewform"

# 폼 항목별 고유 파라미터 ID
ENTRY_STUDENT_ID = "entry.861702772"
ENTRY_NAME = "entry.2066318256"
ENTRY_TRACK = "entry.898039379"

def generate_prefilled_url(student_id, name, track):
    """
    학번, 이름, 트랙 정보를 받아 미리 채워진(Pre-filled) 구글 폼 URL을 반환합니다.
    """
    params = {
        ENTRY_STUDENT_ID: student_id,
        ENTRY_NAME: name,
        ENTRY_TRACK: track
    }
    # 파라미터를 URL 인코딩 (한글 깨짐 방지)
    query_string = urllib.parse.urlencode(params)
    return f"{BASE_URL}?{query_string}"

def send_email(to_email, name, link):
    """
    (예제) 발송용 이메일 로직
    """
    subject = "[공지] 평가 결과 이의제기 설문 참여 안내"
    body = f"""안녕하세요, {name} 학생.
    
평가 결과에 대한 이의제기가 필요한 경우 아래의 전용 링크를 통해 폼을 제출해 주시기 바랍니다.
본 링크는 학생 본인의 학번, 이름, 트랙이 미리 입력되어 있는 고유 링크입니다.

접속 링크: {link}

감사합니다.
"""
    # 실제 발송 로직은 필요 시 주석 해제하여 사용
    pass

def parse_markdown_table(filepath, default_track):
    """
    마크다운 표 형식의 학생 명부 파일을 파싱하여 학생 리스트 반환
    """
    students = []
    if not os.path.exists(filepath):
        print(f"❌ '{filepath}' 파일을 찾을 수 없습니다.")
        return students

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 테이블 헤더 아래 데이터만 파싱
    data_started = False
    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            continue
            
        # 헤더 구분선인 경우 데이터 시작을 알림
        if '---' in line:
            data_started = True
            continue
            
        # 데이터 파싱
        if data_started:
            cols = [col.strip() for col in line.split('|')]
            if len(cols) > 8:
                student_id = cols[3]
                name_eng = cols[4]
                # 한국어 이름이 있는 경우(8번째 열) 최우선 사용
                name_kr = cols[8] if len(cols) > 8 else ''
                
                name = name_kr if name_kr else name_eng
                
                if student_id and student_id.isdigit():
                    students.append({
                        'student_id': student_id,
                        'name': name,
                        'track': default_track
                    })
    return students

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    py_students_file = os.path.join(base_dir, "input", "students", "py-students.md")
    wb_students_file = os.path.join(base_dir, "input", "students", "wb-students.md")
    output_file = os.path.join(base_dir, "output", "appeal_links.csv")
    
    # 1. 마크다운 파일에서 학생 데이터 추출 및 통합
    all_students = []
    
    # 파이썬 수강생 데이터 추출
    print("파이썬 수강생 명부를 불러오는 중...")
    py_students = parse_markdown_table(py_students_file, "파이썬 (Python)")
    all_students.extend(py_students)
    
    # 웹 수강생 데이터 추출
    print("웹 수강생 명부를 불러오는 중...")
    wb_students = parse_markdown_table(wb_students_file, "웹 (Web)")
    all_students.extend(wb_students)
    
    if not all_students:
        print("❌ 파싱된 학생 데이터가 없습니다. 명부 파일을 확인해주세요.")
        return

    # 2. 고유 링크 생성 및 CSV 저장
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(['학번', '이름', '트랙', '학생이메일', '고유링크'])
        
        count = 0
        for student in all_students:
            student_id = student['student_id']
            name = student['name']
            track = student['track']
            
            email = f"{student_id}@stu.ac.kr"
            link = generate_prefilled_url(student_id, name, track)
            
            writer.writerow([student_id, name, track, email, link])
            
            # 메일 발송 함수(테스트 시 주석 처리됨)
            send_email(email, name, link)
            count += 1
            
    print(f"✅ 총 {count}명(파이썬 {len(py_students)}명, 웹 {len(wb_students)}명)의 고유 링크 생성이 완료되었습니다.")
    print(f"📁 결과 파일: {output_file}")

if __name__ == "__main__":
    main()
