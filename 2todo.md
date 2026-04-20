# Issue 43 Execution Task (서브 폴더 생성 및 트랙별 결과 분리)

- [ ] **[1prd]** 준수: 트랙(py, web1, web2) 및 주차(week)를 기반으로 독립된 서브 폴더를 생성하여 CSV를 분리 저장하는 요건 확인 완료
- [ ] **[3test]** 작성: 트랙별 서브 폴더 생성 및 파일(`mail07.csv` 등) 분리 저장 로직에 대한 테스트 시나리오 작성 
- [ ] **TDD - Red**: `bin/extract_emails.py`에 트랙별로 결과를 분류하여 각각의 디렉토리 경로를 반환하는 함수의 단위 실패 테스트 작성
- [ ] **TDD - Green**: `extract_emails.py` 내에서 결과를 트랙별로 그룹핑하고, `output/{track_name}{week:02d}/mail{week:02d}.csv` 형태로 저장하는 로직 구현 및 통과
- [ ] **최종 통합**: 스크립트 실행 후 `output/py07/mail07.csv`, `output/web1_07/mail07.csv` 등 트랙별로 서브 폴더가 정상 생성되고 데이터가 나뉘어 저장되는지 확인
- [ ] **최종 테스트 & 커밋**: 검증 후 최종 결과 커밋 및 브라우저 스크린샷 캡처
