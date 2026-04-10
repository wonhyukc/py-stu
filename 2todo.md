# Issue 33 Execution Task (분반 기반 필터링 및 컬럼 추가 반영)

- [ ] **[1prd]** 준수: 다수결 점수 계산 시 타 분반 수강생 응답 필터링 요건 확인 완료
- [ ] **[3test]** 작성: 분반별 대상 추출 및 CSV 컬럼 생성 테스트 시나리오 작성 
- [ ] **TDD - Red**: `tests/test_peer_grader.py` 또는 `bin/check_evaluations.py`의 단위/통합 실패 테스트 작성
- [ ] **TDD - Green**: `py-students.md` 및 `wb-students.md`를 조회해 유효 ID와 트랙명(py, wb)을 매핑하는 로직 구현 및 통과
- [ ] **최종 통합**: `bin/check_evaluations.py`에서 `--course`에 맞게 대상 필터링, 그리고 CSV 첫 번째 열에 "분반" 항목 추가
- [ ] **최종 테스트 & 커밋**: `pytest` 통과 및 최종 결과 커밋
