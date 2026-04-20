import os
import sys
import pytest
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from bin.extract_emails import get_time_window, parse_students


def test_get_time_window():
    start_dt, deadline_dt = get_time_window()

    # 마감일은 반드시 월요일 09:00 이어야 함 (weekday() == 0)
    assert deadline_dt.weekday() == 0
    assert deadline_dt.hour == 9
    assert deadline_dt.minute == 0

    # 시작일은 마감일로부터 정확히 7일 전이어야 함
    expected_start = deadline_dt - timedelta(days=7)
    assert start_dt == expected_start


def test_parse_students():
    # 파일이 존재하는 환경에서 실행될 경우 딕셔너리 반환 확인
    name_to_id, id_to_track, id_to_names = parse_students()

    assert isinstance(name_to_id, dict)
    assert isinstance(id_to_track, dict)

    # 만약 데이터가 파싱되었다면, key와 value가 모두 문자열이어야 함
    if len(id_to_track) > 0:
        for k, v in id_to_track.items():
            assert isinstance(k, str)
            assert isinstance(v, str)
            assert k.isdigit()  # 학번은 숫자 형태
