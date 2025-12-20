# -*- coding: utf-8 -*-
"""六合 / 三合 / 半合 / 三会检测：只解释，不计分。"""

from typing import Dict, Any, List, Optional

from .config import ZHI_LIUHE, ZHI_SANHE, PILLAR_PALACE_CN, POSITION_WEIGHTS
from .shishen import get_branch_shishen


# 三合局元素映射
SANHE_ELEMENT_MAP: Dict[str, str] = {
    "申": "水", "子": "水", "辰": "水",  # 申子辰水局
    "亥": "木", "卯": "木", "未": "木",  # 亥卯未木局
    "寅": "火", "午": "火", "戌": "火",  # 寅午戌火局
    "巳": "金", "酉": "金", "丑": "金",  # 巳酉丑金局
}

# 三会局定义
ZHI_SANHUI: Dict[str, List[str]] = {
    "寅": ["寅", "卯", "辰"],  # 寅卯辰（春木会）
    "卯": ["寅", "卯", "辰"],
    "辰": ["寅", "卯", "辰"],
    "巳": ["巳", "午", "未"],  # 巳午未（夏火会）
    "午": ["巳", "午", "未"],
    "未": ["巳", "午", "未"],
    "申": ["申", "酉", "戌"],  # 申酉戌（秋金会）
    "酉": ["申", "酉", "戌"],
    "戌": ["申", "酉", "戌"],
    "亥": ["亥", "子", "丑"],  # 亥子丑（冬水会）
    "子": ["亥", "子", "丑"],
    "丑": ["亥", "子", "丑"],
}

# 三会局名称
SANHUI_NAME_MAP: Dict[str, str] = {
    "寅": "木会", "卯": "木会", "辰": "木会",
    "巳": "火会", "午": "火会", "未": "火会",
    "申": "金会", "酉": "金会", "戌": "金会",
    "亥": "水会", "子": "水会", "丑": "水会",
}


def _get_position_weight(pillar: str, kind: str) -> float:
    """获取位置权重。"""
    key = f"{pillar}_{kind}"
    return POSITION_WEIGHTS.get(key, 0.0)


def detect_natal_harmonies(bazi: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    """检测命局内部的六合、三合、半合、三会。

    返回事件列表（统一格式）：
    [
      {
        "type": "branch_harmony",
        "subtype": "liuhe" | "sanhe" | "banhe" | "sanhui",
        "role": "explain",
        "risk_percent": 0.0,
        "flow_type": "natal",
        "group": "水局" | "火局" | "木会" | "火会" | ...,
        "members": ["申", "子", "辰"],  # 该组固定成员
        "matched_branches": ["申", "子"],  # 本次实际组成的支
        "targets": [
          {
            "pillar": "year",
                        "palace": "祖上宫",
            "target_branch": "申",
            "position_weight": 0.10,
            "branch_gan": "庚",  # 可选
            "branch_shishen": {...},  # 可选
          },
          ...
        ]
      },
      ...
    ]
    """
    events: List[Dict[str, Any]] = []
    pillars = ["year", "month", "day", "hour"]
    branches = {p: bazi[p]["zhi"] for p in pillars}

    # 1. 检测六合
    seen_liuhe: set = set()
    for i, pillar1 in enumerate(pillars):
        zhi1 = branches[pillar1]
        partner = ZHI_LIUHE.get(zhi1)
        if not partner:
            continue

        for j, pillar2 in enumerate(pillars):
            if i >= j:
                continue
            zhi2 = branches[pillar2]
            if zhi2 == partner:
                pair_key = tuple(sorted([zhi1, zhi2]))
                if pair_key in seen_liuhe:
                    continue
                seen_liuhe.add(pair_key)

                targets = []
                for p, z in [(pillar1, zhi1), (pillar2, zhi2)]:
                    shishen_info = get_branch_shishen(bazi, z)
                    targets.append({
                        "pillar": p,
                        "palace": PILLAR_PALACE_CN.get(p, ""),
                        "target_branch": z,
                        "position_weight": _get_position_weight(p, "zhi"),
                        "branch_gan": bazi[p].get("gan"),
                        "branch_shishen": shishen_info,
                    })

                events.append({
                    "type": "branch_harmony",
                    "subtype": "liuhe",
                    "role": "explain",
                    "risk_percent": 0.0,
                    "flow_type": "natal",
                    "group": "",
                    "members": [zhi1, zhi2],
                    "matched_branches": [zhi1, zhi2],
                    "targets": targets,
                })

    # 2. 检测三合局（完整三合 + 半合）
    seen_sanhe: set = set()
    for _, group in ZHI_SANHE.items():
        # group 形如 ["申", "子", "辰"]，中间一支 = group[1]
        group_key = tuple(sorted(group))
        if group_key in seen_sanhe:
            continue
        seen_sanhe.add(group_key)

        # 找出命局中属于该三合局的所有柱位（允许同一支重复出现在多宫位）
        found_pillars: List[str] = []
        found_branches: List[str] = []
        for pillar in pillars:
            natal_zhi = branches[pillar]
            if natal_zhi in group:
                found_pillars.append(pillar)
                found_branches.append(natal_zhi)

        # 2.1 完整三合局：三个不同地支都出现
        if len(set(found_branches)) == 3:
            element = SANHE_ELEMENT_MAP.get(group[0])
            targets = []
            for p, z in zip(found_pillars, found_branches):
                shishen_info = get_branch_shishen(bazi, z)
                targets.append({
                    "pillar": p,
                    "palace": PILLAR_PALACE_CN.get(p, ""),
                    "target_branch": z,
                    "position_weight": _get_position_weight(p, "zhi"),
                    "branch_gan": bazi[p].get("gan"),
                    "branch_shishen": shishen_info,
                })

            events.append({
                "type": "branch_harmony",
                "subtype": "sanhe",
                "role": "explain",
                "risk_percent": 0.0,
                "flow_type": "natal",
                "group": f"{element}局" if element else "",
                "members": group,
                "matched_branches": found_branches,
                "targets": targets,
            })
        # 2.2 半合：只认“前两支”或“后两支”，并且必须包含中间那一支
        center = group[1]
        edge_left = group[0]
        edge_right = group[2]
        element = SANHE_ELEMENT_MAP.get(center)

        # 统计每个地支出现在哪些柱位
        zhi_to_pillars: Dict[str, List[str]] = {}
        for p, z in zip(found_pillars, found_branches):
            zhi_to_pillars.setdefault(z, []).append(p)

        # 左半合（edge_left + center）
        if edge_left in zhi_to_pillars and center in zhi_to_pillars:
            for p1 in zhi_to_pillars[edge_left]:
                for p2 in zhi_to_pillars[center]:
                    if p1 == p2:
                        continue
                    targets = []
                    for p, z in ((p1, edge_left), (p2, center)):
                        shishen_info = get_branch_shishen(bazi, z)
                        targets.append({
                            "pillar": p,
                            "palace": PILLAR_PALACE_CN.get(p, ""),
                            "target_branch": z,
                            "position_weight": _get_position_weight(p, "zhi"),
                            "branch_gan": bazi[p].get("gan"),
                            "branch_shishen": shishen_info,
                        })
                    events.append({
                        "type": "branch_harmony",
                        "subtype": "banhe",
                        "role": "explain",
                        "risk_percent": 0.0,
                        "flow_type": "natal",
                        "group": f"{element}局" if element else "",
                        "members": group,
                        "matched_branches": [edge_left, center],
                        "targets": targets,
                    })

        # 右半合（center + edge_right）
        if center in zhi_to_pillars and edge_right in zhi_to_pillars:
            for p1 in zhi_to_pillars[center]:
                for p2 in zhi_to_pillars[edge_right]:
                    if p1 == p2:
                        continue
                    targets = []
                    for p, z in ((p1, center), (p2, edge_right)):
                        shishen_info = get_branch_shishen(bazi, z)
                        targets.append({
                            "pillar": p,
                            "palace": PILLAR_PALACE_CN.get(p, ""),
                            "target_branch": z,
                            "position_weight": _get_position_weight(p, "zhi"),
                            "branch_gan": bazi[p].get("gan"),
                            "branch_shishen": shishen_info,
                        })
                    events.append({
                        "type": "branch_harmony",
                        "subtype": "banhe",
                        "role": "explain",
                        "risk_percent": 0.0,
                        "flow_type": "natal",
                        "group": f"{element}局" if element else "",
                        "members": group,
                        "matched_branches": [center, edge_right],
                        "targets": targets,
                    })

    # 3. 检测三会（只检测完整三会，三支齐）
    seen_sanhui: set = set()
    for zhi, group in ZHI_SANHUI.items():
        group_key = tuple(sorted(group))
        if group_key in seen_sanhui:
            continue
        seen_sanhui.add(group_key)

        found_pillars: List[str] = []
        found_branches: List[str] = []
        for pillar in pillars:
            natal_zhi = branches[pillar]
            if natal_zhi in group:
                found_pillars.append(pillar)
                found_branches.append(natal_zhi)

        if len(found_branches) == 3:
            # 完整三会
            hui_name = SANHUI_NAME_MAP.get(found_branches[0])
            targets = []
            for p, z in zip(found_pillars, found_branches):
                shishen_info = get_branch_shishen(bazi, z)
                targets.append({
                    "pillar": p,
                    "palace": PILLAR_PALACE_CN.get(p, ""),
                    "target_branch": z,
                    "position_weight": _get_position_weight(p, "zhi"),
                    "branch_gan": bazi[p].get("gan"),
                    "branch_shishen": shishen_info,
                })

            events.append({
                "type": "branch_harmony",
                "subtype": "sanhui",
                "role": "explain",
                "risk_percent": 0.0,
                "flow_type": "natal",
                "group": hui_name,
                "members": group,
                "matched_branches": found_branches,
                "targets": targets,
            })

    return events


def detect_flow_harmonies(
    bazi: Dict[str, Dict[str, str]],
    flow_branch: str,
    flow_type: str,
    flow_year: Optional[int] = None,
    flow_label: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """检测流年/大运地支与原局形成的六合、三合、半合、三会。

    返回事件列表（统一格式）：
    [
      {
        "type": "branch_harmony",
        "subtype": "liuhe" | "sanhe" | "banhe" | "sanhui",
        "role": "explain",
        "risk_percent": 0.0,
        "flow_type": "dayun" | "liunian" | "dayun_liunian",
        "flow_year": 2024,
        "flow_label": "甲辰",
        "flow_branch": "辰",
        "group": "水局" | "火局" | "木会" | "火会" | ...,
        "members": ["申", "子", "辰"],
        "matched_branches": ["申", "子", "辰"],
        "targets": [
          {
            "pillar": "year",
                        "palace": "祖上宫",
            "target_branch": "申",
            "position_weight": 0.10,
            "branch_gan": "庚",
            "branch_shishen": {...},
          },
          ...
        ]
      },
      ...
    ]
    """
    events: List[Dict[str, Any]] = []
    pillars = ["year", "month", "day", "hour"]
    branches = {p: bazi[p]["zhi"] for p in pillars}

    # 1. 检测六合
    partner = ZHI_LIUHE.get(flow_branch)
    if partner:
        for pillar in pillars:
            natal_zhi = branches[pillar]
            if natal_zhi == partner:
                shishen_info = get_branch_shishen(bazi, natal_zhi)
                events.append({
                    "type": "branch_harmony",
                    "subtype": "liuhe",
                    "role": "explain",
                    "risk_percent": 0.0,
                    "flow_type": flow_type,
                    "flow_year": flow_year,
                    "flow_label": flow_label,
                    "flow_branch": flow_branch,
                    "group": "",
                    "members": [flow_branch, partner],
                    "matched_branches": [flow_branch, partner],
                    "targets": [{
                        "pillar": pillar,
                        "palace": PILLAR_PALACE_CN.get(pillar, ""),
                        "target_branch": natal_zhi,
                        "position_weight": _get_position_weight(pillar, "zhi"),
                        "branch_gan": bazi[pillar].get("gan"),
                        "branch_shishen": shishen_info,
                    }],
                })

    # 2. 检测三合局（完整三合 + 半合）
    flow_group = ZHI_SANHE.get(flow_branch)
    if flow_group:
        # 收集命局中属于该三合局的地支（允许同一支出现在多个宫位）
        found_pillars_by_zhi: Dict[str, List[str]] = {}  # zhi -> [pillars]
        for pillar in pillars:
            natal_zhi = branches[pillar]
            if natal_zhi in flow_group and natal_zhi != flow_branch:
                found_pillars_by_zhi.setdefault(natal_zhi, []).append(pillar)

        unique_branches = list(found_pillars_by_zhi.keys())
        
        # 2.1 完整三合：流年/大运支 + 命局两个不同地支
        if len(unique_branches) == 2:
            element = SANHE_ELEMENT_MAP.get(flow_branch)
            all_branches = [flow_branch] + unique_branches
            targets = []
            for zhi in unique_branches:
                # 取第一个出现的柱位（如果有多个，取第一个）
                pillar = found_pillars_by_zhi[zhi][0]
                shishen_info = get_branch_shishen(bazi, zhi)
                targets.append({
                    "pillar": pillar,
                    "palace": PILLAR_PALACE_CN.get(pillar, ""),
                    "target_branch": zhi,
                    "position_weight": _get_position_weight(pillar, "zhi"),
                    "branch_gan": bazi[pillar].get("gan"),
                    "branch_shishen": shishen_info,
                })

            events.append({
                "type": "branch_harmony",
                "subtype": "sanhe",
                "role": "explain",
                "risk_percent": 0.0,
                "flow_type": flow_type,
                "flow_year": flow_year,
                "flow_label": flow_label,
                "flow_branch": flow_branch,
                "group": f"{element}局" if element else "",
                "members": flow_group,
                "matched_branches": all_branches,
                "targets": targets,
            })
        # 2.2 半合：必须包含三合局的“中间那一支”，否则不算半合
        center = flow_group[1]
        element = SANHE_ELEMENT_MAP.get(center)

        # 左半合：左支 + 中间支
        left = flow_group[0]
        right = flow_group[2]

        # 流年/大运支作为其中一支，命局提供另一支
        def _emit_banhe(other_zhi: str):
            """内部辅助：根据 other_zhi（另一支）发出半合事件。

            注意：如果命局中同一地支出现在多个宫位（例如酉在年支和月支），
            需要为每个宫位各生成一条半合事件，以便在输出时分别标注不同宫位。
            """
            # 命局中所有匹配的柱位
            other_pillars = found_pillars_by_zhi.get(other_zhi, [])
            if not other_pillars:
                return
            for pillar in other_pillars:
                shishen_info = get_branch_shishen(bazi, other_zhi)
                targets = [{
                    "pillar": pillar,
                    "palace": PILLAR_PALACE_CN.get(pillar, ""),
                    "target_branch": other_zhi,
                    "position_weight": _get_position_weight(pillar, "zhi"),
                    "branch_gan": bazi[pillar].get("gan"),
                    "branch_shishen": shishen_info,
                }]
                events.append({
                    "type": "branch_harmony",
                    "subtype": "banhe",
                    "role": "explain",
                    "risk_percent": 0.0,
                    "flow_type": flow_type,
                    "flow_year": flow_year,
                    "flow_label": flow_label,
                    "flow_branch": flow_branch,
                    "group": f"{element}局" if element else "",
                    "members": flow_group,
                    "matched_branches": [flow_branch, other_zhi],
                    "targets": targets,
                })

        # 根据 flow_branch 所在位置，决定合法的半合对
        if flow_branch == left and center in found_pillars_by_zhi:
            _emit_banhe(center)
        elif flow_branch == center and left in found_pillars_by_zhi:
            _emit_banhe(left)
        elif flow_branch == center and right in found_pillars_by_zhi:
            _emit_banhe(right)
        elif flow_branch == right and center in found_pillars_by_zhi:
            _emit_banhe(center)

    # 3. 检测三会（流年/大运 + 命局两个地支 = 完整三会）
    flow_sanhui_group = ZHI_SANHUI.get(flow_branch)
    if flow_sanhui_group:
        # 收集命局中属于该三会的地支（去重）
        found_pillars_by_zhi: Dict[str, List[str]] = {}  # zhi -> [pillars]
        for pillar in pillars:
            natal_zhi = branches[pillar]
            if natal_zhi in flow_sanhui_group and natal_zhi != flow_branch:
                if natal_zhi not in found_pillars_by_zhi:
                    found_pillars_by_zhi[natal_zhi] = []
                found_pillars_by_zhi[natal_zhi].append(pillar)

        unique_branches = list(found_pillars_by_zhi.keys())
        
        if len(unique_branches) == 2:
            # 流年/大运 + 命局两个不同地支 = 完整三会
            hui_name = SANHUI_NAME_MAP.get(flow_branch)
            all_branches = [flow_branch] + unique_branches
            targets = []
            for zhi in unique_branches:
                # 取第一个出现的柱位（如果有多个，取第一个）
                pillar = found_pillars_by_zhi[zhi][0]
                shishen_info = get_branch_shishen(bazi, zhi)
                targets.append({
                    "pillar": pillar,
                    "palace": PILLAR_PALACE_CN.get(pillar, ""),
                    "target_branch": zhi,
                    "position_weight": _get_position_weight(pillar, "zhi"),
                    "branch_gan": bazi[pillar].get("gan"),
                    "branch_shishen": shishen_info,
                })

            events.append({
                "type": "branch_harmony",
                "subtype": "sanhui",
                "role": "explain",
                "risk_percent": 0.0,
                "flow_type": flow_type,
                "flow_year": flow_year,
                "flow_label": flow_label,
                "flow_branch": flow_branch,
                "group": hui_name,
                "members": flow_sanhui_group,
                "matched_branches": all_branches,
                "targets": targets,
            })

    return events


def detect_sanhe_complete(
    bazi: Dict[str, Dict[str, str]],
    dayun_branch: Optional[str] = None,
    dayun_label: Optional[str] = None,
    dayun_index: Optional[int] = None,
    liunian_branch: Optional[str] = None,
    liunian_year: Optional[int] = None,
    liunian_label: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """检测完整三合局（必须三支齐全），记录每个字的来源。
    
    参数:
        bazi: 命局四柱
        dayun_branch: 大运地支（可选）
        dayun_label: 大运标签（如"壬寅"）（可选）
        dayun_index: 大运索引（可选）
        liunian_branch: 流年地支（可选）
        liunian_year: 流年年份（可选）
        liunian_label: 流年标签（如"壬寅"）（可选）
    
    返回:
        三合局事件列表，每个事件包含 sources 字段，记录每个字的来源。
    """
    events: List[Dict[str, Any]] = []
    pillars = ["year", "month", "day", "hour"]
    branches = {p: bazi[p]["zhi"] for p in pillars}
    
    # 柱位中文名称映射
    PILLAR_NAME_CN = {
        "year": "年柱",
        "month": "月柱",
        "day": "日柱",
        "hour": "时柱",
    }
    
    # 遍历所有三合局
    seen_groups: set = set()
    for _, group in ZHI_SANHE.items():
        group_key = tuple(sorted(group))
        if group_key in seen_groups:
            continue
        seen_groups.add(group_key)
        
        element = SANHE_ELEMENT_MAP.get(group[0])
        group_name = f"{element}局" if element else ""
        
        # 收集每个字的所有来源
        sources_by_zhi: Dict[str, List[Dict[str, Any]]] = {}
        
        # 1. 收集原局中的来源
        for pillar in pillars:
            natal_zhi = branches[pillar]
            if natal_zhi in group:
                sources_by_zhi.setdefault(natal_zhi, []).append({
                    "zhi": natal_zhi,
                    "source_type": "natal",
                    "pillar": pillar,
                    "palace": PILLAR_PALACE_CN.get(pillar, ""),
                    "pillar_name": PILLAR_NAME_CN.get(pillar, ""),
                })
        
        # 2. 收集大运中的来源
        if dayun_branch and dayun_branch in group:
            sources_by_zhi.setdefault(dayun_branch, []).append({
                "zhi": dayun_branch,
                "source_type": "dayun",
                "label": dayun_label or "",
                "index": dayun_index,
            })
        
        # 3. 收集流年中的来源
        if liunian_branch and liunian_branch in group:
            sources_by_zhi.setdefault(liunian_branch, []).append({
                "zhi": liunian_branch,
                "source_type": "liunian",
                "year": liunian_year,
                "label": liunian_label or "",
            })
        
        # 检查是否三支齐全
        if len(sources_by_zhi) == 3:
            # 三支齐全，生成三合局事件
            all_sources = []
            for zhi in group:
                if zhi in sources_by_zhi:
                    all_sources.extend(sources_by_zhi[zhi])
            
            events.append({
                "type": "branch_harmony",
                "subtype": "sanhe",
                "role": "explain",
                "risk_percent": 0.0,
                "group": group_name,
                "members": group,
                "matched_branches": group,
                "sources": all_sources,
                "dayun_branch": dayun_branch,
                "dayun_label": dayun_label,
                "dayun_index": dayun_index,
                "liunian_branch": liunian_branch,
                "liunian_year": liunian_year,
                "liunian_label": liunian_label,
            })
    
    return events


def detect_sanhui_complete(
    bazi: Dict[str, Dict[str, str]],
    dayun_branch: Optional[str] = None,
    dayun_label: Optional[str] = None,
    dayun_index: Optional[int] = None,
    liunian_branch: Optional[str] = None,
    liunian_year: Optional[int] = None,
    liunian_label: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """检测完整三会局（必须三支齐全），记录每个字的来源。
    
    参数:
        bazi: 命局四柱
        dayun_branch: 大运地支（可选）
        dayun_label: 大运标签（如"壬寅"）（可选）
        dayun_index: 大运索引（可选）
        liunian_branch: 流年地支（可选）
        liunian_year: 流年年份（可选）
        liunian_label: 流年标签（如"壬寅"）（可选）
    
    返回:
        三会局事件列表，每个事件包含 sources 字段，记录每个字的来源。
    """
    events: List[Dict[str, Any]] = []
    pillars = ["year", "month", "day", "hour"]
    branches = {p: bazi[p]["zhi"] for p in pillars}
    
    # 柱位中文名称映射
    PILLAR_NAME_CN = {
        "year": "年柱",
        "month": "月柱",
        "day": "日柱",
        "hour": "时柱",
    }
    
    # 遍历所有三会局（去重，每个三会局只检测一次）
    seen_groups: set = set()
    for zhi, group in ZHI_SANHUI.items():
        group_key = tuple(sorted(group))
        if group_key in seen_groups:
            continue
        seen_groups.add(group_key)
        
        hui_name = SANHUI_NAME_MAP.get(group[0])
        
        # 收集每个字的所有来源
        sources_by_zhi: Dict[str, List[Dict[str, Any]]] = {}
        
        # 1. 收集原局中的来源
        for pillar in pillars:
            natal_zhi = branches[pillar]
            if natal_zhi in group:
                sources_by_zhi.setdefault(natal_zhi, []).append({
                    "zhi": natal_zhi,
                    "source_type": "natal",
                    "pillar": pillar,
                    "palace": PILLAR_PALACE_CN.get(pillar, ""),
                    "pillar_name": PILLAR_NAME_CN.get(pillar, ""),
                })
        
        # 2. 收集大运中的来源
        if dayun_branch and dayun_branch in group:
            sources_by_zhi.setdefault(dayun_branch, []).append({
                "zhi": dayun_branch,
                "source_type": "dayun",
                "label": dayun_label or "",
                "index": dayun_index,
            })
        
        # 3. 收集流年中的来源
        if liunian_branch and liunian_branch in group:
            sources_by_zhi.setdefault(liunian_branch, []).append({
                "zhi": liunian_branch,
                "source_type": "liunian",
                "year": liunian_year,
                "label": liunian_label or "",
            })
        
        # 检查是否三支齐全
        if len(sources_by_zhi) == 3:
            # 三支齐全，生成三会局事件
            all_sources = []
            for zhi in group:
                if zhi in sources_by_zhi:
                    all_sources.extend(sources_by_zhi[zhi])
            
            events.append({
                "type": "branch_harmony",
                "subtype": "sanhui",
                "role": "explain",
                "risk_percent": 0.0,
                "group": hui_name,
                "members": group,
                "matched_branches": group,
                "sources": all_sources,
                "dayun_branch": dayun_branch,
                "dayun_label": dayun_label,
                "dayun_index": dayun_index,
                "liunian_branch": liunian_branch,
                "liunian_year": liunian_year,
                "liunian_label": liunian_label,
            })
    
    return events
