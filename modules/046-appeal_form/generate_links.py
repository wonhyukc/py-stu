import csv
import urllib.parse
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 폼 기본 주소
BASE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc8UKgE5AXO9PzmzRuhcCE6C6rtFpD_F_dTRrwfAiPNdCrTMg/viewform"

# 폼 항목별 고유 파라미터 ID (HTML 소스에서 추출)
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
    (예제) 발송용 이메일 로직 - 실제 운영 환경에 맞춰 SMTP 서버나 Gmail API로 교체 필요.
    """
    subject = "[공지] 평가 결과 이의제기 설문 참여 안내"
    body = f"""안녕하세요, {name} 학생.
    
평가 결과에 대한 이의제기가 필요한 경우 아래의 전용 링크를 통해 폼을 제출해 주시기 바랍니다.
본 링크는 학생 본인의 학번, 이름, 트랙이 미리 입력되어 있는 고유 링크입니다.

접속 링크: {link}

감사합니다.
"""
    # 실제 메일 발송 시 주석 해제 및 SMTP 설정 (또는 Gmail API 연동)
    # msg = MIMEMultipart()
    # msg['From'] = "wonhyukc@stu.ac.kr"
    # msg['To'] = to_email
    # msg['Subject'] = subject
    # msg.attach(MIMEText(body, 'plain'))
    # 
    # server = smtplib.SMTP('smtp.gmail.com', 587)
    # server.starttls()
    # server.login("wonhyukc@stu.ac.kr", "앱비밀번호")
    # server.send_message(msg)
    # server.quit()
    pass

def main():
    # 프로젝트 최상단 기준 경로 설정
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_file = os.path.join(base_dir, "input", "roster.csv")
    output_file = os.path.join(base_dir, "output", "appeal_links.csv")
    
    # 1. 입력 파일 존재 여부 확인
    if not os.path.exists(input_file):
        print(f"❌ '{input_file}' 파일이 없습니다.")
        print("   '학번,이름,트랙' 헤더를 가진 학생 명부 CSV 파일을 먼저 준비해 주세요.")
        return

    # 2. CSV 읽기 및 링크 생성
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8', newline='') as f_out:
         
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)
        
        # 헤더 쓰기
        writer.writerow(['학번', '이름', '트랙', '학생이메일', '고유링크'])
        
        count = 0
        for row in reader:
            student_id = row.get('학번', '').strip()
            name = row.get('이름', '').strip()
            track = row.get('트랙', '').strip()
            
            if not student_id:
                continue
                
            # 이메일 주소는 학번@stu.ac.kr 형태라고 가정
            email = f"{student_id}@stu.ac.kr"
            
            # 고유 링크 생성
            link = generate_prefilled_url(student_id, name, track)
            writer.writerow([student_id, name, track, email, link])
            
            # 이메일 발송 호출 (현재는 로직만 있고 실제 발송은 주석 처리됨)
            send_email(email, name, link)
            
            count += 1
            
    print(f"✅ 총 {count}명의 사전 채우기(Pre-filled) 링크 생성이 완료되었습니다.")
    print(f"📁 결과 파일: {output_file}")

if __name__ == "__main__":
    main()
