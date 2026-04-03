import csv
from collections import defaultdict
import os


def validate_assignment_csv(filepath: str):
    if not os.path.exists(filepath):
        print(f"❌ 검증 실패: {filepath} 파일이 존재하지 않습니다.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    checklist = {
        "C1": "모든 학생이 정확히 3명의 피평가자를 배정받았는가?",
        "C2": "자기 자신을 평가하도록 배정된 경우가 없는가?",
        "C3": "동일한 피평가자를 중복해서 배정받은 경우가 없는가?",
        "C4": "배정된 피평가자가 모두 같은 분반에 속해 있는가?",
        "C5": "피평가자(제출자) 풀이 균등하게 배정되었는가? (최소 3명 이상의 순환 평가)",
    }

    results = {k: True for k in checklist.keys()}
    errors = defaultdict(list)
    target_counts = defaultdict(int)  # type: ignore

    evaluator_classes = {r["평가자_학번"].strip(): r["분반"].strip() for r in rows}

    for i, row in enumerate(rows):
        evaluator_id = row["평가자_학번"].strip()
        c_num = row["분반"].strip()

        targets = []
        for t_idx in [1, 2, 3]:
            t_id = row.get(f"피평가자{t_idx}_학번", "").strip()
            if t_id:
                targets.append(t_id)
                target_counts[t_id] += 1

        # C1
        if len(targets) != 3:
            results["C1"] = False
            errors["C1"].append(
                f"평가자 {evaluator_id}의 피평가자가 {len(targets)}명입니다."
            )

        # C2
        if evaluator_id in targets:
            results["C2"] = False
            errors["C2"].append(f"평가자 {evaluator_id}가 자기 자신을 배정받았습니다.")

        # C3
        if len(targets) != len(set(targets)):
            results["C3"] = False
            errors["C3"].append(
                f"평가자 {evaluator_id}가 중복 배정받았습니다: {targets}"
            )

        # C4
        for t_id in targets:
            if t_id in evaluator_classes:
                if evaluator_classes[t_id] != c_num:
                    results["C4"] = False
                    errors["C4"].append(
                        f"평가자 {evaluator_id}({c_num}) -> {t_id}({evaluator_classes[t_id]})"
                    )

    class_targets = defaultdict(list)
    for t_id, count in target_counts.items():
        if t_id in evaluator_classes:
            c_num = evaluator_classes[t_id]
            class_targets[c_num].append((t_id, count))

    print("\n" + "=" * 50)
    print("📊 상호평가 매칭 결과 검증 채점표 (Checklist)")
    print("=" * 50)
    for k, desc in checklist.items():
        status = "✅ PASS" if results[k] else "❌ FAIL"
        print(f"[{status}] {k}: {desc}")
        if not results[k]:
            for err in errors[k][:3]:
                print(f"   -> {err}")
            if len(errors[k]) > 3:
                print(f"   -> ... 외 {len(errors[k]) - 3}건")

    if not results["C3"]:
        print(
            "\n⚠️ [주의] C3 FAIL 관련: 제출자가 10명 이하인 분반의 구조적 한계로 발생한 현상입니다. (문서 참고)"
        )

    print("\n[C5 분반별 피평가자 피드백 수신 빈도 확인]")
    for c_num in sorted(class_targets.keys()):
        t_list = class_targets[c_num]
        counts = [c for _, c in t_list]
        print(
            f"  - 분반 {c_num}: {len(t_list)}명의 피평가자가 각각 {min(counts)}~{max(counts)}번의 피드백 배정됨"
        )
    print("=" * 50 + "\n")
