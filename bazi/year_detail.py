# -*- coding: utf-8 -*-
"""生成指定年份的 year_detail 结构化数据。

用于年请求（time_scope=year）的专用输出。
"""

from typing import Any, Dict, List, Optional
from .shishen import get_shishen, get_branch_main_gan, get_shishen_label


def generate_year_detail(
    facts: Dict[str, Any],
    target_year: int,
) -> Optional[Dict[str, Any]]:
    """生成指定年份的 year_detail 结构化数据。
    
    参数:
        facts: analyze_complete() 返回的完整 facts 数据
        target_year: 目标年份
    
    返回:
        {
            "year": 2026,
            "half_year_grade": { "first": "好运|一般|凶|变动", "second": "好运|一般|凶|变动" },
            "gan_block": { "gan", "shishen", "yongshen_yesno", "tags", "risk_pct" },
            "zhi_block": { "zhi", "shishen", "yongshen_yesno", "tags", "risk_pct" },
            "hint_summary_lines": [...],
            "dayun_brief": { "name", "start_year", "end_year", "grade" },
            "raw_text": "..."
        }
    """
    # 获取 natal 数据
    natal = facts.get("natal", {})
    bazi = natal.get("bazi", {})
    day_gan = bazi.get("day", {}).get("gan", "")
    yongshen_elements = natal.get("yongshen_elements", [])
    
    # 获取 luck 数据
    luck = facts.get("luck", {})
    groups = luck.get("groups", [])
    
    # 找到目标年份的流年数据
    target_liunian = None
    parent_dayun = None
    
    for group in groups:
        dayun = group.get("dayun")
        liunian_list = group.get("liunian", [])
        
        for liunian in liunian_list:
            if liunian.get("year") == target_year:
                target_liunian = liunian
                parent_dayun = dayun
                break
        
        if target_liunian:
            break
    
    if not target_liunian:
        return None
    
    # 1. 上下半年等级（四类枚举）
    half_year_grade = _compute_half_year_grade(target_liunian)
    
    # 2. 天干块
    gan_block = _build_gan_block(
        target_liunian, day_gan, yongshen_elements
    )
    
    # 3. 地支块
    zhi_block = _build_zhi_block(
        target_liunian, day_gan, yongshen_elements
    )
    
    # 4. 提示汇总
    hint_summary_lines = target_liunian.get("hints", [])
    if hint_summary_lines is None:
        hint_summary_lines = []
    
    # 5. 大运简述
    dayun_brief = _build_dayun_brief(parent_dayun, yongshen_elements)
    
    # 6. 生成 raw_text
    raw_text = _build_raw_text(
        target_year,
        half_year_grade,
        gan_block,
        zhi_block,
        hint_summary_lines,
        dayun_brief,
    )
    
    return {
        "year": target_year,
        "half_year_grade": half_year_grade,
        "gan_block": gan_block,
        "zhi_block": zhi_block,
        "hint_summary_lines": hint_summary_lines,
        "dayun_brief": dayun_brief,
        "raw_text": raw_text,
    }


def _compute_half_year_grade(liunian: Dict[str, Any]) -> Dict[str, str]:
    """计算开始/后来等级（四类枚举：好运/一般/凶/变动）。"""
    # 兼容映射：支持新字段 start_good/later_good 和旧字段 first_half_good/second_half_good
    start_good = liunian.get("start_good", liunian.get("first_half_good"))
    later_good = liunian.get("later_good", liunian.get("second_half_good"))
    risk_from_gan = liunian.get("risk_from_gan", 0.0)
    risk_from_zhi = liunian.get("risk_from_zhi", 0.0)

    # 开始判定
    if start_good is None:
        start_grade = "变动"
    elif start_good:
        if risk_from_gan > 20:
            start_grade = "一般"
        else:
            start_grade = "好运"
    else:
        if risk_from_gan > 30:
            start_grade = "凶"
        else:
            start_grade = "一般"

    # 后来判定
    if later_good is None:
        later_grade = "变动"
    elif later_good:
        if risk_from_zhi > 20:
            later_grade = "一般"
        else:
            later_grade = "好运"
    else:
        if risk_from_zhi > 30:
            later_grade = "凶"
        else:
            later_grade = "一般"

    return {
        "start": start_grade,
        "later": later_grade,
    }


def _build_gan_block(
    liunian: Dict[str, Any],
    day_gan: str,
    yongshen_elements: List[str],
) -> Dict[str, Any]:
    """构建天干块。"""
    liunian_gan = liunian.get("gan", "")
    gan_element = liunian.get("gan_element", "")
    risk_from_gan = liunian.get("risk_from_gan", 0.0)
    
    # 计算十神
    gan_shishen = get_shishen(day_gan, liunian_gan) if liunian_gan and day_gan else "-"
    
    # 是否用神
    is_yongshen = gan_element in yongshen_elements if gan_element else False
    
    # 标签
    tags = []
    if gan_shishen and gan_shishen != "-":
        label = get_shishen_label(gan_shishen, is_yongshen)
        if label:
            tags = [t.strip() for t in label.split("/") if t.strip()]
    
    return {
        "gan": liunian_gan,
        "shishen": gan_shishen,
        "yongshen_yesno": "是" if is_yongshen else "否",
        "tags": tags,
        "risk_pct": risk_from_gan,
    }


def _build_zhi_block(
    liunian: Dict[str, Any],
    day_gan: str,
    yongshen_elements: List[str],
) -> Dict[str, Any]:
    """构建地支块。"""
    liunian_zhi = liunian.get("zhi", "")
    zhi_element = liunian.get("zhi_element", "")
    risk_from_zhi = liunian.get("risk_from_zhi", 0.0)
    
    # 计算地支主气的十神
    zhi_main_gan = get_branch_main_gan(liunian_zhi) if liunian_zhi else None
    zhi_shishen = get_shishen(day_gan, zhi_main_gan) if zhi_main_gan and day_gan else "-"
    
    # 是否用神
    is_yongshen = zhi_element in yongshen_elements if zhi_element else False
    
    # 标签
    tags = []
    if zhi_shishen and zhi_shishen != "-":
        label = get_shishen_label(zhi_shishen, is_yongshen)
        if label:
            tags = [t.strip() for t in label.split("/") if t.strip()]
    
    return {
        "zhi": liunian_zhi,
        "shishen": zhi_shishen,
        "yongshen_yesno": "是" if is_yongshen else "否",
        "tags": tags,
        "risk_pct": risk_from_zhi,
    }


def _build_dayun_brief(
    dayun: Optional[Dict[str, Any]],
    yongshen_elements: List[str],
) -> Optional[Dict[str, Any]]:
    """构建大运简述。"""
    if not dayun:
        return None
    
    gan = dayun.get("gan", "")
    zhi = dayun.get("zhi", "")
    start_age = dayun.get("start_age", 0)
    end_age = dayun.get("end_age", 0)
    
    # 大运等级：只用"好"或"一般"
    zhi_good = dayun.get("zhi_good", False)
    grade = "好" if zhi_good else "一般"
    
    return {
        "name": f"{gan}{zhi}",
        "start_age": start_age,
        "end_age": end_age,
        "grade": grade,
    }


def _build_raw_text(
    year: int,
    half_year_grade: Dict[str, str],
    gan_block: Dict[str, Any],
    zhi_block: Dict[str, Any],
    hint_summary_lines: List[str],
    dayun_brief: Optional[Dict[str, Any]],
) -> str:
    """生成 raw_text 用于 debug 和兜底。"""
    lines = []
    
    # 年份标题
    lines.append(f"=== {year}年 ===")
    
    # 大运背景
    if dayun_brief:
        lines.append(f"【大运背景】{dayun_brief['name']}运（{dayun_brief['start_age']}-{dayun_brief['end_age']}岁），等级：{dayun_brief['grade']}")
    
    # 开始/后来
    lines.append(f"【开始/后来】开始：{half_year_grade['start']}，后来：{half_year_grade['later']}")
    
    # 天干
    gan = gan_block
    risk_str = f"危险系数：{gan['risk_pct']:.1f}%" if gan['risk_pct'] > 0 else "不易出现意外和风险"
    tags_str = "/".join(gan['tags']) if gan['tags'] else ""
    lines.append(f"【天干】{gan['gan']}｜十神 {gan['shishen']}｜用神 {gan['yongshen_yesno']}｜标签：{tags_str}｜{risk_str}")
    
    # 地支
    zhi = zhi_block
    risk_str = f"危险系数：{zhi['risk_pct']:.1f}%" if zhi['risk_pct'] > 0 else "不易出现意外和风险"
    tags_str = "/".join(zhi['tags']) if zhi['tags'] else ""
    lines.append(f"【地支】{zhi['zhi']}｜十神 {zhi['shishen']}｜用神 {zhi['yongshen_yesno']}｜标签：{tags_str}｜{risk_str}")
    
    # 提示汇总
    if hint_summary_lines:
        lines.append("【提示汇总】")
        for hint in hint_summary_lines:
            lines.append(f"  - {hint}")
    else:
        lines.append("【提示汇总】今年暂无额外提示汇总")
    
    return "\n".join(lines)

