# -*- coding: utf-8 -*-
"""
Regression Snapshot Generator
生成旧 regression 基线快照，用于检测代码变更对输出的影响。

用法：
    python -m tools.regression_snapshot --mode=generate --output=snapshots/baseline.json
    python -m tools.regression_snapshot --mode=compare --baseline=snapshots/baseline.json --after=snapshots/after.json
"""

import sys
import os
import json
import io
import hashlib
from datetime import datetime
from typing import Dict, Any, List

# 将 bazi 模块添加到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck
from bazi.cli import run_cli
from bazi.compute_facts import compute_facts


# 回归用例定义（关键用例覆盖用神规则）
REGRESSION_CASES = [
    # 基础用例
    {"id": "黄金A", "birth_date": "2005-09-20", "birth_time": "10:00", "is_male": True},
    {"id": "黄金B", "birth_date": "2007-01-28", "birth_time": "12:00", "is_male": True},
    {"id": "2006-12-17_1200_M", "birth_date": "2006-12-17", "birth_time": "12:00", "is_male": True},
    # 用神补木规则用例（壬癸水 + 官杀旺 + 身弱）
    {"id": "用神补木_2007-01-28", "birth_date": "2007-01-28", "birth_time": "12:00", "is_male": True},
    # 用神补火规则用例（甲乙木 + 官杀旺 + 身弱 + 基础用神为水木）
    {"id": "用神补火_2005-08-08", "birth_date": "2005-08-08", "birth_time": "08:00", "is_male": True},
    # 新规则用例：官杀旺+身弱→补食伤
    # 用例1: 火日主，天干地支财星都<20%，食伤土两层都可用
    {"id": "食伤土_双层_2022-12-20", "birth_date": "2022-12-20", "birth_time": "14:00", "is_male": True},
    # 用例2: 木日主，地支财>=20%导致地支食伤不可用，仅天干金
    {"id": "食伤金_仅天干_1985-12-25", "birth_date": "1985-12-25", "birth_time": "06:00", "is_male": True},
    # 用例3: 木日主，天干财>=20%导致天干食伤不可用，仅地支金
    {"id": "食伤金_仅地支_1984-11-30", "birth_date": "1984-11-30", "birth_time": "06:00", "is_male": True},
]


def _parse_datetime(birth_date: str, birth_time: str) -> datetime:
    """解析日期时间字符串为 datetime 对象。"""
    return datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M")


def _capture_cli_output(birth_dt: datetime, is_male: bool) -> str:
    """捕获 CLI 打印输出。"""
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    try:
        run_cli(birth_dt, is_male)
        return captured_output.getvalue()
    finally:
        sys.stdout = old_stdout


def _compute_hash(text: str) -> str:
    """计算文本的 MD5 哈希。"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def generate_snapshot(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """为所有用例生成快照。"""
    snapshot = {
        "generated_at": datetime.now().isoformat(),
        "cases": {}
    }

    for case in cases:
        case_id = case["id"]
        birth_dt = _parse_datetime(case["birth_date"], case["birth_time"])
        is_male = case["is_male"]

        print(f"Processing case: {case_id}...", file=sys.stderr)

        # 1. 捕获 CLI 打印输出
        cli_output = _capture_cli_output(birth_dt, is_male)

        # 2. 获取 facts 数据（用于 LLM 输入）
        facts = compute_facts(birth_dt, is_male, max_dayun=10)
        natal = facts.get("natal", {})

        # 3. 提取用神相关字段
        yongshen_data = {
            "yongshen_elements": natal.get("yongshen_elements", []),
            "yongshen_detail": natal.get("yongshen_detail", {}),
            "special_rules": natal.get("special_rules", []),
            "strength_percent": natal.get("strength_percent", 0.0),
            "support_percent": natal.get("support_percent", 0.0),
        }

        # 4. 提取十神类别百分比
        shishen_category_pcts = natal.get("shishen_category_percentages", {})

        # 5. 存储快照
        snapshot["cases"][case_id] = {
            "input": {
                "birth_date": case["birth_date"],
                "birth_time": case["birth_time"],
                "is_male": is_male,
            },
            "cli_output": cli_output,
            "cli_output_hash": _compute_hash(cli_output),
            "yongshen_data": yongshen_data,
            "shishen_category_pcts": shishen_category_pcts,
            # 用于 LLM 输入的关键字段（序列化后哈希）
            "facts_natal_json": json.dumps(natal, ensure_ascii=False, sort_keys=True),
            "facts_natal_hash": _compute_hash(json.dumps(natal, ensure_ascii=False, sort_keys=True)),
        }

    return snapshot


def _extract_critical_fields(natal_json: str) -> Dict[str, Any]:
    """提取用于回归对比的关键字段（忽略新增的 metadata 字段）。"""
    natal = json.loads(natal_json)

    # 只提取关键输出字段（影响最终打印/LLM 输入的）
    yong_detail = natal.get("yongshen_detail", {})

    return {
        "yongshen_elements": natal.get("yongshen_elements"),
        "base_yongshen_elements": yong_detail.get("base_yongshen_elements"),
        "final_yongshen_elements": yong_detail.get("final_yongshen_elements"),
        "special_rules": natal.get("special_rules"),
        "strength_percent": natal.get("strength_percent"),
        "support_percent": natal.get("support_percent"),
        "shishen_category_percentages": natal.get("shishen_category_percentages"),
    }


def compare_snapshots(baseline: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """对比两个快照，返回差异报告。"""
    report = {
        "baseline_generated_at": baseline.get("generated_at"),
        "after_generated_at": after.get("generated_at"),
        "diffs": [],
        "summary": {"total": 0, "changed": 0, "unchanged": 0}
    }

    baseline_cases = baseline.get("cases", {})
    after_cases = after.get("cases", {})

    all_case_ids = set(baseline_cases.keys()) | set(after_cases.keys())

    for case_id in sorted(all_case_ids):
        report["summary"]["total"] += 1

        baseline_case = baseline_cases.get(case_id)
        after_case = after_cases.get(case_id)

        if baseline_case is None:
            report["diffs"].append({
                "case_id": case_id,
                "type": "new_case",
                "message": "新增用例（baseline 中不存在）"
            })
            report["summary"]["changed"] += 1
            continue

        if after_case is None:
            report["diffs"].append({
                "case_id": case_id,
                "type": "missing_case",
                "message": "用例丢失（after 中不存在）"
            })
            report["summary"]["changed"] += 1
            continue

        # 对比 CLI 输出（最重要：打印层输出必须不变）
        if baseline_case["cli_output_hash"] != after_case["cli_output_hash"]:
            report["diffs"].append({
                "case_id": case_id,
                "type": "cli_output_changed",
                "message": "CLI 打印输出发生变化",
                "baseline_hash": baseline_case["cli_output_hash"],
                "after_hash": after_case["cli_output_hash"],
                "baseline_output": baseline_case["cli_output"][:2000] + "..." if len(baseline_case["cli_output"]) > 2000 else baseline_case["cli_output"],
                "after_output": after_case["cli_output"][:2000] + "..." if len(after_case["cli_output"]) > 2000 else after_case["cli_output"],
            })
            report["summary"]["changed"] += 1
            continue

        # 对比关键字段（忽略新增的 metadata 字段如 yongshen_sources, shishen_by_layer）
        baseline_critical = _extract_critical_fields(baseline_case["facts_natal_json"])
        after_critical = _extract_critical_fields(after_case["facts_natal_json"])

        if baseline_critical != after_critical:
            report["diffs"].append({
                "case_id": case_id,
                "type": "critical_fields_changed",
                "message": "关键字段发生变化（影响最终输出）",
                "baseline": baseline_critical,
                "after": after_critical,
            })
            report["summary"]["changed"] += 1
            continue

        # 无变化
        report["summary"]["unchanged"] += 1

    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Regression Snapshot Tool")
    parser.add_argument("--mode", choices=["generate", "compare"], required=True)
    parser.add_argument("--output", help="输出快照文件路径")
    parser.add_argument("--baseline", help="基线快照文件路径")
    parser.add_argument("--after", help="变更后快照文件路径")

    args = parser.parse_args()

    if args.mode == "generate":
        if not args.output:
            print("Error: --output is required for generate mode", file=sys.stderr)
            sys.exit(1)

        snapshot = generate_snapshot(REGRESSION_CASES)

        # 确保目录存在
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

        print(f"Snapshot generated: {args.output}", file=sys.stderr)
        print(f"Total cases: {len(snapshot['cases'])}", file=sys.stderr)

    elif args.mode == "compare":
        if not args.baseline or not args.after:
            print("Error: --baseline and --after are required for compare mode", file=sys.stderr)
            sys.exit(1)

        with open(args.baseline, "r", encoding="utf-8") as f:
            baseline = json.load(f)

        with open(args.after, "r", encoding="utf-8") as f:
            after = json.load(f)

        report = compare_snapshots(baseline, after)

        print(json.dumps(report, ensure_ascii=False, indent=2))

        # 如果有变化，返回非零退出码
        if report["summary"]["changed"] > 0:
            print(f"\n❌ FAILED: {report['summary']['changed']} case(s) changed!", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"\n✅ PASSED: All {report['summary']['unchanged']} case(s) unchanged.", file=sys.stderr)


if __name__ == "__main__":
    main()
