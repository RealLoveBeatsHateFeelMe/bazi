# -*- coding: utf-8 -*-
"""
Modules：只做 facts 切片，不推理。

注意：
- Modules 的职责：按计划切片 facts 或 index，喂给 LLM
- 不负责计算四档、不负责生成 turning points、不负责决定 years
- MVP 至少要支持这几个 module 名称：
  - DAYUN_OVERVIEW（从 index.dayun / turning_points 取需要的摘要）
  - LAST5_YEAR_GRADE（从 index.year_grade.last5 取）
  - RELATIONSHIP_WINDOW（从 index.relationship 取）
"""

from typing import Any, Dict, List


def get_module_input(
    module_name: str,
    index: Dict[str, Any],
) -> Dict[str, Any]:
    """获取指定 module 的输入数据。
    
    参数:
        module_name: 模块名称（如 "DAYUN_OVERVIEW"）
        index: Request Index v0
    
    返回:
        模块输入数据（字典）
    """
    if module_name == "DAYUN_OVERVIEW":
        return _get_dayun_overview_input(index)
    elif module_name == "LAST5_YEAR_GRADE":
        return _get_last5_year_grade_input(index)
    elif module_name == "FUTURE3_YEAR_GRADE":
        return _get_future3_year_grade_input(index)
    elif module_name == "GOOD_YEAR_SEARCH":
        return _get_good_year_search_input(index)
    elif module_name == "RELATIONSHIP_WINDOW":
        return _get_relationship_window_input(index)
    else:
        return {}


def _get_dayun_overview_input(index: Dict[str, Any]) -> Dict[str, Any]:
    """获取 DAYUN_OVERVIEW 模块的输入数据。
    
    从 index.dayun / turning_points 取需要的摘要。
    """
    dayun = index.get("dayun", {})
    turning_points = index.get("turning_points", {})
    
    return {
        "current_dayun_ref": dayun.get("current_dayun_ref", {}),  # 改为 current_dayun_ref
        "yongshen_swap": dayun.get("yongshen_swap", {}),
        "turning_points_nearby": turning_points.get("nearby", []),
        "should_mention_turning_points": turning_points.get("should_mention", False),
    }


def _get_last5_year_grade_input(index: Dict[str, Any]) -> Dict[str, Any]:
    """获取 LAST5_YEAR_GRADE 模块的输入数据。
    
    从 index.year_grade.last5 取。
    """
    year_grade = index.get("year_grade", {})
    return {
        "last5": year_grade.get("last5", []),
    }


def _get_future3_year_grade_input(index: Dict[str, Any]) -> Dict[str, Any]:
    """获取 FUTURE3_YEAR_GRADE 模块的输入数据。
    
    从 index.year_grade.future3 取。
    """
    year_grade = index.get("year_grade", {})
    return {
        "future3": year_grade.get("future3", []),
    }


def _get_good_year_search_input(index: Dict[str, Any]) -> Dict[str, Any]:
    """获取 GOOD_YEAR_SEARCH 模块的输入数据。
    
    从 index.good_year_search 取。
    """
    good_year_search = index.get("good_year_search", {})
    return {
        "rule": good_year_search.get("rule", ""),
        "future3_good_years": good_year_search.get("future3_good_years", []),
        "has_good_in_future3": good_year_search.get("has_good_in_future3", False),
        "next_good_year": good_year_search.get("next_good_year"),
        "next_good_year_offset": good_year_search.get("next_good_year_offset"),
        "checked_years": good_year_search.get("checked_years", []),
    }


def _get_relationship_window_input(index: Dict[str, Any]) -> Dict[str, Any]:
    """获取 RELATIONSHIP_WINDOW 模块的输入数据。
    
    从 index.relationship 取。
    """
    relationship = index.get("relationship", {})
    return {
        "hit": relationship.get("hit", False),
        "years_hit": relationship.get("years_hit", []),
        "last5_years_hit": relationship.get("last5_years_hit", []),
    }


def get_module_inputs_trace(
    modules: List[str],
    index: Dict[str, Any],
) -> Dict[str, List[str]]:
    """获取所有 modules 的输入数据来源追踪（用于 trace）。
    
    返回:
        {module_name: [source_path, ...]}
        例如: {"DAYUN_OVERVIEW": ["index.dayun.current_dayun_ref", "index.dayun.yongshen_swap", ...]}
    """
    trace_map: Dict[str, List[str]] = {}
    
    for module_name in modules:
        sources: List[str] = []
        
        if module_name == "DAYUN_OVERVIEW":
            sources = [
                "index.dayun.current_dayun_ref",
                "index.dayun.yongshen_swap",
                "index.turning_points.nearby",
            ]
        elif module_name == "LAST5_YEAR_GRADE":
            sources = [
                "index.year_grade.last5",
            ]
        elif module_name == "FUTURE3_YEAR_GRADE":
            sources = [
                "index.year_grade.future3",
            ]
        elif module_name == "GOOD_YEAR_SEARCH":
            sources = [
                "index.good_year_search",
            ]
        elif module_name == "RELATIONSHIP_WINDOW":
            sources = [
                "index.relationship",
            ]
        
        trace_map[module_name] = sources
    
    return trace_map

