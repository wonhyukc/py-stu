import os
import csv
import re
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def parse_md_table(filepath):
    students = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        if line.strip().startswith('|') and '학번' not in line and '---' not in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 9:
                # | 강좌번호 | 전공 | 학번 | 성명 | 이메일 | 연락처 | 국적 | 한국어이름 |
                stu_id = parts[3]
                name_en = parts[4]
                email = parts[5].lower()
                name_kr = parts[8]
                students.append({"id": stu_id, "email": email, "name_en": name_en, "name_kr": name_kr})
    return students

def get_student_id(sender_name, sender_email, students):
    sender_email_lower = sender_email.lower()
    sender_name_lower = sender_name.lower().replace(" ", "")
    for s in students:
        if s['email'] and s['email'] in sender_email_lower:
            return s['id']
        s_en = s['name_en'].lower().replace(" ", "")
        if s_en and s_en in sender_name_lower and len(s_en) > 2:
            return s['id']
        s_kr = s['name_kr'].replace(" ", "")
        if s_kr and s_kr in sender_name_lower and len(s_kr) > 1:
            return s['id']
    return ""

def main():
    stu_list = parse_md_table('/home/hyuk/nvme_data/prj/stu/eval/students/wb-students.md')
    stu_list += parse_md_table('/home/hyuk/nvme_data/prj/stu/eval/students/py-students.md')

    creds = Credentials.from_authorized_user_file('/home/hyuk/nvme_data/prj/stu/eval/token.json', SCOPES)
    service = build('gmail', 'v1', credentials=creds)

    print("Fetching messages...")
    results = service.users().messages().list(userId='me', q='-from:me').execute()
    messages = results.get('messages', [])
    
    while 'nextPageToken' in results:
        page_token = results['nextPageToken']
        results = service.users().messages().list(userId='me', q='-from:me', pageToken=page_token).execute()
        messages.extend(results.get('messages', []))

    print(f"Total messages found: {len(messages)}")

    csv_file = '/home/hyuk/nvme_data/prj/stu/eval/output/all_mails.csv'
    if os.path.exists(csv_file):
        os.remove(csv_file)
        
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['학번', '점수', '이유', '날짜', '이름', '메일제목', '추정하는 학번'])

        for i, msg in enumerate(messages):
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
            payload = msg_data.get('payload', {})
            headers = payload.get('headers', [])

            sender = ""
            subject = ""
            date = ""

            for header in headers:
                if header['name'] == 'From':
                    sender = header['value']
                elif header['name'] == 'Subject':
                    subject = header['value']
                elif header['name'] == 'Date':
                    date = header['value']

            # 최초 메일만 (RE: 혹은 Re: 등으로 시작하면 제외)
            if subject.upper().startswith('RE:') or subject.upper().startswith('FW:'):
                continue

            # 이메일, 이름 추출
            sender_name = sender.split('<')[0].strip().strip('"') if '<' in sender else sender
            sender_email_match = re.search(r'<([^>]+)>', sender)
            sender_email = sender_email_match.group(1) if sender_email_match else sender

            # 학번 추출 (메일 제목에 10자리(혹은 8,9자리) 학번 숫자) 주로 20263... 이런 식
            stu_id_match = re.search(r'\b20[1-9][0-9]{6,8}\b', subject)
            stu_id = stu_id_match.group(0) if stu_id_match else ""

            est_id = get_student_id(sender_name, sender_email, stu_list)

            writer.writerow([stu_id, '', '', date, sender_name, subject, est_id])
            if i % 100 == 0:
                print(f"Processed {i} messages...")

    print(f"Saved to {csv_file}")

if __name__ == '__main__':
    main()
