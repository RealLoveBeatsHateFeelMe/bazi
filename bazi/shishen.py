# -*- coding: utf-8 -*-
"""十神计算：日主天干 → 其它干 / 支对应的十神。"""

from typing import Optional, Dict, List, Any

from .config import GAN_WUXING, POSITION_WEIGHTS

# 天干阴阳
GAN_YINYANG: Dict[str, str] = {
    "甲": "阳", "乙": "阴",
    "丙": "阳", "丁": "阴",
    "戊": "阳", "己": "阴",
    "庚": "阳", "辛": "阴",
    "壬": "阳", "癸": "阴",
}

# 五行生：key 生 value
WUXING_SHENG: Dict[str, str] = {
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木",
}

# 五行克：key 克 value
WUXING_KE: Dict[str, str] = {
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木",
}

# 地支主气 → 代表天干（用于“支的十神”）
ZHI_MAIN_GAN: Dict[str, str] = {
    "子": "癸",
    "丑": "己",
    "寅": "甲",
    "卯": "乙",
    "辰": "戊",
    "巳": "丙",
    "午": "丁",
    "未": "己",
    "申": "庚",
    "酉": "辛",
    "戌": "戊",
    "亥": "壬",
}


def get_shishen(day_gan: str, other_gan: str) -> Optional[str]:
    """计算“其它天干”对日主的十神名称。"""
    if day_gan not in GAN_WUXING or other_gan not in GAN_WUXING:
        return None

    self_wx = GAN_WUXING[day_gan]
    other_wx = GAN_WUXING[other_gan]

    self_yin = GAN_YINYANG.get(day_gan)
    other_yin = GAN_YINYANG.get(other_gan)
    same_yin_yang = (self_yin == other_yin)

    # 1. 同五行：比 / 劫
    if other_wx == self_wx:
        return "比肩" if same_yin_yang else "劫财"

    # 2. 我生他：食神 / 伤官
    if WUXING_SHENG.get(self_wx) == other_wx:
        return "食神" if same_yin_yang else "伤官"

    # 3. 他生我：印（同阴阳偏印，异阴阳正印）
    if WUXING_SHENG.get(other_wx) == self_wx:
        return "偏印" if same_yin_yang else "正印"

    # 4. 我克他：财（同阴阳偏财，异阴阳正财）
    if WUXING_KE.get(self_wx) == other_wx:
        return "偏财" if same_yin_yang else "正财"

    # 5. 他克我：官杀（同阴阳七杀，异阴阳正官）
    if WUXING_KE.get(other_wx) == self_wx:
        return "七杀" if same_yin_yang else "正官"

    return None


def get_branch_main_gan(zhi: str) -> Optional[str]:
    """地支主气对应的代表天干。"""
    return ZHI_MAIN_GAN.get(zhi)


def get_branch_shishen(
    bazi: Dict[str, Dict[str, str]], zhi: str
) -> Optional[Dict[str, str]]:
    """给定命局和某个地支，返回这个地支代表的十神信息（以主气代表天干计算）。

    返回：
      {"gan": "辛", "shishen": "正官"}  或 None
    """
    day_gan = bazi["day"]["gan"]
    main_gan = get_branch_main_gan(zhi)
    if not main_gan:
        return None

    ss = get_shishen(day_gan, main_gan)
    if not ss:
        return None

    return {
        "gan": main_gan,
        "shishen": ss,
    }


def get_branch_ten_god(
    bazi: Dict[str, Dict[str, str]], zhi: str
) -> Optional[Dict[str, str]]:
    """兼容旧命名的别名：推荐使用 get_branch_shishen。

    内部直接转调 get_branch_shishen，保持返回结构不变。
    """
    return get_branch_shishen(bazi, zhi)


# ===== 十神类别分类与统计 =====

# 十神到五大类别的映射
SHISHEN_CATEGORY_MAP: Dict[str, str] = {
    "比肩": "比劫",
    "劫财": "比劫",
    "正财": "财星",
    "偏财": "财星",
    "食神": "食伤",
    "伤官": "食伤",
    "正官": "官杀",
    "七杀": "官杀",
    "正印": "印星",
    "偏印": "印星",
}


def classify_shishen_category(shishen_name: str) -> Optional[str]:
    """将具体十神名映射到五大类别之一。"""
    return SHISHEN_CATEGORY_MAP.get(shishen_name)


def compute_shishen_category_percentages(bazi: Dict[str, Dict[str, str]]) -> Dict[str, float]:
    """
    计算五大十神类别（比劫/财星/食伤/官杀/印星）的力量占比（0~100）。
    使用 POSITION_WEIGHTS，对四柱的天干和地支主气按权重累加。
    """
    categories = ["比劫", "财星", "食伤", "官杀", "印星"]
    raw_scores = {c: 0.0 for c in categories}

    day_gan = bazi["day"]["gan"]

    # 1. 天干：year_gan, month_gan, day_gan, hour_gan
    for pillar in ("year", "month", "day", "hour"):
        gan = bazi[pillar]["gan"]
        key = f"{pillar}_gan"
        w = POSITION_WEIGHTS.get(key, 0.0)
        if w <= 0:
            continue

        ss = get_shishen(day_gan, gan)
        if not ss:
            continue

        cat = classify_shishen_category(ss)
        if not cat:
            continue

        raw_scores[cat] += w

    # 2. 地支主气：year_zhi, month_zhi, day_zhi, hour_zhi
    for pillar in ("year", "month", "day", "hour"):
        zhi = bazi[pillar]["zhi"]
        key = f"{pillar}_zhi"
        w = POSITION_WEIGHTS.get(key, 0.0)
        if w <= 0:
            continue

        tg = get_branch_shishen(bazi, zhi)
        if not tg:
            continue

        cat = classify_shishen_category(tg["shishen"])
        if not cat:
            continue

        raw_scores[cat] += w

    total = sum(raw_scores.values()) or 1.0
    return {c: (raw_scores[c] / total) * 100.0 for c in categories}


def detect_stem_pattern_summary(bazi: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    只看四个天干：年、月、日、时。
    如果某一十神类别在天干上出现次数 >= 2，则返回对应的聚合信息。
    """
    day_gan = bazi["day"]["gan"]
    bucket: Dict[str, List[Dict[str, str]]] = {}

    for pillar in ("year", "month", "day", "hour"):
        gan = bazi[pillar]["gan"]
        ss = get_shishen(day_gan, gan)
        if not ss:
            continue
        
        cat = classify_shishen_category(ss)
        if not cat:
            continue
        
        bucket.setdefault(cat, []).append(
            {
                "pillar": pillar,
                "gan": gan,
                "shishen": ss,
            }
        )

    summary: List[Dict[str, Any]] = []
    for cat, members in bucket.items():
        if len(members) >= 2:
            summary.append(
                {
                    "category": cat,
                    "members": members,
                }
            )

    return summary
