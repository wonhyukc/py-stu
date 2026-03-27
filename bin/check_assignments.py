import sys
import os
import argparse
from datetime import datetime

# 상위 폴더의 modules 패키지를 import 하기 위한 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.mail_fetcher import fetch_assignment_emails
from modules.grader import grade_assignment

def main():
    parser = argparse.ArgumentParser(description="학생 이메일 과제 판별/채점 스크립트")
    parser.add_argument("--no", type=str, default="0.4", help="검색할 과제 번호 (기본값: 0.4)")
    parser.add_argument("--deadline", type=str, default="2026-03-31 23:59:59", help="마감 기한 (형식: YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--max", type=int, default=50, help="최대 검색 메일 수 (기본값: 50)")
    
    args = parser.parse_args()
    
    try:
        deadline_dt = datetime.strptime(args.deadline, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        print("❌ 에러: 파라미터 --deadline 형식은 YYYY-MM-DD HH:MM:SS 이어야 합니다.")
        return

    print(f"🚀 [과제 {args.no} 스캔 및 채점 시작] (마감 기준: {deadline_dt})")
    
    emails = fetch_assignment_emails(args.no, max_results=args.max)
    if not emails:
        print("해당 과제 단어가 포함된 이메일을 찾지 못했습니다.")
        return
        
    print("-" * 140)
    print(f"{'Score':<7} | {'Student (Sender)':<40} | {'Date / Time':<35} | {'Feedback Notes'}")
    print("-" * 140)
    
    for email_data in emails:
        # 이메일 데이터 넘겨서 3점 채점 수행
        result = grade_assignment(email_data, args.no, deadline_dt)
        
        score_str = f"{result['total_score']} / 3"
        sender_short = email_data['sender'][:40]
        date_short = email_data['date_str'][:35]
        reason = result['reason']
        
        print(f"{score_str:<7} | {sender_short:<40} | {date_short:<35} | {reason}")
        
    print("-" * 140)
    print(f"✅ 총 {len(emails)} 건의 과제 이메일 검토를 완료했습니다.")

if __name__ == '__main__':
    main()
