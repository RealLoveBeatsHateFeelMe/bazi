# -*- coding: utf-8 -*-
"""数据丰富化：将打印层逻辑结构化回填到结果对象中。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from .gan_wuhe import GanPosition, detect_gan_wuhe
from .marriage_wuhe import detect_marriage_wuhe_hints
from .yongshen_swap import should_print_yongshen_swap_hint
from .shishen import get_shishen, get_branch_main_gan
from .config import ZHI_WUXING
# 从 cli 模块复制 _generate_marriage_suggestion 的逻辑（避免循环依赖）
def _generate_marriage_suggestion(yongshen_elements: list[str]) -> str:
    """根据用神五行生成婚配倾向。"""
    if not yongshen_elements:
        return ""
    
    zhi_to_zodiac = {
        "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔",
        "辰": "龙", "巳": "蛇", "午": "马", "未": "羊",
        "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
    }
    
    element_to_zhi = {
        "水": ["亥", "子"],
        "金": ["申", "酉"],
        "木": ["寅", "卯"],
        "火": ["巳", "午"],
        "土": ["辰", "戌", "丑", "未"],
    }
    
    zodiac_blocks = {
        "水": [],
        "金": [],
        "木": [],
        "火": [],
        "土": [],
    }
    
    for elem in yongshen_elements:
        if elem in element_to_zhi:
            for zhi in element_to_zhi[elem]:
                zodiac = zhi_to_zodiac.get(zhi, "")
                if zodiac and zodiac not in zodiac_blocks[elem]:
                    zodiac_blocks[elem].append(zodiac)
    
    result_parts = []
    if zodiac_blocks["水"]:
        result_parts.extend(zodiac_blocks["水"])
    if zodiac_blocks["金"]:
        result_parts.extend(zodiac_blocks["金"])
    if zodiac_blocks["木"]:
        result_parts.extend(zodiac_blocks["木"])
    if zodiac_blocks["火"]:
        result_parts.extend(zodiac_blocks["火"])
    if zodiac_blocks["土"]:
        result_parts.extend(zodiac_blocks["土"])
    
    zodiac_str = "".join(result_parts) if result_parts else ""
    wang_str = "，".join(yongshen_elements)
    
    if zodiac_str:
        return f"更容易匹配：{zodiac_str}；或 {wang_str}旺的人。"
    else:
        return f"更容易匹配：{wang_str}旺的人。"


def _serialize_gan_wuhe_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """序列化天干五合事件：将 GanPosition dataclass 和 frozenset 转为 JSON 可序列化的格式。
    
    参数:
        events: detect_gan_wuhe() 返回的事件列表
        
    返回:
        序列化后的事件列表（纯 dict/list）
    """
    serialized = []
    for ev in events:
        # 序列化 gan_pair (frozenset -> sorted list)
        gan_pair = ev.get("gan_pair")
        if isinstance(gan_pair, frozenset):
            gan_pair_list = sorted(list(gan_pair))
        else:
            gan_pair_list = list(gan_pair) if gan_pair else []
        
        # 序列化 pos_a, pos_b, many_side, few_side (GanPosition -> dict)
        def serialize_positions(positions: List[GanPosition]) -> List[Dict[str, Any]]:
            return [asdict(pos) for pos in positions]
        
        serialized_ev = {
            "gan_pair": gan_pair_list,  # 转为 list
            "wuhe_name": ev.get("wuhe_name", ""),
            "pos_a": serialize_positions(ev.get("pos_a", [])),
            "pos_b": serialize_positions(ev.get("pos_b", [])),
            "many_side": serialize_positions(ev.get("many_side", [])),
            "few_side": serialize_positions(ev.get("few_side", [])),
            "many_gan": ev.get("many_gan", ""),
            "few_gan": ev.get("few_gan", ""),
            "is_zhenghe": ev.get("is_zhenghe", False),
            "shishen_a": ev.get("shishen_a", ""),
            "shishen_b": ev.get("shishen_b", ""),
        }
        serialized.append(serialized_ev)
    
    return serialized


def enrich_natal(
    natal: Dict[str, Any],
    bazi: Dict[str, Dict[str, str]],
    day_gan: str,
    is_male: bool,
) -> Dict[str, Any]:
    """丰富原局数据：添加 marriage_suggestion, liuqin_zhuli, wuhe_events, hints。
    
    参数:
        natal: analyze_basic() 返回的原局数据
        bazi: 八字字典
        day_gan: 日主天干
        is_male: 是否男性
        
    返回:
        丰富后的原局数据（新增字段）
    """
    # 1. marriage_suggestion
    yongshen_elements = natal.get("yongshen_elements", [])
    marriage_suggestion = _generate_marriage_suggestion(yongshen_elements)
    
    # 2. liuqin_zhuli：从 dominant_traits 中筛选用神大类
    dominant_traits = natal.get("dominant_traits", [])
    liuqin_zhuli = []
    yongshen_set = set(yongshen_elements)
    
    for trait in dominant_traits:
        element = trait.get("element", "")
        if element and element in yongshen_set:
            liuqin_zhuli.append(trait)
    
    # 3. wuhe_events：原局天干五合
    natal_gan_positions = []
    pillar_labels = {"year": "年柱天干", "month": "月柱天干", "day": "日柱天干", "hour": "时柱天干"}
    for pillar in ["year", "month", "day", "hour"]:
        gan = bazi[pillar]["gan"]
        shishen = get_shishen(day_gan, gan) or "-"
        natal_gan_positions.append(GanPosition(
            source="natal",
            label=pillar_labels[pillar],
            gan=gan,
            shishen=shishen
        ))
    
    natal_wuhe_events_raw = detect_gan_wuhe(natal_gan_positions)
    natal_wuhe_events = _serialize_gan_wuhe_events(natal_wuhe_events_raw)
    
    # 4. hints：原局提示列表（唯一真相源，不包含婚配倾向）
    hints: List[str] = []
    # 注意：婚配倾向不再放入 hints，而是单独存储为 marriage_hint
    
    # 5. 原局层婚恋提醒（从 marriage_wuhe_hints 中提取）
    natal_gans = [
        bazi["year"]["gan"],
        bazi["month"]["gan"],
        bazi["day"]["gan"],  # 包括日干
        bazi["hour"]["gan"],
    ]
    natal_wuhe_hints = detect_marriage_wuhe_hints(natal_gans, day_gan, is_male)
    # 注意：婚恋结构提示不再放入 hints，而是单独存储为 marriage_structure_hints
    # 这里暂时保留在 hints 中，但会在 CLI 层去掉前缀后放入婚恋结构 section
    for hint in natal_wuhe_hints:
        hints.append(f"婚恋结构提示：{hint['hint_text']}")
    
    # 返回新增字段（不修改原字典，由调用者合并）
    return {
        "marriage_suggestion": marriage_suggestion,  # 保留兼容字段
        "marriage_hint": marriage_suggestion,  # 新增：独立的婚配倾向字段（不带【婚配倾向】前缀）
        "liuqin_zhuli": liuqin_zhuli,
        "wuhe_events": natal_wuhe_events,
        "hints": hints,
    }


def enrich_dayun(
    dayun: Dict[str, Any],
    bazi: Dict[str, Dict[str, str]],
    day_gan: str,
    strength_percent: float,
    support_percent: float,
    yongshen_elements: List[str],
    is_male: bool,
) -> Dict[str, Any]:
    """丰富大运数据：添加 yongshen_swap_hint, wuhe_events, hints。
    
    参数:
        dayun: 大运数据
        bazi: 八字字典
        day_gan: 日主天干
        strength_percent: 综合强弱百分比
        support_percent: 生扶力量占比
        yongshen_elements: 用神五行列表
        is_male: 是否男性
        
    返回:
        丰富后的大运数据（新增字段）
    """
    # 1. yongshen_swap_hint
    dayun_zhi = dayun.get("zhi", "")
    yongshen_swap_hint = should_print_yongshen_swap_hint(
        day_gan=day_gan,
        strength_percent=strength_percent,
        support_percent=support_percent,
        yongshen_elements=yongshen_elements,
        dayun_zhi=dayun_zhi,
    )
    
    # 2. wuhe_events：大运层天干五合（只包含涉及大运天干的）
    dayun_gan = dayun.get("gan", "")
    dayun_wuhe_events = []
    
    if dayun_gan:
        dayun_shishen = get_shishen(day_gan, dayun_gan) or "-"
        dayun_gan_positions = []
        pillar_labels = {"year": "年干", "month": "月干", "day": "日干", "hour": "时干"}
        for pillar in ["year", "month", "day", "hour"]:
            gan = bazi[pillar]["gan"]
            shishen = get_shishen(day_gan, gan) or "-"
            dayun_gan_positions.append(GanPosition(
                source="natal",
                label=pillar_labels[pillar],
                gan=gan,
                shishen=shishen
            ))
        dayun_gan_positions.append(GanPosition(
            source="dayun",
            label="大运天干",
            gan=dayun_gan,
            shishen=dayun_shishen
        ))
        
        dayun_wuhe_events_raw = detect_gan_wuhe(dayun_gan_positions)
        # 只保留涉及大运天干的五合
        for ev in dayun_wuhe_events_raw:
            if any(pos.source == "dayun" for pos in ev["many_side"] + ev["few_side"]):
                dayun_wuhe_events.append(ev)
        
        dayun_wuhe_events = _serialize_gan_wuhe_events(dayun_wuhe_events)
    
    # 3. hints：大运提示列表（唯一真相源）
    hints: List[str] = []
    if yongshen_swap_hint:
        from .yongshen_swap import format_yongshen_swap_hint
        hints.append(format_yongshen_swap_hint(yongshen_swap_hint))
    
    # 4. 大运层婚恋提醒（从 marriage_wuhe_hints 中提取）
    dayun_gan = dayun.get("gan", "")
    if dayun_gan:
        # 收集大运层天干：原局四柱天干 + 当前大运天干
        dayun_layer_gans = [
            bazi["year"]["gan"],
            bazi["month"]["gan"],
            bazi["day"]["gan"],
            bazi["hour"]["gan"],
        ]
        trigger_gans_dayun = []
        if dayun_gan:
            dayun_layer_gans.append(dayun_gan)
            trigger_gans_dayun.append(dayun_gan)  # 大运天干作为引动
        
        dayun_wuhe_hints = detect_marriage_wuhe_hints(
            gan_list=dayun_layer_gans,
            day_gan=day_gan,
            is_male=is_male,
            trigger_gans=trigger_gans_dayun if trigger_gans_dayun else None,
        )
        for hint in dayun_wuhe_hints:
            hints.append(f"婚恋变化提醒（如恋爱）：{hint['hint_text']}")
    
    return {
        "yongshen_swap_hint": yongshen_swap_hint,
        "wuhe_events": dayun_wuhe_events,
        "hints": hints,
    }


def enrich_liunian(
    liunian: Dict[str, Any],
    bazi: Dict[str, Dict[str, str]],
    day_gan: str,
    is_male: bool,
    dayun_gan: Optional[str] = None,
) -> Dict[str, Any]:
    """丰富流年数据：添加 wuhe_events, marriage_wuhe_hints, love_signals。
    
    参数:
        liunian: 流年数据
        bazi: 八字字典
        day_gan: 日主天干
        is_male: 是否男性
        dayun_gan: 当前大运天干（可选）
        
    返回:
        丰富后的流年数据（新增字段）
    """
    liunian_gan = liunian.get("gan", "")
    
    # 1. wuhe_events：流年层天干五合（只包含涉及流年天干的）
    liunian_wuhe_events = []
    if liunian_gan:
        liunian_shishen = get_shishen(day_gan, liunian_gan) or "-"
        liunian_gan_positions = []
        pillar_labels = {"year": "年干", "month": "月干", "day": "日干", "hour": "时干"}
        for pillar in ["year", "month", "day", "hour"]:
            gan = bazi[pillar]["gan"]
            shishen = get_shishen(day_gan, gan) or "-"
            liunian_gan_positions.append(GanPosition(
                source="natal",
                label=pillar_labels[pillar],
                gan=gan,
                shishen=shishen
            ))
        if dayun_gan:
            dayun_shishen = get_shishen(day_gan, dayun_gan) or "-"
            liunian_gan_positions.append(GanPosition(
                source="dayun",
                label="大运天干",
                gan=dayun_gan,
                shishen=dayun_shishen
            ))
        liunian_gan_positions.append(GanPosition(
            source="liunian",
            label="流年天干",
            gan=liunian_gan,
            shishen=liunian_shishen
        ))
        
        liunian_wuhe_events_raw = detect_gan_wuhe(liunian_gan_positions)
        # 只保留涉及流年天干的五合
        for ev in liunian_wuhe_events_raw:
            if any(pos.source == "liunian" for pos in ev["many_side"] + ev["few_side"]):
                liunian_wuhe_events.append(ev)
        
        liunian_wuhe_events = _serialize_gan_wuhe_events(liunian_wuhe_events)
    
    # 2. marriage_wuhe_hints：流年层天干五合婚恋提醒
    liunian_layer_gans = [
        bazi["year"]["gan"],
        bazi["month"]["gan"],
        bazi["day"]["gan"],
        bazi["hour"]["gan"],
    ]
    trigger_gans_liunian = []
    if dayun_gan:
        liunian_layer_gans.append(dayun_gan)
    if liunian_gan:
        liunian_layer_gans.append(liunian_gan)
        trigger_gans_liunian.append(liunian_gan)  # 只检查流年天干引动
    
    marriage_wuhe_hints = detect_marriage_wuhe_hints(
        gan_list=liunian_layer_gans,
        day_gan=day_gan,
        is_male=is_male,
        trigger_gans=trigger_gans_liunian if trigger_gans_liunian else None,
    )
    
    # 3. love_signals：感情信号（合冲同现等）
    love_signals = _compute_love_signals(liunian, bazi, day_gan, is_male, liunian_gan)
    
    # 4. hints：流年提示列表（唯一真相源）
    hints: List[str] = []
    
    # 4.1 婚恋变化提醒（从 marriage_wuhe_hints）
    for hint in marriage_wuhe_hints:
        hints.append(f"婚恋变化提醒（如恋爱）：{hint['hint_text']}")
    
    # 4.2 缘分提示（从 love_signals）
    liunian_zhi = liunian.get("zhi", "")
    if liunian_gan:
        gan_shishen = get_shishen(day_gan, liunian_gan)
        if gan_shishen:
            if is_male:
                if gan_shishen in ("正财", "偏财"):
                    hints.append("提示：缘分（天干）：暧昧推进")
            else:
                if gan_shishen in ("正官", "七杀"):
                    hints.append("提示：缘分（天干）：暧昧推进")
    
    if liunian_zhi:
        main_gan = get_branch_main_gan(liunian_zhi)
        if main_gan:
            zhi_shishen = get_shishen(day_gan, main_gan)
            if zhi_shishen:
                if is_male:
                    if zhi_shishen in ("正财", "偏财"):
                        hints.append("提示：缘分（地支）：易遇合适伴侣（良缘）")
                else:
                    if zhi_shishen in ("正官", "七杀"):
                        hints.append("提示：缘分（地支）：易遇合适伴侣（良缘）")
    
    # 4.3 合冲同现提示
    if love_signals.get("he_and_chong_coexist"):
        hints.append("提示：感情线合冲同现（进展易受阻/反复拉扯；仓促定论的稳定性更低）")
    
    # 4.4 天克地冲提示（从 liunian 数据中提取）
    # 检查运年天克地冲（从 clashes_dayun 中检查）
    clashes_dayun = liunian.get("clashes_dayun", [])
    for ev_clash in clashes_dayun:
        if not ev_clash:
            continue
        if ev_clash.get("is_tian_ke_di_chong", False):
            hints.append("提示：运年天克地冲（家人去世/生活环境变化剧烈，如出国上学打工）")
            break  # 每年只加一次
    
    # 检查时柱天克地冲（用于后续互斥判断，实际提示由 cli.py 生成）
    clashes_natal = liunian.get("clashes_natal", [])
    has_hour_tkdc = False
    for ev in clashes_natal:
        if not ev:
            continue
        tkdc_targets = ev.get("tkdc_targets", [])
        for tkdc_target in tkdc_targets:
            if tkdc_target.get("pillar") == "hour":
                # 时柱天克地冲的提示由 cli.py 的 _generate_hour_tkdc_hint() 生成
                # 这里只标记 has_hour_tkdc 用于互斥判断
                has_hour_tkdc = True
                break
        if has_hour_tkdc:
            break
    
    # 4.5 风险管理选项（从 total_risk_percent 判断，>= 40% 时添加）
    total_risk = liunian.get("total_risk_percent", 0.0)
    if total_risk >= 40.0:
        hints.append("风险管理选项（供参考）：保险/预案；投机回撤风险更高；合规优先；职业变动成本更高；情绪波动时更易误判；重大决定适合拉长周期")
    
    # 4.6 其他提示（从 clashes_natal 和 harmonies_natal 中提取）
    # 婚姻宫/夫妻宫被冲
    clash_palaces_hit = set()
    for ev in clashes_natal:
        if not ev:
            continue
        targets = ev.get("targets", [])
        for target in targets:
            palace = target.get("palace", "")
            if palace in ("婚姻宫", "夫妻宫"):
                clash_palaces_hit.add(palace)
    
    if clash_palaces_hit:
        hints.append("提示：感情（单身：更易暧昧/受阻；有伴侣：争执起伏）")
    
    # 婚姻宫/夫妻宫被合（六合/半合）
    harmonies_natal = liunian.get("harmonies_natal", [])
    harmony_palaces_hit = set()
    for ev in harmonies_natal:
        if ev.get("type") != "branch_harmony":
            continue
        subtype = ev.get("subtype")
        if subtype not in ("liuhe", "banhe"):
            continue
        targets = ev.get("targets", [])
        for target in targets:
            palace = target.get("palace", "")
            if palace in ("婚姻宫", "夫妻宫"):
                harmony_palaces_hit.add(palace)
    
    for palace in harmony_palaces_hit:
        hints.append(f"提示：{palace}引动（单身：更容易出现暧昧/推进；有伴侣：关系推进或波动）")
    
    # 事业家庭宫被冲（且未命中时柱天克地冲）
    if "事业家庭宫" in clash_palaces_hit and not has_hour_tkdc:
        hints.append("提示：家庭变动（搬家/换工作/家庭节奏变化）")
    
    return {
        "wuhe_events": liunian_wuhe_events,
        "marriage_wuhe_hints": marriage_wuhe_hints,
        "love_signals": love_signals,
        "hints": hints,
    }


def _compute_love_signals(
    liunian: Dict[str, Any],
    bazi: Dict[str, Dict[str, str]],
    day_gan: str,
    is_male: bool,
    liunian_gan: Optional[str],
) -> Dict[str, Any]:
    """计算流年感情信号。
    
    返回:
        {
            "marriage_palace_triggered": bool,  # 婚姻宫/夫妻宫被冲
            "marriage_palace_harmony": bool,    # 婚姻宫/夫妻宫被合（六合/半合）
            "liuyuan": bool,                    # 流年财官杀缘分提示
            "he_and_chong_coexist": bool,       # 合冲同现
        }
    """
    signals = {
        "marriage_palace_triggered": False,
        "marriage_palace_harmony": False,
        "liuyuan": False,
        "he_and_chong_coexist": False,
    }
    
    # 1. 检查婚姻宫/夫妻宫被冲
    clashes_natal = liunian.get("clashes_natal", [])
    clash_palaces = set()
    for ev in clashes_natal:
        if not ev:
            continue
        targets = ev.get("targets", [])
        for target in targets:
            palace = target.get("palace", "")
            if palace in ("婚姻宫", "夫妻宫"):
                clash_palaces.add(palace)
                signals["marriage_palace_triggered"] = True
    
    # 2. 检查婚姻宫/夫妻宫被合（只检查六合/半合，不包含三合/三会）
    harmonies_natal = liunian.get("harmonies_natal", [])
    harmony_palaces = set()
    for ev in harmonies_natal:
        if ev.get("type") != "branch_harmony":
            continue
        subtype = ev.get("subtype")
        if subtype not in ("liuhe", "banhe"):  # 只包含六合和半合
            continue
        targets = ev.get("targets", [])
        for target in targets:
            palace = target.get("palace", "")
            if palace in ("婚姻宫", "夫妻宫"):
                harmony_palaces.add(palace)
                signals["marriage_palace_harmony"] = True
    
    # 3. 检查流年财官杀缘分提示
    liunian_zhi = liunian.get("zhi", "")
    if liunian_gan:
        gan_shishen = get_shishen(day_gan, liunian_gan)
        if gan_shishen:
            if is_male:
                if gan_shishen in ("正财", "偏财"):
                    signals["liuyuan"] = True
            else:
                if gan_shishen in ("正官", "七杀"):
                    signals["liuyuan"] = True
    
    if liunian_zhi:
        main_gan = get_branch_main_gan(liunian_zhi)
        if main_gan:
            zhi_shishen = get_shishen(day_gan, main_gan)
            if zhi_shishen:
                if is_male:
                    if zhi_shishen in ("正财", "偏财"):
                        signals["liuyuan"] = True
                else:
                    if zhi_shishen in ("正官", "七杀"):
                        signals["liuyuan"] = True
    
    # 4. 合冲同现：has_love_clash && (has_love_merge || has_liuyuan)
    has_love_clash = signals["marriage_palace_triggered"]
    has_love_merge = signals["marriage_palace_harmony"]
    has_liuyuan = signals["liuyuan"]
    
    if has_love_clash and (has_love_merge or has_liuyuan):
        signals["he_and_chong_coexist"] = True
    
    return signals


def compute_turning_points(groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """计算大运转折点列表。
    
    参数:
        groups: analyze_luck() 返回的 groups 列表
        
    返回:
        转折点列表，每个元素包含：
        {
            "year": int,           # 转折年份
            "from_state": str,     # "好运" | "一般"
            "to_state": str,       # "好运" | "一般"
            "change_type": str,    # "转弱" | "转好"
        }
    """
    turning_points = []
    prev_zhi_good: Optional[bool] = None
    
    for group in groups:
        dy = group.get("dayun")
        # 如果 dayun 为 None，说明是大运开始之前的流年，不参与转折点计算
        if dy is None:
            continue
        
        current_zhi_good = dy.get("zhi_good", False)
        
        if prev_zhi_good is not None and prev_zhi_good != current_zhi_good:
            start_year = dy.get("start_year")
            if start_year is None:
                continue
            
            if prev_zhi_good and not current_zhi_good:
                from_state, to_state, change_type = "好运", "一般", "转弱"
            else:
                from_state, to_state, change_type = "一般", "好运", "转好"
            
            turning_points.append({
                "year": start_year,
                "from_state": from_state,
                "to_state": to_state,
                "change_type": change_type,
            })
        
        prev_zhi_good = current_zhi_good
    
    return turning_points

