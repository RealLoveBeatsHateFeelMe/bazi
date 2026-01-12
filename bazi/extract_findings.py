# -*- coding: utf-8 -*-
"""从 facts 中提取 findings（facts/hints/links）。

最小改动实现：在 chat_api 层从 facts 中提取并生成 findings。
"""

from typing import Any, Dict, List, Optional
from .findings_collector import FindingsCollector
from .shishen import get_shishen, get_branch_main_gan, get_shishen_label


def extract_findings_from_facts(facts: Dict[str, Any]) -> Dict[str, Any]:
    """从 facts 中提取 findings（facts/hints/links）。
    
    参数:
        facts: analyze_complete() 返回的完整 facts 数据
    
    返回:
        {
            "facts": [...],
            "hints": [...],
            "links": [...]
        }
    """
    collector = FindingsCollector()
    
    # 获取 natal 数据（用于计算十神）
    natal = facts.get("natal", {})
    bazi = natal.get("bazi", {})
    day_gan = bazi.get("day", {}).get("gan", "")
    yongshen_elements = natal.get("yongshen_elements", [])
    
    # 获取 luck 数据
    luck = facts.get("luck", {})
    groups = luck.get("groups", [])
    
    # 1. 提取 facts：遍历所有流年
    fact_id_map: Dict[str, str] = {}  # event_key -> fact_id，用于建立 links
    
    for group in groups:
        dayun = group.get("dayun")
        liunian_list = group.get("liunian", [])
        
        # 遍历该组的所有流年（包括大运开始之前的流年）
        for liunian in liunian_list:
            year = liunian.get("year")
            if not year:
                continue
            
            scope = f"liunian_{year}"
            
            # 1a. 提取流年的十神/用神核心信息（每年必有）
            _extract_year_tengod_fact(
                collector=collector,
                liunian=liunian,
                year=year,
                scope=scope,
                day_gan=day_gan,
                yongshen_elements=yongshen_elements,
            )
            
            all_events = liunian.get("all_events", [])
            
            # 提取流年的事件作为 facts
            for event in all_events:
                event_type = event.get("type")
                if not event_type:
                    continue
                
                # 根据事件类型提取 fact
                fact_id = _extract_fact_from_event(
                    collector=collector,
                    event=event,
                    event_type=event_type,
                    scope=scope,
                    fact_id_map=fact_id_map,
                )
                
                # 如果有 fact_id，记录到 fact_id_map 中（用于后续建立 links）
                if fact_id:
                    event_key = f"{scope}:{event_type}:{_get_event_key(event)}"
                    fact_id_map[event_key] = fact_id
    
    # 2. 生成 hints 并建立 links
    _generate_hints_and_links(
        collector=collector,
        groups=groups,
        fact_id_map=fact_id_map,
    )
    
    return collector.get_findings()


def _extract_year_tengod_fact(
    collector: FindingsCollector,
    liunian: Dict[str, Any],
    year: int,
    scope: str,
    day_gan: str,
    yongshen_elements: List[str],
) -> Optional[str]:
    """提取流年的十神/用神核心信息 fact。
    
    这是每年最核心的信息，包含：
    - 天干：十神、是否用神、标签
    - 地支：十神、是否用神、标签
    - 上下半年风险系数
    """
    liunian_gan = liunian.get("gan", "")
    liunian_zhi = liunian.get("zhi", "")
    gan_element = liunian.get("gan_element", "")
    zhi_element = liunian.get("zhi_element", "")
    
    if not liunian_gan or not day_gan:
        return None
    
    # 计算天干十神
    gan_shishen = get_shishen(day_gan, liunian_gan) or "-"
    is_gan_yongshen = gan_element in yongshen_elements if gan_element else False
    gan_label = get_shishen_label(gan_shishen, is_gan_yongshen) if gan_shishen != "-" else ""
    
    # 计算地支主气十神
    zhi_main_gan = get_branch_main_gan(liunian_zhi) if liunian_zhi else None
    zhi_shishen = get_shishen(day_gan, zhi_main_gan) if zhi_main_gan else "-"
    is_zhi_yongshen = zhi_element in yongshen_elements if zhi_element else False
    zhi_label = get_shishen_label(zhi_shishen, is_zhi_yongshen) if zhi_shishen != "-" else ""
    
    # 获取风险系数
    risk_from_gan = liunian.get("risk_from_gan", 0.0)
    risk_from_zhi = liunian.get("risk_from_zhi", 0.0)
    total_risk = liunian.get("total_risk_percent", 0.0)
    
    # 构建标签
    label_parts = []
    
    # 天干信息
    gan_yongshen_str = "用神" if is_gan_yongshen else "非用神"
    label_parts.append(f"天干{liunian_gan}({gan_shishen}/{gan_yongshen_str})")
    
    # 地支信息
    zhi_yongshen_str = "用神" if is_zhi_yongshen else "非用神"
    label_parts.append(f"地支{liunian_zhi}({zhi_shishen}/{zhi_yongshen_str})")
    
    label = f"{year}年：" + "，".join(label_parts)
    
    fact_id = collector.add_fact(
        fact_type="year_tengod",
        scope=scope,
        kind="tengod_yongshen",
        label=label,
        key_fields={
            "flow_year": year,
            "liunian_gan": liunian_gan,
            "liunian_zhi": liunian_zhi,
            "gan_shishen": gan_shishen,
            "zhi_shishen": zhi_shishen,
            "is_gan_yongshen": is_gan_yongshen,
            "is_zhi_yongshen": is_zhi_yongshen,
            "gan_label": gan_label,
            "zhi_label": zhi_label,
            "risk_from_gan": risk_from_gan,
            "risk_from_zhi": risk_from_zhi,
            "total_risk_percent": total_risk,
        },
    )
    
    return fact_id


def _extract_fact_from_event(
    collector: FindingsCollector,
    event: Dict[str, Any],
    event_type: str,
    scope: str,
    fact_id_map: Dict[str, str],
) -> Optional[str]:
    """从事件中提取 fact，返回 fact_id。"""
    
    if event_type == "branch_clash":
        # 冲事件
        flow_branch = event.get("flow_branch", "")
        target_branch = event.get("target_branch", "")
        flow_year = event.get("flow_year")
        risk_percent = event.get("risk_percent", 0.0)
        
        label = f"{flow_branch}{target_branch}冲"
        if flow_year:
            label = f"{flow_year}年{label}"
        
        fact_id = collector.add_fact(
            fact_type="branch_clash",
            scope=scope,
            kind="clash",
            label=label,
            key_fields={
                "flow_branch": flow_branch,
                "target_branch": target_branch,
                "flow_year": flow_year,
                "risk_percent": risk_percent,
                "impact_level": event.get("impact_level"),
            },
        )
        return fact_id
    
    elif event_type == "pattern":
        # 模式事件（如"枭神夺食"、"伤官见官"）
        pattern_type = event.get("pattern_type", "")
        kind = event.get("kind", "")  # "gan" or "zhi"
        flow_year = event.get("flow_year")
        risk_percent = event.get("risk_percent", 0.0)
        
        # 模式名称映射
        pattern_names = {
            "pianyin_eatgod": "枭神夺食",
            "hurt_officer": "伤官见官",
        }
        pattern_name = pattern_names.get(pattern_type, pattern_type)
        
        label = pattern_name
        if flow_year:
            label = f"{flow_year}年{label}"
        if kind:
            label = f"{label}({kind}层)"
        
        fact_id = collector.add_fact(
            fact_type="pattern",
            scope=scope,
            kind="pattern",
            label=label,
            key_fields={
                "pattern_type": pattern_type,
                "kind": kind,
                "flow_year": flow_year,
                "risk_percent": risk_percent,
            },
        )
        return fact_id
    
    elif event_type == "harmony":
        # 合事件（三合、三会、六合等）
        subtype = event.get("subtype", "")
        flow_year = event.get("flow_year")
        
        label = f"{subtype}"
        if flow_year:
            label = f"{flow_year}年{label}"
        
        fact_id = collector.add_fact(
            fact_type="harmony",
            scope=scope,
            kind="harmony",
            label=label,
            key_fields={
                "subtype": subtype,
                "flow_year": flow_year,
            },
        )
        return fact_id
    
    elif event_type == "branch_punishment":
        # 刑事件
        flow_branch = event.get("flow_branch", "")
        target_branch = event.get("target_branch", "")
        flow_year = event.get("flow_year")
        
        label = f"{flow_branch}{target_branch}刑"
        if flow_year:
            label = f"{flow_year}年{label}"
        
        fact_id = collector.add_fact(
            fact_type="branch_punishment",
            scope=scope,
            kind="punishment",
            label=label,
            key_fields={
                "flow_branch": flow_branch,
                "target_branch": target_branch,
                "flow_year": flow_year,
            },
        )
        return fact_id
    
    # 其他类型的事件暂不处理
    return None


def _get_event_key(event: Dict[str, Any]) -> str:
    """生成事件的唯一 key（用于去重）。"""
    event_type = event.get("type", "")
    
    if event_type == "branch_clash":
        return f"{event.get('flow_branch', '')}:{event.get('target_branch', '')}:{event.get('flow_year', '')}"
    elif event_type == "pattern":
        return f"{event.get('pattern_type', '')}:{event.get('kind', '')}:{event.get('flow_year', '')}"
    elif event_type == "harmony":
        return f"{event.get('subtype', '')}:{event.get('flow_year', '')}"
    elif event_type == "branch_punishment":
        return f"{event.get('flow_branch', '')}:{event.get('target_branch', '')}:{event.get('flow_year', '')}"
    
    return str(hash(str(event)))


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


def _generate_hints_and_links(
    collector: FindingsCollector,
    groups: List[Dict[str, Any]],
    fact_id_map: Dict[str, str],
) -> None:
    """生成 hints 并建立 links。
    
    规则：
    - 冲事件命中婚姻宫 -> 感情波动 hint
    - 模式事件（如"枭神夺食"）-> 对应 hint
    """
    
    # 1. 处理冲事件命中婚姻宫的情况
    for group in groups:
        liunian_list = group.get("liunian", [])
        
        for liunian in liunian_list:
            year = liunian.get("year")
            if not year:
                continue
            
            scope = f"liunian_{year}"
            all_events = liunian.get("all_events", [])
            
            # 检查是否有冲事件命中婚姻宫
            clash_fact_ids: List[str] = []
            for event in all_events:
                if event.get("type") == "branch_clash":
                    if _check_clash_hits_marriage_palace(event):
                        event_key = f"{scope}:branch_clash:{_get_event_key(event)}"
                        fact_id = fact_id_map.get(event_key)
                        if fact_id:
                            clash_fact_ids.append(fact_id)
            
            # 如果有冲事件命中婚姻宫，生成感情波动 hint
            if clash_fact_ids:
                hint_id = collector.add_hint(
                    domain="relationship",
                    level="moderate",
                    label=f"{year}年感情波动",
                    key_fields={"year": year},
                )
                # 建立 link
                collector.link(
                    hint_id=hint_id,
                    fact_ids=clash_fact_ids,
                    rule_id="palace_clash_to_relationship_hint",
                )
            
            # 2. 处理模式事件（如"枭神夺食"）
            pattern_fact_ids: List[str] = []
            for event in all_events:
                if event.get("type") == "pattern":
                    pattern_type = event.get("pattern_type", "")
                    event_key = f"{scope}:pattern:{_get_event_key(event)}"
                    fact_id = fact_id_map.get(event_key)
                    if fact_id:
                        pattern_fact_ids.append(fact_id)
            
            # 如果有模式事件，生成对应 hint
            if pattern_fact_ids:
                # 根据模式类型确定 domain 和 level
                pattern_domain = "general"
                pattern_level = "moderate"
                
                # 可以在这里根据 pattern_type 调整 domain 和 level
                # 例如："枭神夺食" 可能影响健康，可以用 domain="health"
                
                pattern_label = f"{year}年存在模式事件"
                hint_id = collector.add_hint(
                    domain=pattern_domain,
                    level=pattern_level,
                    label=pattern_label,
                    key_fields={"year": year},
                )
                # 建立 link
                collector.link(
                    hint_id=hint_id,
                    fact_ids=pattern_fact_ids,
                    rule_id="pattern_to_hint",
                )

