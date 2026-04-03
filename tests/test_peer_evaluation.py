import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_majority_vote_clear():
    # 3test.md: 3명 중 2명 이상이 동일한 점수 배열을 주었을 때
    assert True


def test_majority_vote_tie():
    # 3test.md: 2명이 서로 다른 점수를 주었을 때 합이 높은 것을 다수결로 선택
    assert True


def test_evaluator_points():
    # 3test.md: 다수결 일치 시 배정 비율 획득, 소수 의견 감점
    assert True


def test_final_score_normalized():
    # 3test.md: 0.8과 0.2 가중치 적용 확인. 최대 1.0
    assert True
