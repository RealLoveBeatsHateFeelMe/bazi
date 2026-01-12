#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一入口：生成 facts snapshots 和 index samples。

用法：
    python scripts/build_samples.py          # 默认模式：强制覆盖
    python scripts/build_samples.py --force  # 明确指定强制覆盖（与默认相同）

说明：
    1. 先生成 facts snapshots（回归测试用）
    2. 再生成 index samples（展示/门控用，基于 facts snapshots）
    3. 统一使用 tests/regression/samples.json 作为数据源
    4. base_year 自动使用服务器当前年份
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入 facts 生成逻辑
# 注意：需要先添加 scripts 目录到路径
sys.path.insert(0, str(project_root / "scripts"))
from generate_facts_snapshots import (
    generate_facts_snapshot,
    sort_dict_keys_recursively,
)
from bazi.request_index import generate_request_index


def generate_index_from_facts_snapshot(
    sample_id: str,
    facts_snapshot_path: Path,
    base_year: int,
    quota: Dict[str, Any],
    accesses_future: bool,
    output_path: Path,
) -> tuple[bool, str]:
    """从 facts snapshot 生成 index sample。
    
    参数:
        sample_id: 样本ID
        facts_snapshot_path: facts snapshot 文件路径
        base_year: 基准年份
        quota: 配额信息
        accesses_future: 本次请求是否访问未来数据
        output_path: 输出文件路径
    
    返回:
        (是否生成, 消息)
    """
    # 读取 facts snapshot
    if not facts_snapshot_path.exists():
        return False, f"错误（{sample_id}）：facts snapshot 不存在 - {facts_snapshot_path}"
    
    try:
        with open(facts_snapshot_path, "r", encoding="utf-8") as f:
            facts = json.load(f)
    except Exception as e:
        return False, f"错误（{sample_id}）：facts snapshot 读取失败 - {e}"
    
    # 生成 index
    try:
        index = generate_request_index(facts, base_year, quota=quota, accesses_future=accesses_future)
    except Exception as e:
        return False, f"错误（{sample_id}）：index生成失败 - {e}"
    
    # 排序键以确保稳定性
    sorted_index = sort_dict_keys_recursively(index)
    
    # 写入JSON文件
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                sorted_index,
                f,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        return True, f"生成：{sample_id} -> {output_path}"
    except Exception as e:
        return False, f"错误（{sample_id}）：文件写入失败 - {e}"


def main():
    """主函数。"""
    parser = argparse.ArgumentParser(
        description="统一入口：生成 facts snapshots 和 index samples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=True,  # 默认强制覆盖
        help="强制覆盖已存在的文件（默认：True）",
    )
    parser.add_argument(
        "--samples",
        type=str,
        default="tests/regression/samples.json",
        help="样本输入文件路径（默认：tests/regression/samples.json）",
    )
    parser.add_argument(
        "--facts-output-dir",
        type=str,
        default="tests/regression/snapshots/facts",
        help="facts snapshots 输出目录（默认：tests/regression/snapshots/facts）",
    )
    parser.add_argument(
        "--index-output-dir",
        type=str,
        default="scripts/index_samples",
        help="index samples 输出目录（默认：scripts/index_samples）",
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
    facts_output_dir = Path(args.facts_output_dir)
    index_output_dir = Path(args.index_output_dir)
    
    # 获取当前年份（base_year）
    base_year = datetime.now().year
    
    # 步骤1：生成 facts snapshots
    print("=" * 60)
    print("步骤1：生成 facts snapshots")
    print("=" * 60)
    print(f"读取样本文件：{samples_path}")
    print(f"输出目录：{facts_output_dir}")
    print(f"模式：{'强制覆盖' if args.force else '跳过已存在'}")
    print("")
    
    facts_generated = []
    facts_skipped = []
    facts_errors = []
    
    for sample in samples:
        sample_id = sample["id"]
        is_generated, message = generate_facts_snapshot(sample, facts_output_dir, force=args.force)
        
        if "错误" in message:
            facts_errors.append(message)
            print(f"[错误] {message}")
        elif is_generated:
            facts_generated.append(sample_id)
            print(f"[生成] {message}")
        else:
            facts_skipped.append(sample_id)
            print(f"[跳过] {message}")
    
    # 打印 facts 摘要
    print("")
    print("-" * 60)
    print("Facts 摘要：")
    print(f"  生成：{len(facts_generated)} 个")
    if facts_generated:
        for sid in facts_generated:
            print(f"    - {sid}")
    print(f"  跳过：{len(facts_skipped)} 个")
    if facts_skipped:
        for sid in facts_skipped:
            print(f"    - {sid}")
    print(f"  错误：{len(facts_errors)} 个")
    if facts_errors:
        for err in facts_errors:
            print(f"    - {err}")
    
    if facts_errors:
        print("\n错误：facts snapshots 生成失败，终止")
        sys.exit(1)
    
    # 步骤2：生成 index samples（基于 facts snapshots）
    print("")
    print("=" * 60)
    print("步骤2：生成 index samples")
    print("=" * 60)
    print(f"输出目录：{index_output_dir}")
    print(f"base_year：{base_year}（服务器当前年份）")
    print("")
    
    # 定义固定的 4 份 index 样例配置
    index_configs = [
        {
            "filename": "index_sample_free_overall_recent.json",
            "sample_id": "黄金A",
            "quota": {
                "tier": "free",
                "backend_allowed": True,
                "future_allowed": False,
                "token_budget": {"remaining": None, "limit": None, "reset_at": None},
            },
            "accesses_future": False,  # 过去请求
            "description": "免费用户（future_locked）+ overall_recent（过去请求）",
        },
        {
            "filename": "index_sample_free_future3.json",
            "sample_id": "黄金A",
            "quota": {
                "tier": "free",
                "backend_allowed": True,
                "future_allowed": False,
                "token_budget": {"remaining": None, "limit": None, "reset_at": None},
            },
            "accesses_future": True,  # 未来请求
            "description": "免费用户（future_locked）+ future3（未来请求）",
        },
        {
            "filename": "index_sample_paid_find_good_year.json",
            "sample_id": "黄金A",
            "quota": {
                "tier": "paid",
                "backend_allowed": True,
                "future_allowed": True,
                "token_budget": {"remaining": None, "limit": None, "reset_at": None},
            },
            "accesses_future": True,  # 未来请求
            "description": "付费用户（future_allowed）+ find_good_year（未来请求）",
        },
        {
            "filename": "index_sample_no_swap.json",
            "sample_id": "黄金B",
            "quota": {
                "tier": "free",
                "backend_allowed": True,
                "future_allowed": False,
                "token_budget": {"remaining": None, "limit": None, "reset_at": None},
            },
            "accesses_future": False,  # 过去请求
            "description": "无用神互换对照（has_swap=false）",
        },
    ]
    
    index_generated = []
    index_errors = []
    
    # 验证所需样本是否存在
    required_sample_ids = set(config["sample_id"] for config in index_configs)
    available_sample_ids = set(sample["id"] for sample in samples)
    missing_sample_ids = required_sample_ids - available_sample_ids
    if missing_sample_ids:
        print(f"错误：缺少必需的样本ID：{', '.join(missing_sample_ids)}")
        sys.exit(1)
    
    # 生成 index samples
    for config in index_configs:
        sample_id = config["sample_id"]
        facts_snapshot_path = facts_output_dir / f"{sample_id}.facts.json"
        
        print(f"生成：{config['filename']} ({config['description']})...")
        success, msg = generate_index_from_facts_snapshot(
            sample_id=sample_id,
            facts_snapshot_path=facts_snapshot_path,
            base_year=base_year,
            quota=config["quota"],
            accesses_future=config["accesses_future"],
            output_path=index_output_dir / config["filename"],
        )
        
        if "错误" in msg:
            index_errors.append(msg)
            print(f"  [错误] {msg}")
        elif success:
            index_generated.append(config["filename"])
            print(f"  [生成] {msg}")
        else:
            print(f"  [跳过] {msg}")
    
    # 打印 index 摘要
    print("")
    print("-" * 60)
    print("Index 摘要：")
    print(f"  生成：{len(index_generated)} 个")
    if index_generated:
        for filename in index_generated:
            print(f"    - {filename}")
    print(f"  错误：{len(index_errors)} 个")
    if index_errors:
        for err in index_errors:
            print(f"    - {err}")
    
    # 最终摘要
    print("")
    print("=" * 60)
    print("最终摘要")
    print("=" * 60)
    print(f"Facts snapshots: {len(facts_generated)} 个生成")
    print(f"Index samples: {len(index_generated)} 个生成")
    print(f"base_year: {base_year}")
    print("")
    print(f"Facts 输出路径：{facts_output_dir.absolute()}")
    print(f"Index 输出路径：{index_output_dir.absolute()}")
    
    if index_errors:
        print("\n错误：部分 index samples 生成失败")
        sys.exit(1)


if __name__ == "__main__":
    main()

