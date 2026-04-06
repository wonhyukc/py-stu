import random

def deduplicate_students(students):
    """
    동일한 학번(또는 식별자)이 여러 번 리스트에 존재할 경우, 가장 마지막 기록만 취합합니다.
    """
    seen = {}
    for student in students:
        student_id = student.get('id')
        seen[student_id] = student
    
    return list(seen.values())

def assign_random_peer_reviews(evaluators, submitted_ids, min_receive=3):
    """
    균형 무작위 배당 (Balanced Random Allocation) 알고리즘
    
    - evaluators: 전체 학생 리스트 (dict)
    - submitted_ids: 과제를 제출한 학생들의 ID 집합 (set or list)
    - min_receive: 제출자 1명이 최소한 받아야 하는 피평가 횟수 (기본값: 3)
    
    조건:
    1. 모든 학생(미제출자 포함)은 최소 1개의 과제를 평가해야 함.
    2. 제출자는 타겟 목표 횟수(최소 3건) 이상의 평가를 균등하게 받아야 함.
    3. 본인 과제는 배정될 수 없음.
    """
    # 1. 대상 분류
    S_objs = [e for e in evaluators if e['id'] in submitted_ids]
    NS_objs = [e for e in evaluators if e['id'] not in submitted_ids]
    
    S_ids = [e['id'] for e in S_objs]
    NS_ids = [e['id'] for e in NS_objs]
    E_ids = [e['id'] for e in evaluators]
    
    if len(S_ids) < 2:
        raise ValueError("제출자가 2명 미만이면 교차 상호평가를 진행할 수 없습니다.")
        
    # 2. 할당량(Quota) 계산
    # 누구나 최소 1건을 평가합니다. (미제출자는 가급적 여기서 멈춤)
    quota = {e_id: 1 for e_id in E_ids}
    total_quota = len(E_ids)
    
    # 평가 대상은 '제출자(S_ids)' 이며, 이들이 각각 min_receive 번씩 평가를 받아야 합니다.
    # 총 필요한 리뷰 횟수 (Total Required Reviews)
    target_total = max(len(S_ids) * min_receive, len(E_ids))
    
    max_s_quota = len(S_ids) - 1  # 본인을 평가할 수 없으므로 S는 최대 len(S)-1 건만 평가 가능
    
    # 목표 할당량에 도달할 때까지 제출자의 평가 횟수(quota)를 우선적으로 올려줍니다.
    while total_quota < target_total:
        added = False
        for s_id in S_ids:
            if quota[s_id] < max_s_quota:
                quota[s_id] += 1
                total_quota += 1
                added = True
                if total_quota == target_total:
                    break
        if total_quota == target_total:
            break
            
        if not added:
            # 제출자가 모두 한계에 도달했는데도 모자라면 미제출자 할당량을 증가시킵니다.
            for ns_id in NS_ids:
                if quota[ns_id] < len(S_ids):
                    quota[ns_id] += 1
                    total_quota += 1
                    added = True
                    if total_quota == target_total:
                        break
        if not added:
            # 더 이상 추가할 수 있는 할당량이 없음
            break
            
    # 3. 균등 분배 배정 (Greedy Balanced Random)
    # 각 피평가자(제출자)가 받은 평가 횟수를 추적
    receive_counts = {s_id: 0 for s_id in S_ids}
    assignments = {} # e_id -> list of reviewee ids
    
    # 리뷰어 순서를 무작위로 섞어서 특정 학번이 항상 유리/불리하지 않도록 함
    evaluator_ids_shuffled = list(E_ids)
    random.shuffle(evaluator_ids_shuffled)
    
    for e_id in evaluator_ids_shuffled:
        q = quota[e_id]
        
        # 유효한 타겟: 본인이 아닌 "제출자"
        valid_targets = [s_id for s_id in S_ids if s_id != e_id]
        
        # 무작위성을 부여하기 위해 먼저 셔플
        random.shuffle(valid_targets)
        # 현재까지 피평가 배트를 가장 적게 받은 사람부터 우선 정렬 (안정 정렬)
        valid_targets.sort(key=lambda x: receive_counts[x])
        
        chosen = valid_targets[:q]
        assignments[e_id] = chosen
        
        # 선택된 타겟들의 피평가 카운트 증가
        for tgt in chosen:
            receive_counts[tgt] += 1
            
    # 4. 결과 매핑
    id_to_obj = {e['id']: e for e in evaluators}
    results = []
    
    # 학번 오름차순으로 예쁘게 정렬하여 출력
    for e_id in sorted(E_ids):
        reviewer = id_to_obj[e_id]
        reviewees = [id_to_obj[tgt_id] for tgt_id in assignments.get(e_id, [])]
        results.append({
            "reviewer": reviewer,
            "reviewees": reviewees
        })
        
    return results, receive_counts
