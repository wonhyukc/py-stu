---
name: moodle-tsv-converter
description: "Moodle 점수 데이터를 TSV 포맷(id, score 컬럼)으로 변환하고 관리하는 스킬"
---

# Moodle TSV Converter Skill

Moodle에 점수를 일괄 등록하기 위해 오프라인(Python 등) 채점 결과를 `id`, `score` 두 컬럼을 가진 TSV 파일로 변환할 때 사용하는 스킬입니다. Moodle의 "Paste from spreadsheet" 기능과 완벽하게 호환되도록 만듭니다.

## 언제 사용하나요?
- 사용자가 Moodle 성적 업로드용 파일(`moodle_score_track_*.csv` 등) 생성 코드를 수정해달라고 요청할 때.
- 성적 데이터 변환 시 포맷(TSV)과 컬럼명(`id`, `score`)을 강제해야 할 때.

## 에이전트 행동 지침
1. **스크립트 점검**: 
   - 사용자가 지목한 변환 스크립트(주로 `scripts/convert_moodle_scores.py`)를 엽니다.
2. **출력 포맷 강제**:
   - 출력 파일의 확장자를 `.tsv`로 설정합니다. (탭 구분자 `\t` 사용)
   - 헤더(Header)가 반드시 `['id', 'score']` 형태인지 확인하고 수정합니다.
3. **검증 및 실행**:
   - 스크립트를 실행하여 데이터가 올바른 포맷의 파일로 출력되었는지 검사합니다.
   - 변환된 TSV 파일의 헤더와 첫 데이터를 확인해 정상 변환을 사용자에게 보고합니다.
