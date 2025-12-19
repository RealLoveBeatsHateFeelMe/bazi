# -*- coding: utf-8 -*-
"""地支冲：算什么和什么冲、力量多大、冲到哪几个宫 + 冲击等级 + 十神 + 可叠加评分。"""

from typing import Dict, Any, List, Optional

from .config import POSITION_WEIGHTS, PILLAR_PALACE, ZHI_CHONG, GAN_WUXING, KE_MAP, TIAN_KE_DI_CHONG_EXTRA_RISK
from .shishen import get_branch_shishen


# 墓库冲：辰戌、丑未 互冲比普通冲更重
GRAVE_CLASH_PAIRS = {
    ("辰", "戌"),
    ("戌", "辰"),
    ("丑", "未"),
    ("未", "丑"),
}


def _is_grave_clash(flow_branch: str, target_branch: str) -> bool:
    """是否属于墓库之间的对冲（辰戌 / 丑未）。"""
    return (flow_branch, target_branch) in GRAVE_CLASH_PAIRS


def branch_total_power(bazi: Dict[str, Dict[str, str]], target_branch: str) -> float:
    """某个地支在命局中的总力量（0~1），
    = 这个支在四柱中所有出现位置的地支权重之和。
    """
    total = 0.0
    for pillar in ("year", "month", "day", "hour"):
        if bazi[pillar]["zhi"] == target_branch:
            key = f"{pillar}_zhi"
            total += POSITION_WEIGHTS.get(key, 0.0)
    return total


def _classify_impact(risk_percent: float) -> str:
    """按“最终影响分”分档。

    规则：
        ≤15%   → 只论有变化（minor）
        15–30% → 有较大变化（moderate）
        ≥30%   → 要严肃提醒（major）
    """
    if risk_percent <= 15.0:
        return "minor"
    if risk_percent <= 30.0:
        return "moderate"
    return "major"


def _classify_suggestion(impact_level: str) -> str:
    """将 impact_level 映射到提醒等级。"""
    if impact_level == "minor":
        return "normal"        # 只预测变化
    if impact_level == "moderate":
        return "be_careful"    # 预测变化 + 提醒注意
    return "strong_warning"    # 提醒买保险、别冒险、别违法等


def _check_tian_ke_di_chong(
    flow_gan: Optional[str],
    flow_branch: str,
    target_gan: Optional[str],
    target_branch: str,
) -> bool:
    """检查是否满足天克地冲条件。
    
    天克地冲 = 地支互冲 + 天干五行互克
    
    参数:
        flow_gan: 流年/大运天干
        flow_branch: 流年/大运地支
        target_gan: 命局/大运天干（被冲的那一柱的天干）
        target_branch: 命局/大运地支（被冲的那一柱的地支）
    
    返回:
        True 如果满足天克地冲条件，否则 False
    """
    # 检查地支是否互冲
    clash_target = ZHI_CHONG.get(flow_branch)
    if clash_target != target_branch:
        return False
    
    # 检查天干是否互克
    if not flow_gan or not target_gan:
        return False
    
    flow_element = GAN_WUXING.get(flow_gan)
    target_element = GAN_WUXING.get(target_gan)
    
    if not flow_element or not target_element:
        return False
    
    # 检查是否互克：KE_MAP[e1] == e2 或 KE_MAP[e2] == e1
    return (KE_MAP.get(flow_element) == target_element or 
            KE_MAP.get(target_element) == flow_element)


def detect_branch_clash(
    bazi: Dict[str, Dict[str, str]],
    flow_branch: str,
    flow_type: str,
    flow_year: Optional[int] = None,
    flow_label: Optional[str] = None,
    flow_gan: Optional[str] = None,  # 新增：流年/大运天干（用于天克地冲检测）
) -> Optional[Dict[str, Any]]:
    """检测某个流年 / 大运地支，对命局有没有“冲”。

    返回一条事件结构：
    {
      "type": "branch_clash",
      "flow_type": "liunian" / "dayun",
      "flow_year": 2024,
      "flow_label": "甲辰",
      "flow_branch": "辰",
      "target_branch": "戌",

      "base_power": 0.10,
      "base_power_percent": 10.0,   # 纯粹按命局权重算出来的冲力量
      "grave_bonus_percent": 5.0,   # 若为墓库对冲，否则 0
      "risk_percent": 15.0,         # 可叠加总影响（后面还能再加枭神夺食等）

      "impact_level": "minor" / "moderate" / "major",
      "suggestion_level": "normal" / "be_careful" / "strong_warning",

      "targets": [...],
      "shishens": {...}
    }
    没有冲则返回 None。
    """
    target_branch = ZHI_CHONG.get(flow_branch)
    if not target_branch:
        return None

    targets: List[Dict[str, Any]] = []
    base_total = 0.0

    # 1. 找命局里所有“被冲的那个支”出现在哪里 + 权重
    for pillar in ("year", "month", "day", "hour"):
        if bazi[pillar]["zhi"] == target_branch:
            key = f"{pillar}_zhi"
            w = POSITION_WEIGHTS.get(key, 0.0)
            base_total += w

            # 该柱地支代表的十神（例如：正官、伤官等）
            tg = get_branch_shishen(bazi, target_branch)

            targets.append(
                {
                    "pillar": pillar,
                    "palace": PILLAR_PALACE.get(pillar, ""),
                    "position_weight": w,
                    "branch_gan": tg["gan"] if tg else None,
                    "branch_shishen": tg["shishen"] if tg else None,
                }
            )

    # 命局里根本没有这个被冲的支，就不算事件
    if not targets:
        return None

    # 2. 基础冲力量（只看命局权重）
    base_power = base_total             # 0~1
    base_power_percent = base_power * 100.0

    # 3. 额外加成：墓库对冲 +5%
    grave_bonus_percent = 0.0
    if _is_grave_clash(flow_branch, target_branch):
        grave_bonus_percent += 5.0

    # 未来在这里继续加：
    #   - if 有天克地冲: extra_bonus += X
    #   - if 有“枭神夺食”: extra_bonus += Y
    #   - if 有“伤官见官”: extra_bonus += Z
    # 4. 天克地冲检测（在冲的基础上额外 +10%，每个满足的柱都加一次）
    tkdc_bonus_percent = 0.0
    tkdc_targets: List[Dict[str, Any]] = []
    
    if flow_gan:
        # 检查每个被冲的柱是否满足天克地冲
        for target in targets:
            target_pillar = target.get("pillar")
            target_gan = bazi[target_pillar]["gan"]
            
            if _check_tian_ke_di_chong(flow_gan, flow_branch, target_gan, target_branch):
                # 记录天克地冲（用于标注）
                tkdc_targets.append({
                    "pillar": target_pillar,
                    "palace": target.get("palace"),
                    "target_gan": target_gan,
                    "flow_gan": flow_gan,
                })
                # 天克地冲的力量加成规则：
                # - 年柱：不加成（0%）
                # - 日柱：额外加10% + 10% = 20%（基础10% + 日柱额外10%）
                # - 其他柱（月柱、时柱）：正常加10%
                if target_pillar == "year":
                    # 年柱不加成
                    pass
                elif target_pillar == "day":
                    # 日柱额外加10% + 10% = 20%
                    tkdc_bonus_percent += TIAN_KE_DI_CHONG_EXTRA_RISK * 2
                else:
                    # 月柱、时柱正常加10%
                    tkdc_bonus_percent += TIAN_KE_DI_CHONG_EXTRA_RISK
    
    extra_bonus_percent = grave_bonus_percent + tkdc_bonus_percent

    # 5. 总影响分 = 基础冲 + 各种加成（封顶 100）
    risk_percent = base_power_percent + extra_bonus_percent
    if risk_percent > 100.0:
        risk_percent = 100.0

    impact_level = _classify_impact(risk_percent)
    suggestion_level = _classify_suggestion(impact_level)

    # 6. 流年 / 大运这一边的十神（按地支主气来算）
    flow_tg = get_branch_shishen(bazi, flow_branch)
    target_tg = get_branch_shishen(bazi, target_branch)

    result = {
        "type": "branch_clash",
        "role": "base",  # 基础事件，参与线运计算
        "flow_type": flow_type,
        "flow_year": flow_year,
        "flow_label": flow_label,
        "flow_branch": flow_branch,
        "flow_gan": flow_gan,  # 添加flow_gan字段，用于打印天克地冲
        "target_branch": target_branch,

        "base_power": base_power,
        "base_power_percent": base_power_percent,
        "grave_bonus_percent": grave_bonus_percent,
        "tkdc_bonus_percent": tkdc_bonus_percent,  # 天克地冲总加成（包含多个柱的累加）
        "tkdc_targets": tkdc_targets,  # 满足天克地冲的柱列表
        "risk_percent": risk_percent,

        "impact_level": impact_level,
        "suggestion_level": suggestion_level,

        "targets": targets,
        "shishens": {
            "flow_branch": flow_tg,
            "target_branch": target_tg,
        },
    }
    
    # 如果满足天克地冲，添加相关字段
    if tkdc_bonus_percent > 0:
        result["tkdc_bonus_percent"] = tkdc_bonus_percent
        result["is_tian_ke_di_chong"] = True
        result["tkdc_targets"] = tkdc_targets
    
    return result


def detect_natal_tian_ke_di_chong(bazi: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    """检测原局内部的天克地冲。
    
    返回事件列表：
    [
      {
        "type": "natal_tian_ke_di_chong",
        "pillar1": "year",
        "pillar2": "month",
        "gan1": "甲",
        "zhi1": "子",
        "gan2": "庚",
        "zhi2": "午",
        "palace1": "祖上宫（家庭出身、早年环境）",
        "palace2": "婚姻宫",
        "risk_percent": 10.0,  # 天克地冲固定10%
      },
      ...
    ]
    """
    from .config import PILLAR_PALACE, GAN_WUXING, KE_MAP
    
    events = []
    pillars = ["year", "month", "day", "hour"]
    
    for i, pillar1 in enumerate(pillars):
        for pillar2 in pillars[i + 1:]:
            gan1 = bazi[pillar1]["gan"]
            zhi1 = bazi[pillar1]["zhi"]
            gan2 = bazi[pillar2]["gan"]
            zhi2 = bazi[pillar2]["zhi"]
            
            # 检查地支是否互冲
            clash_target = ZHI_CHONG.get(zhi1)
            if clash_target != zhi2:
                continue
            
            # 检查天干是否互克
            gan1_element = GAN_WUXING.get(gan1)
            gan2_element = GAN_WUXING.get(gan2)
            
            if not gan1_element or not gan2_element:
                continue
            
            # 检查是否互克：KE_MAP[e1] == e2 或 KE_MAP[e2] == e1
            is_ke = (KE_MAP.get(gan1_element) == gan2_element or 
                     KE_MAP.get(gan2_element) == gan1_element)
            
            if is_ke:
                events.append({
                    "type": "natal_tian_ke_di_chong",
                    "pillar1": pillar1,
                    "pillar2": pillar2,
                    "gan1": gan1,
                    "zhi1": zhi1,
                    "gan2": gan2,
                    "zhi2": zhi2,
                    "palace1": PILLAR_PALACE.get(pillar1, ""),
                    "palace2": PILLAR_PALACE.get(pillar2, ""),
                    "risk_percent": 10.0,  # 天克地冲固定10%
                })
    
    return events
