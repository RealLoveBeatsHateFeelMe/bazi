# -*- coding: utf-8 -*-
"""十神模式检测：命局、大运、流年的模式识别。"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Set, Tuple

from .shishen import get_shishen, get_branch_main_gan, get_branch_shishen
from .config import PATTERN_GAN_RISK_LIUNIAN, PATTERN_ZHI_RISK_LIUNIAN, GAN_WUXING, ZHI_WUXING


# 模式类型定义
PATTERN_HURT_OFFICER = "hurt_officer"  # 伤官见官
PATTERN_PIANYIN_EATGOD = "pianyin_eatgod"  # 枭神夺食

# 模式匹配规则：{shishen1, shishen2} -> pattern_type
PATTERN_MATCHES: Dict[Tuple[str, str], str] = {
    ("伤官", "正官"): PATTERN_HURT_OFFICER,
    ("正官", "伤官"): PATTERN_HURT_OFFICER,
    ("偏印", "食神"): PATTERN_PIANYIN_EATGOD,
    ("食神", "偏印"): PATTERN_PIANYIN_EATGOD,
}


def _is_pattern_match(shishen1: str, shishen2: str) -> Optional[str]:
    """判断两个十神是否构成模式配对。
    
    返回模式类型（"hurt_officer" 或 "pianyin_eatgod"），如果不匹配则返回 None。
    """
    key = (shishen1, shishen2)
    return PATTERN_MATCHES.get(key)


def _collect_positions(
    bazi: Dict[str, Dict[str, str]],
    day_gan: str,
    dayun_gan: Optional[str] = None,
    dayun_zhi: Optional[str] = None,
    liunian_gan: Optional[str] = None,
    liunian_zhi: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """收集所有天干和地支位置及其十神信息。
    
    返回：
        (gan_positions, zhi_positions)
        每个 position 包含：
        {
            "source": "natal" | "dayun" | "liunian",
            "pillar": "year" | "month" | "day" | "hour" | "dayun" | "liunian",
            "kind": "gan" | "zhi",
            "char": "甲" | "子" 等,
            "shishen": "正官" | "伤官" 等,
        }
    """
    gan_positions: List[Dict[str, Any]] = []
    zhi_positions: List[Dict[str, Any]] = []
    
    # 命局天干
    for pillar in ("year", "month", "day", "hour"):
        gan = bazi[pillar]["gan"]
        shishen = get_shishen(day_gan, gan)
        if shishen:
            gan_positions.append({
                "source": "natal",
                "pillar": pillar,
                "kind": "gan",
                "char": gan,
                "shishen": shishen,
            })
    
    # 命局地支（主气）
    for pillar in ("year", "month", "day", "hour"):
        zhi = bazi[pillar]["zhi"]
        branch_info = get_branch_shishen(bazi, zhi)
        if branch_info and branch_info.get("shishen"):
            zhi_positions.append({
                "source": "natal",
                "pillar": pillar,
                "kind": "zhi",
                "char": zhi,
                "shishen": branch_info["shishen"],
            })
    
    # 大运天干
    if dayun_gan:
        shishen = get_shishen(day_gan, dayun_gan)
        if shishen:
            gan_positions.append({
                "source": "dayun",
                "pillar": "dayun",
                "kind": "gan",
                "char": dayun_gan,
                "shishen": shishen,
            })
    
    # 大运地支（主气）
    if dayun_zhi:
        branch_info = get_branch_shishen(bazi, dayun_zhi)
        if branch_info and branch_info.get("shishen"):
            zhi_positions.append({
                "source": "dayun",
                "pillar": "dayun",
                "kind": "zhi",
                "char": dayun_zhi,
                "shishen": branch_info["shishen"],
            })
    
    # 流年天干
    if liunian_gan:
        shishen = get_shishen(day_gan, liunian_gan)
        if shishen:
            gan_positions.append({
                "source": "liunian",
                "pillar": "liunian",
                "kind": "gan",
                "char": liunian_gan,
                "shishen": shishen,
            })
    
    # 流年地支（主气）
    if liunian_zhi:
        branch_info = get_branch_shishen(bazi, liunian_zhi)
        if branch_info and branch_info.get("shishen"):
            zhi_positions.append({
                "source": "liunian",
                "pillar": "liunian",
                "kind": "zhi",
                "char": liunian_zhi,
                "shishen": branch_info["shishen"],
            })
    
    return gan_positions, zhi_positions


def detect_natal_patterns(bazi: Dict[str, Dict[str, str]], day_gan: str) -> List[Dict[str, Any]]:
    """检测命局静态模式（§5.3.1）。
    
    返回模式列表，每个模式包含：
      {
        "pattern_type": "hurt_officer" | "pianyin_eatgod",
        "layer": "natal",
        "pairs": [
            {
                "pos1": {"source": "natal", "pillar": "year", "kind": "gan", "char": "甲", "shishen": "伤官"},
                "pos2": {"source": "natal", "pillar": "month", "kind": "gan", "char": "辛", "shishen": "正官"},
      },
      ...
    ]
    }
    """
    gan_positions, zhi_positions = _collect_positions(bazi, day_gan)
    
    patterns: Dict[str, Dict[str, Any]] = {}
    
    # 天干层配对
    for i, pos1 in enumerate(gan_positions):
        for pos2 in gan_positions[i + 1:]:
            pattern_type = _is_pattern_match(pos1["shishen"], pos2["shishen"])
            if pattern_type:
                if pattern_type not in patterns:
                    patterns[pattern_type] = {
                        "pattern_type": pattern_type,
                        "layer": "natal",
                        "pairs": [],
                    }
                patterns[pattern_type]["pairs"].append({
                    "pos1": pos1,
                    "pos2": pos2,
                })
    
    # 地支层配对
    for i, pos1 in enumerate(zhi_positions):
        for pos2 in zhi_positions[i + 1:]:
            pattern_type = _is_pattern_match(pos1["shishen"], pos2["shishen"])
            if pattern_type:
                if pattern_type not in patterns:
                    patterns[pattern_type] = {
                        "pattern_type": pattern_type,
                        "layer": "natal",
                        "pairs": [],
                    }
                patterns[pattern_type]["pairs"].append({
                    "pos1": pos1,
                    "pos2": pos2,
                })
    
    return list(patterns.values())


def detect_dayun_patterns(
    bazi: Dict[str, Dict[str, str]], 
    day_gan: str, 
    dayun_gan: str, 
    dayun_zhi: str
) -> List[Dict[str, Any]]:
    """检测大运静态模式（§5.3.2）。
    
    返回模式列表，结构同 detect_natal_patterns，但 layer="dayun"。
    只包含至少有一个位置来自大运的模式。
    """
    gan_positions, zhi_positions = _collect_positions(
        bazi, day_gan, dayun_gan=dayun_gan, dayun_zhi=dayun_zhi
    )
    
    patterns: Dict[str, Dict[str, Any]] = {}
    
    # 天干层配对（至少有一个来自大运）
    for i, pos1 in enumerate(gan_positions):
        for pos2 in gan_positions[i + 1:]:
            # 至少有一个位置来自大运
            if pos1["source"] != "dayun" and pos2["source"] != "dayun":
                continue
            pattern_type = _is_pattern_match(pos1["shishen"], pos2["shishen"])
            if pattern_type:
                if pattern_type not in patterns:
                    patterns[pattern_type] = {
                        "pattern_type": pattern_type,
                        "layer": "dayun",
                        "pairs": [],
                    }
                patterns[pattern_type]["pairs"].append({
                    "pos1": pos1,
                    "pos2": pos2,
                })
    
    # 地支层配对（至少有一个来自大运）
    for i, pos1 in enumerate(zhi_positions):
        for pos2 in zhi_positions[i + 1:]:
            # 至少有一个位置来自大运
            if pos1["source"] != "dayun" and pos2["source"] != "dayun":
                continue
            pattern_type = _is_pattern_match(pos1["shishen"], pos2["shishen"])
            if pattern_type:
                if pattern_type not in patterns:
                    patterns[pattern_type] = {
                        "pattern_type": pattern_type,
        "layer": "dayun",
                        "pairs": [],
                    }
                patterns[pattern_type]["pairs"].append({
                    "pos1": pos1,
                    "pos2": pos2,
                })
    
    return list(patterns.values())


def detect_liunian_patterns(
    bazi: Dict[str, Dict[str, str]],
    day_gan: str,
    dayun_gan: str,
    dayun_zhi: str,
    liunian_gan: str,
    liunian_zhi: str,
    yongshen_elements: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """检测流年动态模式（§5.3.3），并计算风险。
    
    只建立"包含流年位置"的配对。
    
    参数:
        yongshen_elements: 用神五行列表，用于判断枭神是否是用神
    
    返回模式事件列表，每个事件包含：
    {
        "type": "pattern",
        "pattern_type": "hurt_officer" | "pianyin_eatgod",
        "role": "base",  # 基础事件，参与线运计算
        "kind": "gan" | "zhi",  # 天干层还是地支层
        "risk_percent": 10.0 | 15.0,  # 默认15%，如果枭神是用神则10%
        "pos1": {...},
        "pos2": {...},
        "flow_year": 2024,
        "flow_label": "甲辰",
    }
    """
    gan_positions, zhi_positions = _collect_positions(
        bazi, day_gan,
        dayun_gan=dayun_gan, dayun_zhi=dayun_zhi,
        liunian_gan=liunian_gan, liunian_zhi=liunian_zhi
    )
    
    events: List[Dict[str, Any]] = []
    
    # 天干层：流年天干与其他天干配对
    liunian_gan_pos = next((p for p in gan_positions if p["source"] == "liunian"), None)
    if liunian_gan_pos:
        for other_pos in gan_positions:
            if other_pos["source"] == "liunian":
                continue  # 跳过自己
            pattern_type = _is_pattern_match(liunian_gan_pos["shishen"], other_pos["shishen"])
            if pattern_type:
                # 默认15%风险
                risk = PATTERN_GAN_RISK_LIUNIAN  # 15.0
                # 如果是枭神夺食且枭神（偏印）是用神，则按10%算
                if pattern_type == PATTERN_PIANYIN_EATGOD and yongshen_elements:
                    # 找到偏印位置，检查其五行是否在用神列表中
                    pianyin_pos = liunian_gan_pos if liunian_gan_pos["shishen"] == "偏印" else other_pos
                    if pianyin_pos["shishen"] == "偏印":
                        pianyin_char = pianyin_pos["char"]
                        pianyin_element = GAN_WUXING.get(pianyin_char)
                        if pianyin_element and pianyin_element in yongshen_elements:
                            risk = 10.0
                # 如果是伤官见官且伤官是用神，则按10%算
                elif pattern_type == PATTERN_HURT_OFFICER and yongshen_elements:
                    # 找到伤官位置，检查其五行是否在用神列表中
                    shang_guan_pos = liunian_gan_pos if liunian_gan_pos["shishen"] == "伤官" else other_pos
                    if shang_guan_pos["shishen"] == "伤官":
                        shang_guan_char = shang_guan_pos["char"]
                        shang_guan_element = GAN_WUXING.get(shang_guan_char)
                        if shang_guan_element and shang_guan_element in yongshen_elements:
                            risk = 10.0
                events.append({
                    "type": "pattern",
                    "pattern_type": pattern_type,
                    "role": "base",  # 基础事件，参与线运计算
                    "kind": "gan",
                    "risk_percent": risk,
                    "pos1": liunian_gan_pos,
                    "pos2": other_pos,
                })
    
    # 地支层：流年地支与其他地支配对
    liunian_zhi_pos = next((p for p in zhi_positions if p["source"] == "liunian"), None)
    if liunian_zhi_pos:
        for other_pos in zhi_positions:
            if other_pos["source"] == "liunian":
                continue  # 跳过自己
            pattern_type = _is_pattern_match(liunian_zhi_pos["shishen"], other_pos["shishen"])
            if pattern_type:
                # 默认15%风险
                risk = PATTERN_ZHI_RISK_LIUNIAN  # 15.0
                # 如果是枭神夺食且枭神（偏印）是用神，则按10%算
                if pattern_type == PATTERN_PIANYIN_EATGOD and yongshen_elements:
                    # 找到偏印位置，检查其五行是否在用神列表中
                    pianyin_pos = liunian_zhi_pos if liunian_zhi_pos["shishen"] == "偏印" else other_pos
                    if pianyin_pos["shishen"] == "偏印":
                        pianyin_char = pianyin_pos["char"]
                        # 地支需要先转为主气天干，再查五行
                        pianyin_main_gan = get_branch_main_gan(pianyin_char)
                        if pianyin_main_gan:
                            pianyin_element = GAN_WUXING.get(pianyin_main_gan)
                            if pianyin_element and pianyin_element in yongshen_elements:
                                risk = 10.0
                # 如果是伤官见官且伤官是用神，则按10%算
                elif pattern_type == PATTERN_HURT_OFFICER and yongshen_elements:
                    # 找到伤官位置，检查其五行是否在用神列表中
                    shang_guan_pos = liunian_zhi_pos if liunian_zhi_pos["shishen"] == "伤官" else other_pos
                    if shang_guan_pos["shishen"] == "伤官":
                        shang_guan_char = shang_guan_pos["char"]
                        # 地支需要先转为主气天干，再查五行
                        shang_guan_main_gan = get_branch_main_gan(shang_guan_char)
                        if shang_guan_main_gan:
                            shang_guan_element = GAN_WUXING.get(shang_guan_main_gan)
                            if shang_guan_element and shang_guan_element in yongshen_elements:
                                risk = 10.0
                events.append({
                    "type": "pattern",
                    "pattern_type": pattern_type,
                    "role": "base",  # 基础事件，参与线运计算
                    "kind": "zhi",
                    "risk_percent": risk,
                    "pos1": liunian_zhi_pos,
                    "pos2": other_pos,
                })
    
    return events
