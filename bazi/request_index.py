# -*- coding: utf-8 -*-
"""
Request Index v0 生成：从 facts 派生请求级索引。

注意：
- Index 是请求级派生快照：随 base_year（服务器本地年）变化，尤其 last5/last3
- Index 只做抽取/汇总，不做解释，不扫 events 大段文本
- 字段缺失必须保守默认（空列表/false/空字符串），字段名稳定不改
- facts 是唯一真相源，Index 从 facts 派生，不做额外推理
"""

from typing import Any, Dict, List, Optional
from datetime import datetime


def _get_scan_horizon_end_year(facts: Dict[str, Any]) -> int:
    """获取扫描终点年份（facts 支持的最晚可计算年份）。
    
    从 luck.groups 中找到最后一个大运的结束年份。
    """
    luck = facts.get("luck", {})
    groups = luck.get("groups", [])
    
    if not groups:
        return 2100  # 保守默认
    
    # 找到最后一个有效大运
    last_valid_group = None
    for group in reversed(groups):
        dayun = group.get("dayun")
        if dayun is not None:
            last_valid_group = group
            break
    
    if last_valid_group is None:
        return 2100  # 保守默认
    
    dayun = last_valid_group.get("dayun")
    start_year = dayun.get("start_year")
    if start_year is None:
        return 2100  # 保守默认
    
    # 最后一个大运的结束年份 = start_year + 9（或下一个大运起始年份 - 1）
    # 这里简化处理，使用 start_year + 9
    return start_year + 9


def generate_request_index(
    facts: Dict[str, Any],
    base_year: int,
) -> Dict[str, Any]:
    """生成 Request Index v0。
    
    参数:
        facts: 完整的 facts 数据（来自 analyze_complete）
        base_year: 服务器本地年份（用于计算 last5/last3）
    
    返回:
        Request Index v0 字典
    """
    # 1) index.meta（时间范围）
    meta = {
        "index_version": "0.1.0",
        "base_year": base_year,
        "last5_years": [base_year, base_year - 1, base_year - 2, base_year - 3, base_year - 4],  # 必须含当年
        "last3_years": [base_year, base_year - 1, base_year - 2],
        "future3_years": [base_year, base_year + 1, base_year + 2],  # 从今年开始的未来三年
        "scan_horizon_end_year": _get_scan_horizon_end_year(facts),  # 用于"未来三年无好运 → 继续往后找最近好运年"
    }
    
    # 2) index.dayun（确保"当前大运"永远抓对）
    dayun_index = _build_dayun_index(facts, base_year)
    
    # 3) index.turning_points（临近才提）
    turning_points_index = _build_turning_points_index(facts, base_year)
    
    # 4) index.year_grade（同时产出 last5 + future3）
    year_grade_index = _build_year_grade_index(facts, meta["last5_years"], meta["future3_years"])
    
    # 5) index.good_year_search（新增：从今年起找好运年/第几年好运）
    good_year_search_index = _build_good_year_search_index(facts, base_year, meta["future3_years"], meta["scan_horizon_end_year"])
    
    # 6) index.relationship（只提示窗口，不展开）
    relationship_index = _build_relationship_index(facts, meta["last5_years"])
    
    return {
        "meta": meta,
        "dayun": dayun_index,
        "turning_points": turning_points_index,
        "year_grade": year_grade_index,
        "good_year_search": good_year_search_index,
        "relationship": relationship_index,
    }


def _build_dayun_index(facts: Dict[str, Any], base_year: int) -> Dict[str, Any]:
    """构建 dayun 索引。
    
    必须字段：
    - current_dayun: 当前大运摘要（至少包含起止年 + 好运/一般/坏运标签）
    - yongshen_swap: 用神互换信息
    """
    luck = facts.get("luck", {})
    groups = luck.get("groups", [])
    
    # 找到当前年份所在的大运
    current_dayun_obj = None
    current_dayun_index = None
    current_dayun_end_year = None
    
    for idx, group in enumerate(groups):
        dayun = group.get("dayun")
        if dayun is None:
            continue
        
        start_year = dayun.get("start_year")
        if start_year is None:
            continue
        
        # 计算结束年份（下一个大运起始年份 - 1，或当前大运起始年份 + 9）
        end_year = start_year + 9
        if idx + 1 < len(groups):
            next_group = groups[idx + 1]
            next_dayun = next_group.get("dayun")
            if next_dayun:
                next_start_year = next_dayun.get("start_year")
                if next_start_year:
                    end_year = next_start_year - 1
        
        if start_year <= base_year <= end_year:
            current_dayun_obj = dayun
            current_dayun_index = dayun.get("index")
            current_dayun_end_year = end_year
            break
    
    # 构建 current_dayun_ref（确保"当前大运"永远抓对；不存大段文案，不存整本大运）
    if current_dayun_obj:
        # 确定 fortune_label：从 dayun_label 映射到 "好运" / "一般" / "坏运"
        dayun_label = current_dayun_obj.get("dayun_label", "一般")
        is_good = current_dayun_obj.get("is_good", False)
        is_very_good = current_dayun_obj.get("is_very_good", False)
        
        # 映射 fortune_label
        if is_very_good or (is_good and "好运" in dayun_label):
            fortune_label = "好运"
        elif "坏运" in dayun_label or "变动过大" in dayun_label:
            fortune_label = "坏运"
        else:
            fortune_label = "一般"
        
        # 构建简洁的 label（只包含干支）
        gan = current_dayun_obj.get("gan", "")
        zhi = current_dayun_obj.get("zhi", "")
        label = f"{gan}{zhi}" if gan and zhi else ""
        
        current_dayun_ref = {
            "label": label,  # 例如 "壬午"
            "start_year": current_dayun_obj.get("start_year"),
            "end_year": current_dayun_end_year if current_dayun_end_year is not None else (current_dayun_obj.get("start_year", 0) + 9),
            "fortune_label": fortune_label,  # "好运" / "一般" / "坏运"
        }
    else:
        # 保守默认：空对象
        current_dayun_ref = {
            "label": "",
            "start_year": None,
            "end_year": None,
            "fortune_label": "一般",
        }
    
    # 构建 yongshen_swap（从 facts 的 indexes.dayun.yongshen_shift 派生）
    yongshen_shift = facts.get("indexes", {}).get("dayun", {}).get("yongshen_shift", {})
    has_swap = yongshen_shift.get("hit", False)
    windows = yongshen_shift.get("windows", [])
    
    # 转换为 items 格式（只包含可审计的最小信息）
    items: List[Dict[str, Any]] = []
    hint = ""
    
    if has_swap and windows:
        for window in windows:
            items.append({
                "dayun_seq": window.get("dayun_seq"),
                "year_range": window.get("year_range", {}),
                "from_elements": window.get("from_elements", []),
                "to_elements": window.get("to_elements", []),
            })
        
        # 生成 hint（只做汇总，不展开）
        if len(items) == 1:
            year_range = items[0].get("year_range", {})
            start_year = year_range.get("start_year", 0)
            end_year = year_range.get("end_year", 0)
            hint = f"存在用神侧重变化窗口（{start_year}-{end_year}年，仅提示变动，不展开原因；需要可继续追问）"
        else:
            hint = f"存在用神侧重变化窗口（共{len(items)}个窗口，仅提示变动，不展开原因；需要可继续追问）"
    
    return {
        "current_dayun_ref": current_dayun_ref,  # 改为 current_dayun_ref（简洁结构）
        "yongshen_swap": {
            "has_swap": has_swap,
            "items": items,  # 无互换则 []
            "hint": hint,    # 无互换则 ""（可选）
        },
    }


def _build_turning_points_index(facts: Dict[str, Any], base_year: int) -> Dict[str, Any]:
    """构建 turning_points 索引。
    
    必须字段：
    - all: list（可空，但字段必须存在）
    - nearby: list（all 裁剪到窗口 [base_year-3, base_year+3]）
    - should_mention: bool（nearby 非空即 true）
    """
    turning_points = facts.get("turning_points", [])
    
    # nearby 窗口：[base_year-3, base_year+3]（包含今年，前后各三年）
    nearby_window_start = base_year - 3
    nearby_window_end = base_year + 3
    
    nearby_list: List[Dict[str, Any]] = []
    for tp in turning_points:
        year = tp.get("year")
        if year is not None and nearby_window_start <= year <= nearby_window_end:
            nearby_list.append(tp)
    
    # 按年份排序（升序）
    nearby_list.sort(key=lambda x: x.get("year", 0))
    
    return {
        "all": turning_points,  # 可空，但字段必须存在
        "nearby": nearby_list,   # all 裁剪到窗口
        "should_mention": len(nearby_list) > 0,  # nearby 非空即 true
    }


def _build_year_grade_index(
    facts: Dict[str, Any], 
    last5_years: List[int],
    future3_years: List[int],
) -> Dict[str, Any]:
    """构建 year_grade 索引。
    
    必须字段：
    - last5: 长度=5，顺序严格按 last5_years 排序（year 从大到小）
    - future3: 长度=3，顺序严格按 future3_years 排序（year 从小到大）
    """
    luck = facts.get("luck", {})
    groups = luck.get("groups", [])
    
    # 收集所有流年数据到字典中（year -> liunian_dict）
    liunian_map: Dict[int, Dict[str, Any]] = {}
    for group in groups:
        liunian_list = group.get("liunian", [])
        for ln in liunian_list:
            year = ln.get("year")
            if year is not None:
                liunian_map[year] = ln
    
    # 构建 last5 列表（按 last5_years 顺序，year 从大到小）
    last5_list: List[Dict[str, Any]] = []
    for year in last5_years:  # 已经是 [base_year, base_year-1, ...] 顺序（从大到小）
        year_obj = _build_year_grade_item(year, liunian_map)
        last5_list.append(year_obj)
    
    # 构建 future3 列表（按 future3_years 顺序，year 从小到大）
    future3_list: List[Dict[str, Any]] = []
    for year in future3_years:  # [base_year, base_year+1, base_year+2]
        year_obj = _build_year_grade_item(year, liunian_map)
        future3_list.append(year_obj)
    
    return {
        "last5": last5_list,    # 长度=5，顺序严格按 last5_years 排序（year 从大到小）
        "future3": future3_list, # 长度=3，顺序严格按 future3_years 排序（year 从小到大）
    }


def _build_year_grade_item(year: int, liunian_map: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    """构建单个 YearGrade 项。"""
    if year not in liunian_map:
        # 该年份不存在流年数据，使用保守默认
        return {
            "year": year,
            "Y": 0.0,
            "year_label": "一般",
        }
    
    ln = liunian_map[year]
    Y = ln.get("total_risk_percent", 0.0)
    
    # 计算 year_label（按用户最新口径）
    if Y >= 40.0:
        year_label = "全年 凶（棘手/意外）"
    elif Y >= 25.0:
        year_label = "全年 明显变动（可克服）"
    else:
        # Y < 25.0，必须输出上下半年
        risk_from_gan = ln.get("risk_from_gan", 0.0)
        risk_from_zhi = ln.get("risk_from_zhi", 0.0)
        is_gan_yongshen = ln.get("first_half_good", False)
        is_zhi_yongshen = ln.get("second_half_good", False)
        
        half1_label = _calc_half_year_label(risk_from_gan, is_gan_yongshen)
        half2_label = _calc_half_year_label(risk_from_zhi, is_zhi_yongshen)
        
        year_label = f"上半年 {half1_label}，下半年 {half2_label}"
    
    # 构建 year 对象
    year_obj: Dict[str, Any] = {
        "year": year,
        "Y": Y,
        "year_label": year_label,
    }
    
    # 当 Y < 25.0 时，必须额外输出两个 half（从流年数据中获取）
    if Y < 25.0:
        risk_from_gan = ln.get("risk_from_gan", 0.0)
        risk_from_zhi = ln.get("risk_from_zhi", 0.0)
        is_gan_yongshen = ln.get("first_half_good", False)
        is_zhi_yongshen = ln.get("second_half_good", False)
        
        year_obj["half1"] = {
            "H": risk_from_gan,
            "half_label": _calc_half_year_label(risk_from_gan, is_gan_yongshen),
        }
        year_obj["half2"] = {
            "H": risk_from_zhi,
            "half_label": _calc_half_year_label(risk_from_zhi, is_zhi_yongshen),
        }
    
    return year_obj


def _calc_half_year_label(H: float, is_yongshen: bool) -> str:
    """计算半年判词。
    
    规则（必须按用户最新口径）：
    - H <= 10.0：用神 → "好运"；非用神 → "一般"
    - 10.0 < H < 20.0："有轻微变动"
    - H >= 20.0："凶（棘手/意外）"
    """
    if H <= 10.0:
        return "好运" if is_yongshen else "一般"
    elif H < 20.0:
        return "有轻微变动"
    else:  # H >= 20.0
        return "凶（棘手/意外）"


def _build_good_year_search_index(
    facts: Dict[str, Any],
    base_year: int,
    future3_years: List[int],
    scan_horizon_end_year: int,
) -> Dict[str, Any]:
    """构建 good_year_search 索引。
    
    必有字段（永远存在，找不到就空/Null）：
    - rule: "half1_or_half2_label_is_好运"
    - future3_good_years: [year...]
    - has_good_in_future3: bool
    - next_good_year: int | null（未来三年都没好运时，从 base_year 往后继续找最近好运年）
    - next_good_year_offset: int | null（next_good_year - base_year）
    - checked_years: [year...]（审计：到底扫了哪些年）
    
    好运年判定规则（写死）：
    只要该年 half1.half_label == "好运" 或 half2.half_label == "好运" 即认为该年是"好运年"
    """
    luck = facts.get("luck", {})
    groups = luck.get("groups", [])
    
    # 收集所有流年数据到字典中（year -> liunian_dict）
    liunian_map: Dict[int, Dict[str, Any]] = {}
    for group in groups:
        liunian_list = group.get("liunian", [])
        for ln in liunian_list:
            year = ln.get("year")
            if year is not None:
                liunian_map[year] = ln
    
    # 1. 检查 future3_years 中的好运年
    future3_good_years: List[int] = []
    checked_years: List[int] = list(future3_years)  # 先记录检查的年份
    
    for year in future3_years:
        if year not in liunian_map:
            continue
        
        ln = liunian_map[year]
        Y = ln.get("total_risk_percent", 0.0)
        
        # 只有当 Y < 25.0 时，才有 half1/half2
        if Y < 25.0:
            risk_from_gan = ln.get("risk_from_gan", 0.0)
            risk_from_zhi = ln.get("risk_from_zhi", 0.0)
            is_gan_yongshen = ln.get("first_half_good", False)
            is_zhi_yongshen = ln.get("second_half_good", False)
            
            half1_label = _calc_half_year_label(risk_from_gan, is_gan_yongshen)
            half2_label = _calc_half_year_label(risk_from_zhi, is_zhi_yongshen)
            
            # 好运年判定：half1 或 half2 的 half_label == "好运"
            if half1_label == "好运" or half2_label == "好运":
                future3_good_years.append(year)
    
    has_good_in_future3 = len(future3_good_years) > 0
    
    # 2. 如果未来三年没有好运，从 base_year 往后继续找
    next_good_year: Optional[int] = None
    next_good_year_offset: Optional[int] = None
    
    if not has_good_in_future3:
        # 从 future3_years 的最后一年 + 1 开始，直到 scan_horizon_end_year
        start_search_year = max(future3_years) + 1 if future3_years else base_year + 3
        
        for year in range(start_search_year, scan_horizon_end_year + 1):
            checked_years.append(year)  # 记录检查的年份
            
            if year not in liunian_map:
                continue
            
            ln = liunian_map[year]
            Y = ln.get("total_risk_percent", 0.0)
            
            # 只有当 Y < 25.0 时，才有 half1/half2
            if Y < 25.0:
                risk_from_gan = ln.get("risk_from_gan", 0.0)
                risk_from_zhi = ln.get("risk_from_zhi", 0.0)
                is_gan_yongshen = ln.get("first_half_good", False)
                is_zhi_yongshen = ln.get("second_half_good", False)
                
                half1_label = _calc_half_year_label(risk_from_gan, is_gan_yongshen)
                half2_label = _calc_half_year_label(risk_from_zhi, is_zhi_yongshen)
                
                # 好运年判定：half1 或 half2 的 half_label == "好运"
                if half1_label == "好运" or half2_label == "好运":
                    next_good_year = year
                    next_good_year_offset = year - base_year
                    break
    
    return {
        "rule": "half1_or_half2_label_is_好运",
        "future3_good_years": future3_good_years,
        "has_good_in_future3": has_good_in_future3,
        "next_good_year": next_good_year,          # int | null
        "next_good_year_offset": next_good_year_offset,  # int | null
        "checked_years": checked_years,            # 审计：到底扫了哪些年
    }


def _build_relationship_index(facts: Dict[str, Any], last5_years: List[int]) -> Dict[str, Any]:
    """构建 relationship 索引。
    
    必须字段：
    - hit: bool
    - years_hit: list[int]（命中列表）
    - last5_years_hit: list[int]（years_hit 与 last5_years 的交集，保持排序与 last5_years 一致）
    """
    relationship = facts.get("indexes", {}).get("relationship", {})
    years_hit = relationship.get("years", [])
    hit = relationship.get("hit", False)
    
    # last5_years_hit：years_hit 与 last5_years 的交集，保持排序与 last5_years 一致
    last5_years_set = set(last5_years)
    last5_years_hit = [y for y in last5_years if y in years_hit]
    
    return {
        "hit": hit,
        "years_hit": years_hit,        # 命中列表
        "last5_years_hit": last5_years_hit,  # years_hit 与 last5_years 的交集，保持排序与 last5_years 一致
    }

