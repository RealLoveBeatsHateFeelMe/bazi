# -*- coding: utf-8 -*-
"""地支刑：检测刑的组合、区分普通刑与墓库刑。"""

from typing import Dict, Any, List, Optional, Set, Tuple

from .config import POSITION_WEIGHTS, PILLAR_PALACE, ZHI_CHONG
from .shishen import get_branch_shishen


# 普通刑的组合（子卯、寅巳、巳申、申寅）
NORMAL_PUNISH_PAIRS: Set[Tuple[str, str]] = {
    ("子", "卯"),
    ("卯", "子"),
    ("寅", "巳"),
    ("巳", "寅"),
    ("巳", "申"),
    ("申", "巳"),
    ("申", "寅"),
    ("寅", "申"),
}

# 墓库刑的组合（丑戌未三刑）
# 注意：辰未不刑，所以不包含 ("辰","未") 和 ("未","辰")
# 丑戌未三刑：丑-戌、戌-未、未-丑
GRAVE_PUNISH_PAIRS: Set[Tuple[str, str]] = {
    ("丑", "戌"),
    ("戌", "丑"),
    ("戌", "未"),
    ("未", "戌"),
    ("未", "丑"),
    ("丑", "未"),
}

# 自刑的组合（辰辰、午午、酉酉、亥亥）
SELF_PUNISH_PAIRS: Set[Tuple[str, str]] = {
    ("辰", "辰"),
    ("午", "午"),
    ("酉", "酉"),
    ("亥", "亥"),
}

# 所有刑的组合
ALL_PUNISH_PAIRS = NORMAL_PUNISH_PAIRS | GRAVE_PUNISH_PAIRS | SELF_PUNISH_PAIRS

# 刑的风险系数
PUNISHMENT_NORMAL_RISK = 5.0  # 普通刑
PUNISHMENT_GRAVE_RISK = 6.0   # 墓库刑（丑戌未三刑）
PUNISHMENT_SELF_RISK = 5.0    # 自刑（辰辰、午午、酉酉、亥亥）

# 静态刑的风险（原基础风险的一半）
STATIC_PUNISH_NORMAL_RISK = PUNISHMENT_NORMAL_RISK * 0.5  # 2.5
STATIC_PUNISH_GRAVE_RISK = PUNISHMENT_GRAVE_RISK * 0.5    # 3.0


def _is_grave_punishment(flow_branch: str, target_branch: str) -> bool:
    """是否属于墓库刑（基于 GRAVE_PUNISH_PAIRS membership）。"""
    return (flow_branch, target_branch) in GRAVE_PUNISH_PAIRS


def _get_punish_targets(flow_branch: str) -> List[str]:
    """根据流年地支，返回所有可能被刑的目标地支列表。"""
    targets = []
    for pair in ALL_PUNISH_PAIRS:
        if pair[0] == flow_branch:
            targets.append(pair[1])
    return list(set(targets))  # 去重


def detect_branch_punishments(
    bazi: Dict[str, Dict[str, str]],
    flow_branch: str,
    flow_type: str,
    flow_year: Optional[int] = None,
    flow_label: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """检测某个流年 / 大运地支，对命局有没有"刑"。

    返回事件列表（可能为空）：
    [
      {
        "type": "punishment",
        "flow_type": "liunian" / "dayun",
        "flow_year": 2024,
        "flow_label": "甲辰",
        "flow_branch": "辰",
        "target_branch": "戌",
        "role": "punisher",
        "base_power_percent": 10.0,  # 被刑宫位的权重（仅展示用）
        "risk_percent": 6.0,         # 固定值：普通刑 5%，墓库刑 6%
        "is_grave": True,            # 是否墓库刑
        "targets": [...],
        "shishens": {...}
      },
      ...
    ]
    """
    punish_targets = _get_punish_targets(flow_branch)
    if not punish_targets:
        return []

    events = []

    for target_branch in punish_targets:
        # 找命局里所有"被刑的那个支"出现在哪里
        target_pillars = []
        for pillar in ("year", "month", "day", "hour"):
            if bazi[pillar]["zhi"] == target_branch:
                target_pillars.append(pillar)

        # 命局里根本没有这个被刑的支，跳过
        if not target_pillars:
            continue

        # 检查是否同时满足"冲"（如果既冲又刑，应该被过滤掉，但这里先检测）
        clash_target = ZHI_CHONG.get(flow_branch)
        if clash_target == target_branch:
            # 既冲又刑，按规则应该只算冲，不算刑
            # 这里仍然生成事件，但上层会过滤
            pass

        # 判断刑的类型
        is_grave = _is_grave_punishment(flow_branch, target_branch)
        is_self = (flow_branch, target_branch) in SELF_PUNISH_PAIRS
        
        # 风险系数（固定值，不按命中柱位数倍增）
        if is_grave:
            risk_percent = PUNISHMENT_GRAVE_RISK  # 6%
        elif is_self:
            risk_percent = PUNISHMENT_SELF_RISK   # 5%
        else:
            risk_percent = PUNISHMENT_NORMAL_RISK  # 5%

        # 流年 / 大运这一边的十神（在循环外计算，因为对所有柱都一样）
        flow_tg = get_branch_shishen(bazi, flow_branch)
        target_tg = get_branch_shishen(bazi, target_branch)

        # 为命局中每个被刑的柱生成一个独立的刑事件
        for pillar in target_pillars:
            key = f"{pillar}_zhi"
            w = POSITION_WEIGHTS.get(key, 0.0)
            base_power_percent = w * 100.0  # 单个柱的权重

            # 该柱地支代表的十神
            tg = get_branch_shishen(bazi, target_branch)

            targets = [{
                "pillar": pillar,
                "palace": PILLAR_PALACE.get(pillar, ""),
                "position_weight": w,
                "branch_gan": tg["gan"] if tg else None,
                "branch_shishen": tg["shishen"] if tg else None,
            }]

            events.append(
                {
                    "type": "punishment",
                    "flow_type": flow_type,
                    "flow_year": flow_year,
                    "flow_label": flow_label,
                    "flow_branch": flow_branch,
                    "target_branch": target_branch,
                    "role": "punisher",
                    "base_power_percent": base_power_percent,
                    "risk_percent": risk_percent,
                    "is_grave": is_grave,
                    "targets": targets,
                    "shishens": {
                        "flow_branch": flow_tg,
                        "target_branch": target_tg,
                    },
                }
            )

    return events


def detect_natal_clashes_and_punishments(
    bazi: Dict[str, Dict[str, str]]
) -> Dict[str, Any]:
    """检测命局内部的冲和刑。

    返回：
    {
      "clashes": [...],  # 命局内部的冲
      "punishments": [...],  # 命局内部的刑
    }
    """
    clashes = []
    punishments = []

    # 检测命局内部的冲（使用 clash.py 的逻辑）
    from .clash import detect_branch_clash

    pillars = ["year", "month", "day", "hour"]
    for i, pillar1 in enumerate(pillars):
        for pillar2 in pillars[i + 1 :]:
            zhi1 = bazi[pillar1]["zhi"]
            zhi2 = bazi[pillar2]["zhi"]
            clash_target = ZHI_CHONG.get(zhi1)
            if clash_target == zhi2:
                clash_ev = detect_branch_clash(
                    bazi, zhi1, "natal", None, f"{pillar1}-{pillar2}"
                )
                if clash_ev:
                    clashes.append(clash_ev)

    # 检测命局内部的刑
    # 对于自刑（如酉酉），只检测一次，避免重复计算
    self_punish_processed = set()  # 记录已处理的自刑地支
    
    for i, pillar1 in enumerate(pillars):
        for pillar2 in pillars[i + 1 :]:
            zhi1 = bazi[pillar1]["zhi"]
            zhi2 = bazi[pillar2]["zhi"]
            if (zhi1, zhi2) in ALL_PUNISH_PAIRS:
                # 检查是否同时满足"冲"（如果既冲又刑，只算冲）
                clash_target = ZHI_CHONG.get(zhi1)
                if clash_target == zhi2:
                    continue  # 跳过，只算冲

                # 直接生成一个刑事件，不调用 detect_branch_punishments（避免重复）
                # 判断刑的类型
                is_grave = _is_grave_punishment(zhi1, zhi2)
                is_self = (zhi1, zhi2) in SELF_PUNISH_PAIRS
                
                # 对于自刑，如果已经处理过这个地支，跳过（只检测第一次出现的自刑）
                if is_self:
                    if zhi1 in self_punish_processed:
                        continue
                    self_punish_processed.add(zhi1)
                    # 同时标记zhi2，因为自刑是双向的（酉酉自刑，无论是年-月还是月-年，都只算一次）
                    self_punish_processed.add(zhi2)
                
                if is_grave:
                    risk_percent = PUNISHMENT_GRAVE_RISK  # 6%
                elif is_self:
                    risk_percent = PUNISHMENT_SELF_RISK   # 5%
                else:
                    risk_percent = PUNISHMENT_NORMAL_RISK  # 5%
                
                # 计算权重（仅展示用）
                key1 = f"{pillar1}_zhi"
                key2 = f"{pillar2}_zhi"
                w1 = POSITION_WEIGHTS.get(key1, 0.0)
                w2 = POSITION_WEIGHTS.get(key2, 0.0)
                base_power_percent = (w1 + w2) * 100.0
                
                punishments.append({
                    "type": "punishment",
                    "flow_type": "natal",
                    "flow_branch": zhi1,
                    "target_branch": zhi2,
                    "role": "punisher",
                    "base_power_percent": base_power_percent,
                    "risk_percent": risk_percent,
                    "is_grave": is_grave,
                    "targets": [
                        {
                            "pillar": pillar2,
                            "palace": PILLAR_PALACE.get(pillar2, ""),
                            "position_weight": w2,
                        }
                    ],
                })

    return {
        "clashes": clashes,
        "punishments": punishments,
    }
