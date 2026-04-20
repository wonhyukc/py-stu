# Issue 43 Test Scenarios (서브 폴더 생성 및 트랙별 결과 분리)

## 단위 테스트 (Unit Tests)
1. **트랙별 이름 매핑 검증**
   - **Target**: `bin/extract_emails.py`
   - **목표**: 결과 데이터를 그룹핑할 때, `468` 트랙은 `py`, `761` 트랙은 `web1`, `762` 트랙은 `web2` 등 지정된 prefix 문자열로 올바르게 변환되는지 확인.
   
2. **서브 폴더 경로 생성 검증**
   - **Case**: 주차가 `7`로 주어졌을 때.
   - **조건**: 
     - `py` 트랙 -> `output/py07/mail07.csv` 경로를 반환하는지 확인.
     - `web1` 트랙 -> `output/web1_07/mail07.csv` 경로를 반환하는지 확인.
     - 트랙 식별이 불가능한 경우(unknown) -> `output/unknown07/mail07.csv` 또는 `output/mail07.csv`로 올바르게 폴백(fallback)되는지 확인.

## 통합 검증 (E2E / Integration)
3. **CSV 분리 저장 여부**
   - **Case**: 여러 트랙의 학생들이 섞여 있는 이메일 데이터(또는 실행 결과)를 처리했을 때.
   - **조건**: 스크립트 실행 후 `output/` 디렉토리 내에 트랙별 서브 폴더가 정상적으로 자동 생성되며, 각 폴더 내에 해당하는 트랙의 학생들만 포함된 CSV 파일이 올바르게 기록되는지 확인.
