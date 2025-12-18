# -*- coding: utf-8 -*-
"""用神计算：全局五行占比 + 按规则选用神。"""

from typing import Dict, List, Tuple

from .config import GAN_WUXING, ZHI_WUXING, ELEMENTS


def calc_global_element_distribution(bazi: Dict[str, Dict[str, str]]) -> Dict[str, float]:
    """计算“全局八个字”的五行占比（木火土金水）。

    规则：八个字（4 干 4 支）每个字权重相同，各记 1 份。
    不区分位置权重，只算频率。
    """
    counts: Dict[str, float] = {e: 0.0 for e in ELEMENTS}
    total = 0.0

    for pillar in ("year", "month", "day", "hour"):
        gan = bazi[pillar]["gan"]
        zhi = bazi[pillar]["zhi"]

        wx_gan = GAN_WUXING.get(gan)
        wx_zhi = ZHI_WUXING.get(zhi)

        if wx_gan in counts:
            counts[wx_gan] += 1.0
            total += 1.0
        if wx_zhi in counts:
            counts[wx_zhi] += 1.0
            total += 1.0

    if total == 0:
        return {e: 0.0 for e in ELEMENTS}

    return {e: counts[e] / total * 100.0 for e in ELEMENTS}


def determine_yongshen(
    bazi: Dict[str, Dict[str, str]],
    strength_percent: float,
    global_dist: Dict[str, float],
) -> Dict[str, object]:
    """根据日主（天干）+ 日主强弱 + 全局五行占比，确定用神五行。

    规则来自你的描述：
      - 甲乙木：>=50 强，<50 弱
      - 丙丁火：>=50 强，<50 弱
      - 戊己土：>=50 强，<50 弱
      - 庚金：  >=25 强，<25 弱
      - 辛金：  特判“水>70%”优先；否则 >=20 强，<20 弱
      - 壬癸水：>=50 强，<50 弱
    """
    day_gan = bazi["day"]["gan"]
    day_element = GAN_WUXING.get(day_gan)
    water_percent = global_dist.get("水", 0.0)

    yongshen: List[str] = []

    # 甲乙木
    if day_gan in ("甲", "乙"):
        if strength_percent >= 50.0:
            # 强：取火土
            yongshen = ["火", "土"]
        else:
            # 弱：取水木
            yongshen = ["水", "木"]

    # 丙丁火
    elif day_gan in ("丙", "丁"):
        if strength_percent >= 50.0:
            # 强：金水
            yongshen = ["金", "水"]
        else:
            # 弱：木火
            yongshen = ["木", "火"]

    # 戊己土
    elif day_gan in ("戊", "己"):
        if strength_percent >= 50.0:
            # 强：金水
            yongshen = ["金", "水"]
        else:
            # 弱：火土
            yongshen = ["火", "土"]

    # 庚金
    elif day_gan == "庚":
        if strength_percent >= 25.0:
            # 强：木火
            yongshen = ["木", "火"]
        else:
            # 弱：土金
            yongshen = ["土", "金"]

    # 辛金
    elif day_gan == "辛":
        # 全局水 > 70% 优先：从“水太多”角度调候
        if water_percent > 70.0:
            yongshen = ["木", "火"]
        else:
            if strength_percent >= 20.0:
                # 强：水木
                yongshen = ["水", "木"]
            else:
                # 弱：土金
                yongshen = ["土", "金"]

    # 壬癸水
    elif day_gan in ("壬", "癸"):
        if strength_percent >= 50.0:
            # 强：木火
            yongshen = ["木", "火"]
        else:
            # 弱：金水
            yongshen = ["金", "水"]

    # 兜底：如果上面没匹配上（理论上不会），简单返回“生扶日主”的五行
    if not yongshen:
        if day_element == "木":
            yongshen = ["水", "木"]
        elif day_element == "火":
            yongshen = ["木", "火"]
        elif day_element == "土":
            yongshen = ["火", "土"]
        elif day_element == "金":
            yongshen = ["土", "金"]
        elif day_element == "水":
            yongshen = ["金", "水"]

    return {
        "day_gan": day_gan,
        "day_element": day_element,
        "strength_percent": float(strength_percent),
        "global_distribution": global_dist,
        "yongshen_elements": yongshen,
        "water_percent": float(water_percent),
    }
