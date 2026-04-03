#!/usr/bin/env python3
import sys
import os

# 상위 폴더의 modules 패키지를 import 하기 위한 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
# 1prd.md 에 등재된 통합 폼 시트 ID
SHEET_ID = "1_o-F6UaQ2WOe0nH2zuT_0xpwiOm1ebmWo2sEQzQptEk"
GID = 427896056


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    secret_path = os.path.join(base_dir, "secret.json")

    print("🚀 [상호평가 스캔 및 이상치 점검 시작]")
    try:
        creds = Credentials.from_service_account_file(secret_path, scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    except Exception as e:
        print(f"❌ 인증 실패: {e}")
        sys.exit(1)

    # gid 기반으로 sheet title 찾기
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        sheet_title = None
        for s in sheet_metadata.get("sheets", []):
            if s["properties"].get("sheetId") == GID:
                sheet_title = s["properties"]["title"]
                break

        if not sheet_title:
            print(f"❌ 시트 ID({GID})를 찾을 수 없습니다.")
            sys.exit(1)

        print(f"✅ 대상 시트 발견: {sheet_title}")

        range_name = f"{sheet_title}!A:Z"
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=SHEET_ID, range=range_name)
            .execute()
        )
        values = result.get("values", [])
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        sys.exit(1)

    if not values:
        print("💡 시트에 데이터가 없습니다.")
        return

    headers = values[0]
    evaluator_idx = -1
    target_idx = -1
    score_idxs = []

    for i, h in enumerate(headers):
        h_str = str(h)
        if ("학번 번호" in h_str or "Student ID" in h_str) and evaluator_idx == -1:
            evaluator_idx = i
        elif "피평가자" in h_str or "대상자" in h_str or "Reviewee" in h_str:
            target_idx = i
        elif "평가" in h_str or "기준" in h_str or "점수" in h_str:
            score_idxs.append(i)

    # 1prd.md나 현재 시트 상태를 기반으로, 추가 컬럼이 없다고 하더라도 일단 프로세스를 진행
    if evaluator_idx == -1:
        print(
            "⚠️ '학번'이나 'Student ID' 컬럼을 찾지 못했습니다. 컬럼 헤더를 다시 확인해주세요."
        )
        evaluator_idx = 3  # 기본 fallback (0-indexed -> 3 is 4th col)

    outliers_detected = 0
    valid_reviews = 0

    print("-" * 120)
    print(
        f"{'Evaluator (학번)':<20} | {'Reviewee (대상자)':<20} | {'Scores (이상치 포함)'}"
    )
    print("-" * 120)

    for row in values[1:]:
        if len(row) <= evaluator_idx:
            continue

        evaluator = row[evaluator_idx].strip()
        target = (
            row[target_idx].strip()
            if target_idx != -1 and len(row) > target_idx
            else "N/A"
        )

        scores_given = []
        has_outlier = False

        for idx in score_idxs:
            if len(row) > idx:
                val = row[idx].strip()
                scores_given.append(val)
                # 이상치 규칙: 0 또는 1이 아닌 경우 (예: 2점 등)
                if val not in ["0", "1"]:
                    has_outlier = True
            else:
                scores_given.append("N/A")

        if scores_given and has_outlier:
            outliers_detected += 1
            print(
                print(
                    f"\033[93m⚠️  Warning: [평가자 {evaluator}] -> [대상자 {target}] "
                    f"이상치 점수 발견 ({scores_given}) (점수는 따로 처리하지 않고 통과)\033[0m"
                )
            )
        else:
            if not scores_given:
                # 평가 기준 컬럼이 아직 없는 경우
                pass

        if target != "N/A" or scores_given:
            valid_reviews += 1
            if not has_outlier:
                print(f"{evaluator:<20} | {target:<20} | {scores_given}")

    print("-" * 120)
    print(
        f"✅ 총 {valid_reviews} 건의 평가 데이터 스캔 완료. (발견된 이상치: {outliers_detected} 건)"
    )


if __name__ == "__main__":
    main()
