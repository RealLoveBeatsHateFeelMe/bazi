# -*- coding: utf-8 -*-
"""Relationship Index (Index-5) 生成：感情变动窗口白名单口径。

基于以下两类触发条件判定 relationship_hit：
A. 冲到婚姻宫/夫妻宫
B. 天干争合官杀/财星
"""

from typing import Any, Dict, List, Set, Optional
from datetime import datetime

from .config import PILLAR_PALACE, PILLAR_PALACE_CN
from .marriage_wuhe import detect_marriage_wuhe_hints, get_spouse_star_and_competitor
from .shishen import get_shishen, classify_shishen_category


# Relationship 类型枚举值
RELATIONSHIP_TYPE_PALACE_CLASH = "palace_clash"  # 冲到婚姻宫/夫妻宫
RELATIONSHIP_TYPE_COMPETING_COMBINE_OFFICIAL_KILL = "competing_combine_official_kill"  # 天干争合官杀
RELATIONSHIP_TYPE_COMPETING_COMBINE_WEALTH = "competing_combine_wealth"  # 天干争合财星


def _is_marriage_palace(pillar: str) -> bool:
    """判断柱位是否是婚姻宫或夫妻宫。
    
    参数:
        pillar: 柱位名称（"year", "month", "day", "hour"）
    
    返回:
        True 如果是婚姻宫或夫妻宫，否则 False
    """
    # 月柱 = 婚姻宫，日柱 = 夫妻宫
    return pillar in ("month", "day")


def _check_clash_hits_marriage_palace(clash_event: Dict[str, Any]) -> bool:
    """检查冲事件是否命中婚姻宫/夫妻宫。
    
    参数:
        clash_event: 冲事件字典（来自 all_events，type="branch_clash"）
    
    返回:
        True 如果命中婚姻宫/夫妻宫，否则 False
    """
    targets = clash_event.get("targets", [])
    if not targets:
        return False
    
    # 检查所有目标是否命中婚姻宫/夫妻宫
    for target in targets:
        pillar = target.get("pillar", "")
        if _is_marriage_palace(pillar):
            return True
    
    return False


def _check_competing_combine_hits_spouse_star(
    wuhe_events: List[Dict[str, Any]],
    day_gan: str,
    is_male: bool,
) -> tuple[bool, Optional[str]]:
    """检查天干争合是否命中官杀/财星。
    
    参数:
        wuhe_events: 该年的天干五合事件列表（来自 liunian.wuhe_events）
        day_gan: 日主天干
        is_male: 是否为男性
    
    返回:
        (是否命中, 类型字符串) 或 (False, None)
        类型字符串为：competing_combine_official_kill 或 competing_combine_wealth
    
    注意：此函数复用现有的 gan_wuhe 检测结果，只判断争合是否命中官杀/财星。
    
    业务逻辑：
    - 在争合中，few_side（少的一侧）是被争合的目标，many_side（多的一侧）是争合的一方
    - 检查 few_side 的十神是否是官杀（女命）或财星（男命）
    """
    if not wuhe_events:
        return (False, None)
    
    # 获取配偶星X（用于验证被争合的目标是否是X）
    mapping = get_spouse_star_and_competitor(day_gan, is_male)
    if not mapping:
        return (False, None)
    
    X, Y, wuhe_name = mapping  # X是配偶星（官杀或财星），Y是争合字
    
    # 遍历所有五合事件，查找争合（is_zhenghe=True）
    for event in wuhe_events:
        is_zhenghe = event.get("is_zhenghe", False)
        if not is_zhenghe:
            continue  # 只关注争合，跳过普通1对1合
        
        # 获取参与争合的天干对
        gan_pair = event.get("gan_pair", [])
        if len(gan_pair) != 2:
            continue
        
        # 获取争合目标（few_side）的天干和十神
        # 在争合中，few_side（少的一侧）是被争合的目标
        few_side = event.get("few_side", [])
        many_side = event.get("many_side", [])
        
        if not few_side or not many_side:
            continue
        
        # 检查 few_side 的天干是否是配偶星X（官杀或财星）
        for pos in few_side:
            # pos 可能是 dict（已序列化）或 GanPosition（未序列化）
            if isinstance(pos, dict):
                pos_gan = pos.get("gan", "")
                pos_shishen = pos.get("shishen", "")
            else:
                pos_gan = pos.gan
                pos_shishen = pos.shishen
            
            # 检查 few_side 的天干是否是配偶星X
            if pos_gan == X:
                # 验证十神类别（双重检查）
                if pos_shishen:
                    category = classify_shishen_category(pos_shishen)
                    if not is_male:
                        # 女命：检查是否命中官杀
                        if category == "官杀":
                            return (True, RELATIONSHIP_TYPE_COMPETING_COMBINE_OFFICIAL_KILL)
                    else:
                        # 男命：检查是否命中财星
                        if category == "财星":
                            return (True, RELATIONSHIP_TYPE_COMPETING_COMBINE_WEALTH)
                else:
                    # 如果十神为空，但天干匹配X，也认为命中（因为X的定义就是官杀/财星）
                    if not is_male:
                        return (True, RELATIONSHIP_TYPE_COMPETING_COMBINE_OFFICIAL_KILL)
                    else:
                        return (True, RELATIONSHIP_TYPE_COMPETING_COMBINE_WEALTH)
    
    return (False, None)


def generate_relationship_index(
    luck_data: Dict[str, Any],
    bazi: Dict[str, Dict[str, str]],
    day_gan: str,
    is_male: bool,
    current_year: Optional[int] = None,
) -> Dict[str, Any]:
    """生成 Relationship Index (Index-5)。
    
    参数:
        luck_data: analyze_luck 返回的 luck 数据
        bazi: 八字字典
        day_gan: 日主天干
        is_male: 是否为男性
        current_year: 当前年份（用于计算 last5_hit 和 last5_years），如果为None则使用当前系统年份
    
    返回:
        Relationship Index 字典：
        {
            "hit": bool,
            "types": List[str],  # 允许值：palace_clash, competing_combine_official_kill, competing_combine_wealth
            "years": List[int],  # 命中的年份列表，排序稳定
            "last5_hit": bool,
            "last5_years": List[int],  # 近5年命中的年份列表，排序稳定
        }
    """
    if current_year is None:
        current_year = datetime.now().year
    
    hit_years: Set[int] = set()
    relationship_types: Set[str] = set()
    
    # 遍历所有流年
    groups = luck_data.get("groups", [])
    for group in groups:
        liunian_list = group.get("liunian", [])
        dayun = group.get("dayun")
        # 大运开始之前的流年组，dayun 为 None，没有大运天干
        dayun_gan = dayun.get("gan", "") if dayun else None
        
        for liunian in liunian_list:
            year = liunian.get("year")
            if not year:
                continue
            
            year_hit = False
            year_types: Set[str] = set()
            
            # ===== A. 检查冲到婚姻宫/夫妻宫 =====
            # A1. 检查流年与命局的冲
            all_events = liunian.get("all_events", [])
            for event in all_events:
                if event.get("type") == "branch_clash":
                    # 检查是否命中婚姻宫/夫妻宫
                    if _check_clash_hits_marriage_palace(event):
                        year_hit = True
                        year_types.add(RELATIONSHIP_TYPE_PALACE_CLASH)
            
            # A2. 检查运年相冲是否命中婚姻宫/夫妻宫
            # 注意：运年相冲（大运与流年相冲）不直接命中命局宫位，
            # 但根据需求，运年相冲如果作用到命局相关宫位，也应检测
            # 实际上运年相冲不会在 targets 中包含命局宫位信息，
            # 所以这里暂不检查运年相冲（如需检查，需要额外逻辑）
            
            # ===== B. 检查天干争合官杀/财星 =====
            # 复用现有的 wuhe_events（已由 enrich_liunian 生成）
            wuhe_events = liunian.get("wuhe_events", [])
            has_competing, competing_type = _check_competing_combine_hits_spouse_star(
                wuhe_events=wuhe_events,
                day_gan=day_gan,
                is_male=is_male,
            )
            
            if has_competing and competing_type:
                year_hit = True
                year_types.add(competing_type)
            
            # 如果该年命中，添加到集合中
            if year_hit:
                hit_years.add(year)
                relationship_types.update(year_types)
    
    # 转换为排序列表
    sorted_years = sorted(list(hit_years))
    sorted_types = sorted(list(relationship_types))
    
    # 计算 last5_hit 和 last5_years
    # 近5年：包含当前年份往前推5年（不包括当前年份）
    # 例如：如果 current_year = 2024，则 last5_years 包含 [2019, 2020, 2021, 2022, 2023]
    last5_years_list = [y for y in sorted_years if y >= (current_year - 5) and y < current_year]
    last5_hit = len(last5_years_list) > 0
    
    return {
        "hit": len(sorted_years) > 0,
        "types": sorted_types,
        "years": sorted_years,
        "last5_hit": last5_hit,
        "last5_years": sorted(last5_years_list),
    }

