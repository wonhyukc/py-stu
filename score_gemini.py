import csv
import os
import json
import time
import re
from playwright.sync_api import sync_playwright
import google.generativeai as genai
import PIL.Image

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    exit(1)

genai.configure(api_key=API_KEY)
# We use JSON response mime type to get a structured evaluation
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config={"response_mime_type": "application/json"}
)

input_csv = "/data/hyuk/prj/stu/eval/wb02-mid.csv"
output_csv = "/data/hyuk/prj/stu/eval/wb02-mid-scored.csv"

# 1. Parse CSV to get all links
students = []
with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        student_id = row["Student ID"]
        completed_time = row["Completed Time"]
        raw_links_str = row["Links"]
        
        # Extract URLs
        raw_links = raw_links_str.split("\n")
        clean_links = []
        for l in raw_links:
            match = re.search(r'(https?://gemini\.google\.com/share/[a-zA-Z0-9_-]+)', l)
            if match:
                clean_links.append(match.group(1))
            else:
                # Some links might not have https:// prefix
                match = re.search(r'(gemini\.google\.com/share/[a-zA-Z0-9_-]+)', l)
                if match:
                    clean_links.append("https://" + match.group(1))

        if clean_links:
            students.append({
                "id": student_id,
                "time": completed_time,
                "raw_links": raw_links_str,
                "links": clean_links
            })

print(f"Loaded {len(students)} students to evaluate.")

prompt = """
당신은 웹 프로그래밍 과목의 깐깐하지만 공정한 조교입니다. 학생이 제출한 제미니(Gemini) 대화 기록 스크린샷들을 보고 학생의 학습 노력을 평가해야 합니다.

평가 기준 (최대 5점):
- 1~2점: 시험이나 과제 문제를 그대로 복사/붙여넣기만 하고 끝난 경우. 질문에 대한 답변만 얻고 추가 질문이나 상호작용이 전혀 없음.
- 3점: 문제를 복붙했으나, 답변을 읽고 이해가 안 가는 짧은 부분에 대해 한 번 정도 단순 추가 질문을 한 경우.
- 4점: 문제의 답안뿐만 아니라 "왜 그런지" 이유를 묻거나, 관련 개념에 대해 추가적인 설명을 요구한 경우. 다른 예시를 보여달라고 요청하며 개념을 이해하려고 시도한 경우.
- 5점: 본인이 먼저 코드를 작성해보고 리뷰나 디버깅을 요청한 경우. 배운 개념을 확장하여 심도 있는 꼬리 질문(Follow-up questions)을 여러 번 이어나가며 주도적으로 학습한 흔적이 명확히 보이는 경우.

주어진 스크린샷은 한 학생이 제출한 모든 제미니 대화 기록입니다. (여러 장일 수 있음)
모든 스크린샷의 대화 내용을 종합적으로 판단하여 다음 JSON 형식으로 응답해주세요:
{
  "score": <점수 (정수 1~5)>,
  "reason": "<평가 사유 (왜 이 점수를 주었는지 2~3문장으로 한국어로 설명)>",
  "summary": "<학생이 질문한 주요 내용 요약 (1~2문장)>"
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # Use a large viewport to capture as much content as possible
    page = browser.new_page(viewport={"width": 1280, "height": 1080})
    
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(["Student ID", "Completed Time", "Links", "Score", "Reason", "Summary"])
        
        for student in students:
            print(f"\nEvaluating Student ID: {student['id']} ({len(student['links'])} links)")
            images = []
            
            for i, link in enumerate(student['links']):
                print(f"  Fetching: {link}")
                img_path = f"/data/hyuk/prj/stu/eval/tmp_{student['id']}_{i}.png"
                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=20000)
                    # wait a bit for JS rendering of the chat
                    page.wait_for_timeout(3000)
                    # Take full page screenshot
                    page.screenshot(path=img_path, full_page=True)
                    images.append(PIL.Image.open(img_path))
                except Exception as e:
                    print(f"  Error loading {link}: {e}")
            
            if not images:
                print("  No images captured. Score: 0")
                writer.writerow([student['id'], student['time'], student['raw_links'], 0, "유효한 링크가 없거나 캡처에 실패했습니다.", ""])
                out_f.flush()
                continue
            
            # Send to Gemini
            print("  Evaluating with Gemini 2.5 Flash...")
            try:
                content = [prompt] + images
                response = model.generate_content(content)
                res_data = json.loads(response.text)
                
                score = res_data.get("score", 0)
                reason = res_data.get("reason", "")
                summary = res_data.get("summary", "")
                
                print(f"  Score: {score}/5")
                print(f"  Reason: {reason}")
            except Exception as e:
                print(f"  Gemini API Error: {e}")
                score = -1
                reason = f"API 오류 발생: {e}"
                summary = ""
            
            writer.writerow([student['id'], student['time'], student['raw_links'], score, reason, summary])
            out_f.flush()
            
            # Clean up temporary images to save space
            for img in images:
                img.close()
            for i in range(len(student['links'])):
                img_path = f"/data/hyuk/prj/stu/eval/tmp_{student['id']}_{i}.png"
                if os.path.exists(img_path):
                    os.remove(img_path)
            
            # small delay to prevent rate limits
            time.sleep(2)

    browser.close()

print(f"\nEvaluation complete. Results saved to {output_csv}")
