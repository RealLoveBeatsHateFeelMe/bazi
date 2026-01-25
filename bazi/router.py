# -*- coding: utf-8 -*-
"""
Router：只读 index 决策 + 输出可审计结果。

注意：
- Router 输入：用户 query + index
- Router 输出必须写入 trace
- Router 只读 index，不扫 facts 全书
- Router 决定 modules
"""

from typing import Any, Dict, List, Tuple
import re


def route(
    query: str,
    index: Dict[str, Any],
) -> Tuple[str, List[str], List[int], List[str]]:
    """Router 主函数：识别意图并决定 modules 和 years。
    
    参数:
        query: 用户查询
        index: Request Index v0
    
    返回:
        (intent, modules, years_used, reasons)
        - intent: 意图标识（"overall_recent" | "recent_3_years" | "named_year" | "unknown"）
        - modules: 模块列表（如 ["DAYUN_OVERVIEW", "LAST5_YEAR_GRADE", "RELATIONSHIP_WINDOW"]）
        - years_used: 使用的年份列表（排序稳定）
        - reasons: 简短原因列表（用于 trace）
    """
    # 3.1 intent 识别最低限度（MVP）
    intent, years_used, intent_reasons = _identify_intent(query, index)
    
    # 决定 modules
    modules, module_reasons = _decide_modules(intent, index, years_used)
    
    # 合并 reasons
    reasons = intent_reasons + module_reasons
    
    return intent, modules, years_used, reasons


def _identify_intent(
    query: str,
    index: Dict[str, Any],
) -> Tuple[str, List[int], List[str]]:
    """识别用户意图。
    
    MVP Router v0 优先级（固定）：
    1. 点名年份 → named_year
    2. "第几年好运/哪年好运/好运年份" → find_good_year
    3. "未来/接下来/往后/未来三年" → future3
    4. "回放/近五年/五年" → replay_last5
    5. 默认 → overall_recent
    
    返回:
        (intent, years_used, reasons)
    """
    query_lower = query.lower()
    meta = index.get("meta", {})
    
    # 1. 检查是否点名某年（优先级最高）
    year_patterns = [
        r"(\d{4})\s*年",  # 2024年
        r"([一二三四五六七八九零]{4})\s*年",  # 中文年份（简化匹配）
    ]
    for pattern in year_patterns:
        match = re.search(pattern, query)
        if match:
            year_str = match.group(1)
            # 尝试解析年份（简化版，只处理数字）
            if year_str.isdigit():
                year = int(year_str)
                return (
                    "named_year",
                    [year],
                    [f"用户点名年份: {year}"],
                )
    
    # 2. 检查是否询问"第几年好运/哪年好运/好运年份"
    if re.search(r"第[几多少]年.*好运|哪[一年].*好运|好运.*年份|好运.*年|什么时候.*好运", query_lower):
        future3_years = meta.get("future3_years", [])
        return (
            "find_good_year",
            future3_years,  # 先使用 future3_years，Router 会从 index.good_year_search 获取结果
            [f"用户询问好运年份，使用 future3_years: {future3_years}，结果从 index.good_year_search 获取"],
        )
    
    # 3. 检查是否询问"未来/接下来/往后/未来三年"
    if re.search(r"未来|接下来|往后|未来三[年个]|接下来三[年个]", query_lower):
        future3_years = meta.get("future3_years", [])
        return (
            "future3",
            future3_years,
            [f"用户询问未来，使用 future3_years: {future3_years}"],
        )
    
    # 4. 检查是否询问"回放/近五年/五年"
    if re.search(r"回放|近五[年个]|五[年个]", query_lower):
        last5_years = meta.get("last5_years", [])
        return (
            "replay_last5",
            last5_years,
            [f"用户询问回放/近五年，使用 last5_years: {last5_years}"],
        )
    
    # 5. 检查是否明确说"三年/近三年"
    if re.search(r"三[年个]|近三[年个]", query_lower):
        last3_years = meta.get("last3_years", [])
        return (
            "recent_3_years",
            last3_years,
            [f"用户明确提及'三年'，使用 last3_years: {last3_years}"],
        )
    
    # 6. 默认：overall_recent（整体/最近几年/模糊时间）
    last5_years = meta.get("last5_years", [])
    return (
        "overall_recent",
        last5_years,
        [f"默认整体/最近几年查询，使用 last5_years: {last5_years}"],
    )


def _decide_modules(
    intent: str,
    index: Dict[str, Any],
    years_used: List[int],
) -> Tuple[List[str], List[str]]:
    """决定需要使用的 modules。
    
    MVP 至少要支持这几个 module 名称：
    - DAYUN_OVERVIEW（从 index.dayun / turning_points 取需要的摘要）
    - LAST5_YEAR_GRADE（从 index.year_grade.last5 取）
    - FUTURE3_YEAR_GRADE（从 index.year_grade.future3 取）
    - GOOD_YEAR_SEARCH（从 index.good_year_search 取）
    - RELATIONSHIP_WINDOW（从 index.relationship 取）
    
    返回:
        (modules, reasons)
    """
    modules: List[str] = []
    reasons: List[str] = []
    
    # 总是包含 DAYUN_OVERVIEW（"大运是气候"）
    modules.append("DAYUN_OVERVIEW")
    reasons.append("大运是气候，需要当前大运摘要")
    
    # 根据 intent 决定 modules
    if intent == "find_good_year":
        # 询问好运年份：需要 GOOD_YEAR_SEARCH
        modules.append("GOOD_YEAR_SEARCH")
        reasons.append("用户询问好运年份，从 index.good_year_search 获取结果")
    elif intent == "future3":
        # 询问未来三年：需要 FUTURE3_YEAR_GRADE
        modules.append("FUTURE3_YEAR_GRADE")
        reasons.append(f"用户询问未来三年，使用 future3_years: {years_used}")
    elif intent == "replay_last5":
        # 询问回放/近五年：需要 LAST5_YEAR_GRADE
        modules.append("LAST5_YEAR_GRADE")
        reasons.append(f"用户询问回放/近五年，使用 last5_years: {years_used}")
    elif intent in ("overall_recent", "recent_3_years"):
        # 整体/最近几年：需要 LAST5_YEAR_GRADE
        modules.append("LAST5_YEAR_GRADE")
        reasons.append(f"近{len(years_used)}年天气回放索引（Y < 25 时包含开始/后来）")
    elif intent == "named_year":
        # 点名某年：需要 LAST5_YEAR_GRADE（用于该年的详细信息）
        if years_used:
            modules.append("LAST5_YEAR_GRADE")
            reasons.append(f"点名年份 {years_used[0]} 的详细年表")
    
    # 检查 turning_points 是否需要提及
    turning_points = index.get("turning_points", {})
    should_mention = turning_points.get("should_mention", False)
    if should_mention:
        # turning_points 信息已经包含在 DAYUN_OVERVIEW 模块中，不需要单独模块
        nearby = turning_points.get("nearby", [])
        reasons.append(f"检测到临近转折点（窗口内共 {len(nearby)} 个），将在 DAYUN_OVERVIEW 中提及")
    
    # 检查 relationship 是否有命中
    relationship = index.get("relationship", {})
    hit = relationship.get("hit", False)
    if hit:
        modules.append("RELATIONSHIP_WINDOW")
        years_hit = relationship.get("years_hit", [])
        last5_years_hit = relationship.get("last5_years_hit", [])
        if last5_years_hit:
            reasons.append(f"检测到感情变动窗口（近5年命中: {last5_years_hit}）")
        else:
            reasons.append(f"检测到感情变动窗口（全期命中: {len(years_hit)} 年，近5年无）")
    
    return modules, reasons

