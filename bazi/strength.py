# -*- coding: utf-8 -*-
"""日主强弱计算核心。支持拆分正向/负向力量比例。"""

from typing import Dict

from .config import (
    POSITION_WEIGHTS,
    GAN_WUXING,
    ZHI_WUXING,
    RELATION_COEFF,
)


def calc_day_master_strength(bazi: Dict[str, Dict[str, str]]) -> Dict[str, float]:
    """基于四柱八字 JSON 结构计算日主强弱。

    参数 bazi 结构示例：
    {
      "year":  {"gan": "甲", "zhi": "子"},
      "month": {"gan": "丙", "zhi": "午"},
      "day":   {"gan": "丁", "zhi": "巳"},
      "hour":  {"gan": "辛", "zhi": "亥"},
    }

    返回值字段说明：

    - strength_score_raw:
        总体原始得分（正向减去负向），理论范围约在 [-total_strength, +total_strength]
    - strength_percent:
        综合强弱百分比（方便画一条 0–100 的强弱条）
    - support_score:
        正向（生扶）总强度（已乘上权重）
    - drain_score:
        负向（消耗/克制）总强度（已乘上权重，取绝对值）
    - support_percent:
        正向力量占比，例如 30.0 表示生扶约占 30%
    - drain_percent:
        负向力量占比，例如 70.0 表示消耗约占 70%
    """

    day_gan = bazi["day"]["gan"]
    if day_gan not in GAN_WUXING:
        raise ValueError(f"未知日干: {day_gan}")

    self_wuxing = GAN_WUXING[day_gan]
    if self_wuxing not in RELATION_COEFF:
        raise ValueError(f"未定义日主五行关系系数: {self_wuxing}")

    net_score = 0.0        # 综合净得分（正减负）
    support_score = 0.0    # 生扶总强度
    drain_score = 0.0      # 消耗总强度（绝对值）
    total_strength = 0.0   # 归一化用：|coeff| * weight 之和

    for pos, weight in POSITION_WEIGHTS.items():
        if weight == 0:
            continue

        pillar, layer = pos.split("_")  # e.g. "month_zhi" -> ("month", "zhi")
        char = bazi[pillar]["gan" if layer == "gan" else "zhi"]

        # 当前字五行
        if layer == "gan":
            wx = GAN_WUXING.get(char)
        else:
            wx = ZHI_WUXING.get(char)

        if wx is None:
            raise ValueError(f"未知干支或未定义五行映射: {pillar}.{layer} = {char}")

        coeff = RELATION_COEFF[self_wuxing].get(wx, 0.0)
        if coeff == 0:
            continue

        contrib = weight * coeff
        net_score += contrib

        if coeff > 0:
            support_score += contrib
        elif coeff < 0:
            drain_score += -contrib  # 取绝对值

        total_strength += abs(contrib)

    if total_strength == 0:
        strength_percent = 50.0
        support_percent = 50.0
        drain_percent = 50.0
    else:
        # 综合强弱：全部有利 → 100%，全部不利 → 0%
        strength_percent = (net_score + total_strength) / (2 * total_strength) * 100.0
        # 生/减占比
        support_percent = support_score / total_strength * 100.0
        drain_percent = drain_score / total_strength * 100.0

    def _clip01(x: float) -> float:
        if x < 0:
            return 0.0
        if x > 100:
            return 100.0
        return x

    strength_percent = _clip01(strength_percent)
    support_percent = _clip01(support_percent)
    drain_percent = _clip01(drain_percent)

    return {
        "strength_score_raw": float(net_score),
        "strength_percent": float(strength_percent),
        "support_score": float(support_score),
        "drain_score": float(drain_score),
        "support_percent": float(support_percent),  # 生 / 扶 身百分比
        "drain_percent": float(drain_percent),      # 减 / 耗 力百分比
    }
