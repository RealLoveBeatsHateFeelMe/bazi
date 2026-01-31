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
from .shishen import get_shishen, classify_shishen_category, get_branch_main_gan


# Relationship 类型枚举值
RELATIONSHIP_TYPE_PALACE_CLASH = "palace_clash"  # 冲到婚姻宫/夫妻宫
RELATIONSHIP_TYPE_COMPETING_COMBINE_OFFICIAL_KILL = "competing_combine_official_kill"  # 天干争合官杀
RELATIONSHIP_TYPE_COMPETING_COMBINE_WEALTH = "competing_combine_wealth"  # 天干争合财星
# 新增类型（v1.1）
RELATIONSHIP_TYPE_SPOUSE_STAR_IN_GAN = "spouse_star_in_gan"  # 天干配偶星（能谈恋爱）
RELATIONSHIP_TYPE_SPOUSE_STAR_IN_ZHI = "spouse_star_in_zhi"  # 地支配偶星（遇到对的人，最高层次）
RELATIONSHIP_TYPE_ZHI_LIUHE_COMBINE = "zhi_liuhe_combine"  # 地支六合（能谈恋爱）
RELATIONSHIP_TYPE_ZHI_BANHE_COMBINE = "zhi_banhe_combine"  # 地支半合/三合（能谈恋爱）


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


def _check_spouse_star_in_gan(
    liunian_gan: str,
    day_gan: str,
    is_male: bool,
) -> bool:
    """检查流年天干是否是配偶星。

    参数:
        liunian_gan: 流年天干
        day_gan: 日主天干
        is_male: 是否为男性

    返回:
        True 如果流年天干是配偶星（男财女官杀），否则 False
    """
    if not liunian_gan:
        return False

    gan_shishen = get_shishen(day_gan, liunian_gan)
    if not gan_shishen:
        return False

    if is_male:
        return gan_shishen in ("正财", "偏财")
    else:
        return gan_shishen in ("正官", "七杀")


def _check_spouse_star_in_zhi(
    liunian_zhi: str,
    day_gan: str,
    is_male: bool,
) -> bool:
    """检查流年地支主气是否是配偶星。

    参数:
        liunian_zhi: 流年地支
        day_gan: 日主天干
        is_male: 是否为男性

    返回:
        True 如果流年地支主气是配偶星（男财女官杀），否则 False
    """
    if not liunian_zhi:
        return False

    main_gan = get_branch_main_gan(liunian_zhi)
    if not main_gan:
        return False

    zhi_shishen = get_shishen(day_gan, main_gan)
    if not zhi_shishen:
        return False

    if is_male:
        return zhi_shishen in ("正财", "偏财")
    else:
        return zhi_shishen in ("正官", "七杀")


def _check_zhi_combine(
    liunian: Dict[str, Any],
) -> tuple[bool, bool]:
    """检查流年是否有地支六合或半合。

    参数:
        liunian: 流年数据

    返回:
        (has_liuhe, has_banhe) 元组
    """
    has_liuhe = False
    has_banhe = False

    # 从 harmonies_natal 检查地支合
    harmonies_natal = liunian.get("harmonies_natal", [])
    for ev in harmonies_natal:
        if ev.get("type") != "branch_harmony":
            continue
        subtype = ev.get("subtype", "")
        if subtype == "liuhe":
            has_liuhe = True
        elif subtype == "banhe":
            has_banhe = True

    return (has_liuhe, has_banhe)


def generate_relationship_index(
    luck_data: Dict[str, Any],
    bazi: Dict[str, Dict[str, str]],
    day_gan: str,
    is_male: bool,
    current_year: Optional[int] = None,
) -> Dict[str, Any]:
    """生成 Relationship Index (Index-5)。

    v1.1 增强：新增配偶星检测和地支合检测，增加 years_by_type 字段。

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
            "types": List[str],  # 所有命中的类型
            "years": List[int],  # 命中的年份列表，排序稳定
            "years_by_type": Dict[str, List[int]],  # 按类型分组的年份（新增）
            "last5_hit": bool,
            "last5_years": List[int],  # 近5年命中的年份列表，排序稳定
            "last5_years_by_type": Dict[str, List[int]],  # 近5年按类型分组的年份（新增）
        }
    """
    if current_year is None:
        current_year = datetime.now().year

    hit_years: Set[int] = set()
    relationship_types: Set[str] = set()

    # 按类型分组的年份（新增）
    years_by_type: Dict[str, Set[int]] = {
        RELATIONSHIP_TYPE_PALACE_CLASH: set(),
        RELATIONSHIP_TYPE_COMPETING_COMBINE_OFFICIAL_KILL: set(),
        RELATIONSHIP_TYPE_COMPETING_COMBINE_WEALTH: set(),
        RELATIONSHIP_TYPE_SPOUSE_STAR_IN_GAN: set(),
        RELATIONSHIP_TYPE_SPOUSE_STAR_IN_ZHI: set(),
        RELATIONSHIP_TYPE_ZHI_LIUHE_COMBINE: set(),
        RELATIONSHIP_TYPE_ZHI_BANHE_COMBINE: set(),
    }

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

            liunian_gan = liunian.get("gan", "")
            liunian_zhi = liunian.get("zhi", "")

            # ===== A. 检查冲到婚姻宫/夫妻宫 =====
            all_events = liunian.get("all_events", [])
            for event in all_events:
                if event.get("type") == "branch_clash":
                    if _check_clash_hits_marriage_palace(event):
                        year_hit = True
                        year_types.add(RELATIONSHIP_TYPE_PALACE_CLASH)
                        years_by_type[RELATIONSHIP_TYPE_PALACE_CLASH].add(year)

            # ===== B. 检查天干争合官杀/财星 =====
            wuhe_events = liunian.get("wuhe_events", [])
            has_competing, competing_type = _check_competing_combine_hits_spouse_star(
                wuhe_events=wuhe_events,
                day_gan=day_gan,
                is_male=is_male,
            )

            if has_competing and competing_type:
                year_hit = True
                year_types.add(competing_type)
                years_by_type[competing_type].add(year)

            # ===== C. 检查天干配偶星（新增）=====
            if _check_spouse_star_in_gan(liunian_gan, day_gan, is_male):
                year_hit = True
                year_types.add(RELATIONSHIP_TYPE_SPOUSE_STAR_IN_GAN)
                years_by_type[RELATIONSHIP_TYPE_SPOUSE_STAR_IN_GAN].add(year)

            # ===== D. 检查地支配偶星（新增，最高层次）=====
            if _check_spouse_star_in_zhi(liunian_zhi, day_gan, is_male):
                year_hit = True
                year_types.add(RELATIONSHIP_TYPE_SPOUSE_STAR_IN_ZHI)
                years_by_type[RELATIONSHIP_TYPE_SPOUSE_STAR_IN_ZHI].add(year)

            # ===== E. 检查地支六合/半合（新增）=====
            has_liuhe, has_banhe = _check_zhi_combine(liunian)
            if has_liuhe:
                year_hit = True
                year_types.add(RELATIONSHIP_TYPE_ZHI_LIUHE_COMBINE)
                years_by_type[RELATIONSHIP_TYPE_ZHI_LIUHE_COMBINE].add(year)
            if has_banhe:
                year_hit = True
                year_types.add(RELATIONSHIP_TYPE_ZHI_BANHE_COMBINE)
                years_by_type[RELATIONSHIP_TYPE_ZHI_BANHE_COMBINE].add(year)

            # 如果该年命中，添加到集合中
            if year_hit:
                hit_years.add(year)
                relationship_types.update(year_types)

    # 转换为排序列表
    sorted_years = sorted(list(hit_years))
    sorted_types = sorted(list(relationship_types))

    # 转换 years_by_type 为排序列表（过滤空类型）
    years_by_type_output: Dict[str, List[int]] = {}
    for type_name, years_set in years_by_type.items():
        if years_set:
            years_by_type_output[type_name] = sorted(list(years_set))

    # 计算 last5_hit 和 last5_years
    # 近5年：包含当前年份往前推5年（包含当前年份）
    last5_years_range = set(range(current_year - 4, current_year + 1))
    last5_years_list = [y for y in sorted_years if y in last5_years_range]
    last5_hit = len(last5_years_list) > 0

    # 计算 last5_years_by_type（新增）
    last5_years_by_type_output: Dict[str, List[int]] = {}
    for type_name, years_list in years_by_type_output.items():
        last5_for_type = [y for y in years_list if y in last5_years_range]
        if last5_for_type:
            last5_years_by_type_output[type_name] = sorted(last5_for_type)

    return {
        "hit": len(sorted_years) > 0,
        "types": sorted_types,
        "years": sorted_years,
        "years_by_type": years_by_type_output,  # 新增
        "last5_hit": last5_hit,
        "last5_years": sorted(last5_years_list),
        "last5_years_by_type": last5_years_by_type_output,  # 新增
    }

