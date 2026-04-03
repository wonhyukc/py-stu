import random
import glob
import os


def parse_markdown_table(filepath):
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    headers = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue

        if not headers and "학번" in line:
            headers = [c.strip() for c in line.split("|")[1:-1]]
            continue

        columns = [c.strip() for c in line.split("|")[1:-1]]
        if len(columns) == 0:
            continue

        if headers and "---" not in line:
            if len(columns) >= len(headers):
                row_dict = dict(zip(headers, columns))
                if "학번" in row_dict and row_dict["학번"]:
                    data.append(row_dict)
    return data


def build_master_roster():
    data = []
    md_files = glob.glob(os.path.join("input", "students", "*.md"))
    for md_file in md_files:
        data.extend(parse_markdown_table(md_file))

    roster = {}
    for row in data:
        class_name = row.get("강좌번호", "Unknown")
        name = row.get("한국어이름", "")
        if not name or name.strip() == "":
            name = row.get("성명", "")

        roster[row["학번"]] = {
            "학번": row["학번"],
            "이름": name,
            "강좌번호": class_name,
        }
    return roster


def assign_peers_for_class(evaluators, targets, num_peers=3):
    if not targets:
        return {e["학번"]: [] for e in evaluators}

    random.shuffle(targets)
    assignments = {}

    needed = max(len(evaluators) * num_peers, len(targets))
    target_pool = []
    while len(target_pool) < needed:
        target_pool.extend(targets)

    pool_idx = 0
    for evaluator in evaluators:
        assigned = []
        attempts = 0
        while len(assigned) < num_peers and attempts < 10:
            candidate = target_pool[pool_idx % len(target_pool)]
            pool_idx += 1
            attempts += 1
            if candidate["학번"] != evaluator["학번"] and (
                len(targets) == 1
                or candidate["학번"] not in [a["학번"] for a in assigned]
            ):
                assigned.append(candidate)

        while len(assigned) < num_peers:
            candidate = target_pool[pool_idx % len(target_pool)]
            pool_idx += 1
            assigned.append(candidate)

        assignments[evaluator["학번"]] = assigned

    return assignments
