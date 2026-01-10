#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归样本 facts 快照生成脚本。

用法：
    python scripts/generate_facts_snapshots.py          # 默认模式：跳过已存在的快照
    python scripts/generate_facts_snapshots.py --force  # 强制覆盖所有快照

说明：
    - 流年明细覆盖范围从出生年开始，不再从第一个有效大运起始年份开始
    - 快照中第一个组可能为 {"dayun": None, "liunian": [...]}，表示"大运开始之前的流年"
    - 流年明细最早年份为出生年（或接近出生年），不再依赖 luck.groups[0].dayun.start_year
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 注意：lunar_python 直接使用 datetime 的年月日时分秒，不关心时区
# 因此我们只需要创建一个 naive datetime 对象即可

from bazi.lunar_engine import analyze_complete


# 不稳定字段清单：这些字段会在每次运行时变化，需要被过滤或置空
UNSTABLE_FIELDS = [
    # 时间戳类
    "timestamp",
    "created_at",
    "updated_at",
    "generated_at",
    "runtime_ms",
    "execution_time",
    # ID类（如果包含随机性）
    "trace_id",
    "request_id",
    "session_id",
    # 随机数类
    "random_seed",
    "random_value",
    # 其他可能不稳定的字段
    "version_hash",
    "build_id",
]


def sanitize_facts(facts: Dict[str, Any], path: List[str] = None) -> Dict[str, Any]:
    """递归清理facts中的不稳定字段。
    
    参数:
        facts: 要清理的facts字典
        path: 当前路径（用于调试）
    
    返回:
        清理后的facts字典
    """
    if path is None:
        path = []
    
    if not isinstance(facts, dict):
        return facts
    
    result = {}
    for key, value in facts.items():
        current_path = path + [key]
        
        # 检查是否是不稳定字段
        if key in UNSTABLE_FIELDS:
            # 跳过不稳定字段，不添加到结果中
            continue
        
        # 递归处理嵌套字典
        if isinstance(value, dict):
            sanitized = sanitize_facts(value, current_path)
            if sanitized:  # 只添加非空字典
                result[key] = sanitized
        # 递归处理列表
        elif isinstance(value, list):
            sanitized_list = []
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    sanitized_item = sanitize_facts(item, current_path + [str(i)])
                    if sanitized_item:  # 只添加非空字典
                        sanitized_list.append(sanitized_item)
                else:
                    sanitized_list.append(item)
            result[key] = sanitized_list
        else:
            result[key] = value
    
    return result


def sort_dict_keys_recursively(obj: Any) -> Any:
    """递归地对字典的键进行排序，确保JSON输出稳定。
    
    参数:
        obj: 要排序的对象（字典、列表或其他）
    
    返回:
        排序后的对象
    """
    if isinstance(obj, dict):
        # 对字典的键进行排序
        sorted_dict = {}
        for key in sorted(obj.keys()):
            sorted_dict[key] = sort_dict_keys_recursively(obj[key])
        return sorted_dict
    elif isinstance(obj, list):
        # 递归处理列表中的每个元素
        return [sort_dict_keys_recursively(item) for item in obj]
    else:
        # 其他类型直接返回
        return obj


def generate_facts_snapshot(
    sample: Dict[str, Any],
    output_dir: Path,
    force: bool = False,
) -> tuple[bool, str]:
    """为单个样本生成facts快照。
    
    参数:
        sample: 样本字典，包含 id, birth_date, birth_time, timezone, is_male
        output_dir: 输出目录
        force: 是否强制覆盖已存在的快照
    
    返回:
        (是否生成, 消息)
    """
    sample_id = sample["id"]
    output_path = output_dir / f"{sample_id}.facts.json"
    
    # 检查文件是否已存在
    if output_path.exists() and not force:
        return False, f"跳过（已存在）：{sample_id}"
    
    # 解析日期时间
    birth_date_str = sample["birth_date"]
    birth_time_str = sample["birth_time"]
    timezone_str = sample.get("timezone", "Asia/Shanghai")
    
    # 解析日期和时间
    date_parts = birth_date_str.split("-")
    time_parts = birth_time_str.split(":")
    
    year = int(date_parts[0])
    month = int(date_parts[1])
    day = int(date_parts[2])
    hour = int(time_parts[0])
    minute = int(time_parts[1]) if len(time_parts) > 1 else 0
    second = 0
    
    # 创建datetime对象
    # 注意：lunar_python 直接使用 datetime 的年月日时分秒，不关心时区
    # 因此我们创建 naive datetime（不带时区信息）
    # timezone字段保存在样本中用于文档目的，但不影响计算
    try:
        birth_dt = datetime(year, month, day, hour, minute, second)
    except Exception as e:
        return False, f"错误（{sample_id}）：日期时间解析失败 - {e}"
    
    # 获取性别
    is_male = sample.get("is_male", True)
    
    # 调用facts生成入口
    try:
        facts = analyze_complete(birth_dt, is_male, max_dayun=15)
        
        # 为了快照稳定，固定 last5_hit 和 last5_years 的计算基准年份
        # 使用快照生成时的固定年份（2024年）作为基准，确保每次运行结果一致
        # 注意：实际使用时，Router 应该使用当前年份重新计算 last5_hit
        from datetime import datetime as dt
        snapshot_base_year = 2024  # 固定快照基准年份
        
        if "indexes" in facts and "relationship" in facts["indexes"]:
            relationship = facts["indexes"]["relationship"]
            # 重新计算 last5_hit 和 last5_years，使用固定基准年份
            relationship_years = relationship.get("years", [])
            last5_years_list = [
                y for y in relationship_years 
                if (snapshot_base_year - 5) <= y < snapshot_base_year
            ]
            relationship["last5_hit"] = len(last5_years_list) > 0
            relationship["last5_years"] = sorted(last5_years_list)
    except Exception as e:
        return False, f"错误（{sample_id}）：facts生成失败 - {e}"
    
    # 清理不稳定字段
    sanitized_facts = sanitize_facts(facts)
    
    # 排序键以确保稳定性
    sorted_facts = sort_dict_keys_recursively(sanitized_facts)
    
    # 写入JSON文件
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                sorted_facts,
                f,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,  # 额外确保排序（虽然已经递归排序了）
            )
        return True, f"生成：{sample_id} -> {output_path}"
    except Exception as e:
        return False, f"错误（{sample_id}）：文件写入失败 - {e}"


def main():
    """主函数。"""
    parser = argparse.ArgumentParser(
        description="生成回归样本的facts快照",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖已存在的快照文件",
    )
    parser.add_argument(
        "--samples",
        type=str,
        default="tests/regression/samples.json",
        help="样本输入文件路径（默认：tests/regression/samples.json）",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="tests/regression/snapshots/facts",
        help="输出目录（默认：tests/regression/snapshots/facts）",
    )
    
    args = parser.parse_args()
    
    # 读取样本文件
    samples_path = Path(args.samples)
    if not samples_path.exists():
        print(f"错误：样本文件不存在：{samples_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(samples_path, "r", encoding="utf-8") as f:
            samples = json.load(f)
    except Exception as e:
        print(f"错误：无法读取样本文件：{e}", file=sys.stderr)
        sys.exit(1)
    
    # 验证样本格式
    required_fields = ["id", "birth_date", "birth_time"]
    for sample in samples:
        for field in required_fields:
            if field not in sample:
                print(f"错误：样本缺少必需字段 '{field}'：{sample.get('id', 'unknown')}", file=sys.stderr)
                sys.exit(1)
    
    # 输出目录
    output_dir = Path(args.output_dir)
    
    # 生成快照
    generated = []
    skipped = []
    errors = []
    
    print(f"读取样本文件：{samples_path}")
    print(f"输出目录：{output_dir}")
    print(f"模式：{'强制覆盖' if args.force else '跳过已存在'}")
    print("")
    
    for sample in samples:
        sample_id = sample["id"]
        is_generated, message = generate_facts_snapshot(sample, output_dir, force=args.force)
        
        if "错误" in message:
            errors.append(message)
            print(f"[错误] {message}")
        elif is_generated:
            generated.append(sample_id)
            print(f"[生成] {message}")
        else:
            skipped.append(sample_id)
            print(f"[跳过] {message}")
    
    # 打印摘要
    print("")
    print("=" * 60)
    print("摘要：")
    print(f"  生成：{len(generated)} 个")
    if generated:
        for sid in generated:
            print(f"    - {sid}")
    
    print(f"  跳过：{len(skipped)} 个")
    if skipped:
        for sid in skipped:
            print(f"    - {sid}")
    
    print(f"  错误：{len(errors)} 个")
    if errors:
        for err in errors:
            print(f"    - {err}")
    
    print("")
    print(f"输出路径：{output_dir.absolute()}")
    
    # 如果有错误，退出码为非0
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()

