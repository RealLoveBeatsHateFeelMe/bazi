#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 Request Index v0 样例 JSON。

用法：
    python scripts/generate_index_samples.py

说明：
    生成 4 份 index JSON 样例：
    1. index_sample_free_overall_recent.json - 免费用户（future_locked）+ overall_recent
    2. index_sample_free_future3.json - 免费用户（future_locked）+ future3
    3. index_sample_paid_find_good_year.json - 付费用户（future_allowed）+ find_good_year
    4. index_sample_no_swap.json - 无用神互换对照（has_swap=false）
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bazi.lunar_engine import analyze_complete
from bazi.request_index import generate_request_index


def sort_dict_keys_recursively(obj: Any) -> Any:
    """递归地对字典的键进行排序，确保JSON输出稳定。"""
    if isinstance(obj, dict):
        sorted_dict = {}
        for key in sorted(obj.keys()):
            sorted_dict[key] = sort_dict_keys_recursively(obj[key])
        return sorted_dict
    elif isinstance(obj, list):
        return [sort_dict_keys_recursively(item) for item in obj]
    else:
        return obj


def generate_index_sample(
    sample_id: str,
    birth_date_str: str,
    birth_time_str: str,
    is_male: bool,
    base_year: int,
    quota: Dict[str, Any],
    accesses_future: bool,
    output_path: Path,
) -> tuple[bool, str]:
    """生成单个 index 样例。
    
    参数:
        sample_id: 样本ID
        birth_date_str: 出生日期（格式：YYYY-MM-DD）
        birth_time_str: 出生时间（格式：HH:MM）
        is_male: 是否为男性
        base_year: 基准年份
        quota: 配额信息
        output_path: 输出文件路径
    
    返回:
        (是否生成, 消息)
    """
    # 解析日期时间
    date_parts = birth_date_str.split("-")
    time_parts = birth_time_str.split(":")
    
    year = int(date_parts[0])
    month = int(date_parts[1])
    day = int(date_parts[2])
    hour = int(time_parts[0])
    minute = int(time_parts[1]) if len(time_parts) > 1 else 0
    second = 0
    
    # 创建datetime对象
    try:
        birth_dt = datetime(year, month, day, hour, minute, second)
    except Exception as e:
        return False, f"错误（{sample_id}）：日期时间解析失败 - {e}"
    
    # 生成facts
    try:
        facts = analyze_complete(birth_dt, is_male, max_dayun=15)
    except Exception as e:
        return False, f"错误（{sample_id}）：facts生成失败 - {e}"
    
    # 生成index
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
    # 输出目录
    output_dir = project_root / "scripts" / "index_samples"
    
    # 基准年份
    base_year = 2025
    
    # 样例1：免费用户（future_locked）+ overall_recent（使用黄金A，有互换；过去请求）
    print("生成样例1：免费用户（future_locked）+ overall_recent...")
    success, msg = generate_index_sample(
        sample_id="黄金A",
        birth_date_str="2005-09-20",
        birth_time_str="10:00",
        is_male=True,
        base_year=base_year,
        quota={
            "tier": "free",
            "backend_allowed": True,
            "future_allowed": False,
            "token_budget": {"remaining": None, "limit": None, "reset_at": None},
        },
        accesses_future=False,  # 过去请求
        output_path=output_dir / "index_sample_free_overall_recent.json",
    )
    print(f"  {msg}")
    
    # 样例2：免费用户（future_locked）+ future3（使用黄金A；未来请求）
    print("生成样例2：免费用户（future_locked）+ future3...")
    success, msg = generate_index_sample(
        sample_id="黄金A",
        birth_date_str="2005-09-20",
        birth_time_str="10:00",
        is_male=True,
        base_year=base_year,
        quota={
            "tier": "free",
            "backend_allowed": True,
            "future_allowed": False,
            "token_budget": {"remaining": None, "limit": None, "reset_at": None},
        },
        accesses_future=True,  # 未来请求
        output_path=output_dir / "index_sample_free_future3.json",
    )
    print(f"  {msg}")
    
    # 样例3：付费用户（future_allowed）+ find_good_year（使用黄金A；未来请求）
    print("生成样例3：付费用户（future_allowed）+ find_good_year...")
    success, msg = generate_index_sample(
        sample_id="黄金A",
        birth_date_str="2005-09-20",
        birth_time_str="10:00",
        is_male=True,
        base_year=base_year,
        quota={
            "tier": "paid",
            "backend_allowed": True,
            "future_allowed": True,
            "token_budget": {"remaining": None, "limit": None, "reset_at": None},
        },
        accesses_future=True,  # 未来请求
        output_path=output_dir / "index_sample_paid_find_good_year.json",
    )
    print(f"  {msg}")
    
    # 样例4：无用神互换对照（has_swap=false）（使用黄金B；过去请求）
    print("生成样例4：无用神互换对照（has_swap=false）...")
    success, msg = generate_index_sample(
        sample_id="黄金B",
        birth_date_str="2007-01-28",
        birth_time_str="12:00",
        is_male=True,
        base_year=base_year,
        quota={
            "tier": "free",
            "backend_allowed": True,
            "future_allowed": False,
            "token_budget": {"remaining": None, "limit": None, "reset_at": None},
        },
        accesses_future=False,  # 过去请求
        output_path=output_dir / "index_sample_no_swap.json",
    )
    print(f"  {msg}")
    
    print("\n所有样例生成完成！")
    print(f"输出目录：{output_dir}")


if __name__ == "__main__":
    main()

