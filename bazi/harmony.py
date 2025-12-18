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
            "palace": "根基宫",
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
    for zhi, group in ZHI_SANHE.items():
        group_key = tuple(sorted(group))
        if group_key in seen_sanhe:
            continue
        seen_sanhe.add(group_key)

        found_pillars: List[str] = []
        found_branches: List[str] = []
        for pillar in pillars:
            natal_zhi = branches[pillar]
            if natal_zhi in group:
                found_pillars.append(pillar)
                found_branches.append(natal_zhi)

        if len(found_branches) == 3:
            # 完整三合局
            element = SANHE_ELEMENT_MAP.get(found_branches[0])
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
                "group": f"{element}局",
                "members": group,
                "matched_branches": found_branches,
                "targets": targets,
            })
        elif len(found_branches) == 2:
            # 半合（同一三合局齐两支）
            element = SANHE_ELEMENT_MAP.get(found_branches[0])
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
                "subtype": "banhe",
                "role": "explain",
                "risk_percent": 0.0,
                "flow_type": "natal",
                "group": f"{element}局",
                "members": group,
                "matched_branches": found_branches,
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
            "palace": "根基宫",
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
        # 收集命局中属于该三合局的地支（去重，因为可能同一地支出现在多个柱）
        found_pillars_by_zhi: Dict[str, List[str]] = {}  # zhi -> [pillars]
        for pillar in pillars:
            natal_zhi = branches[pillar]
            if natal_zhi in flow_group and natal_zhi != flow_branch:
                if natal_zhi not in found_pillars_by_zhi:
                    found_pillars_by_zhi[natal_zhi] = []
                found_pillars_by_zhi[natal_zhi].append(pillar)

        unique_branches = list(found_pillars_by_zhi.keys())
        
        if len(unique_branches) == 2:
            # 流年/大运 + 命局两个不同地支 = 完整三合局
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
                "group": f"{element}局",
                "members": flow_group,
                "matched_branches": all_branches,
                "targets": targets,
            })
        elif len(unique_branches) == 1:
            # 流年/大运 + 命局一个地支 = 半合
            element = SANHE_ELEMENT_MAP.get(flow_branch)
            zhi = unique_branches[0]
            all_branches = [flow_branch, zhi]
            # 取第一个出现的柱位（如果有多个，取第一个）
            pillar = found_pillars_by_zhi[zhi][0]
            shishen_info = get_branch_shishen(bazi, zhi)
            targets = [{
                "pillar": pillar,
                "palace": PILLAR_PALACE_CN.get(pillar, ""),
                "target_branch": zhi,
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
                "group": f"{element}局",
                "members": flow_group,
                "matched_branches": all_branches,
                "targets": targets,
            })

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
