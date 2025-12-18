# -*- coding: utf-8 -*-
"""主要性格 dominant_traits 计算：只看原局，按五大十神 + 子类拆分。"""

from typing import Dict, Any, List

from .config import POSITION_WEIGHTS
from .shishen import get_shishen, get_branch_main_gan, classify_shishen_category


# 五大类固定顺序，便于前端展示
CATEGORIES = ["印星", "财星", "官杀", "食伤", "比劫"]

# 每个大类下的具体十神子类
CATEGORY_SUBS: Dict[str, tuple[str, str]] = {
    "印星": ("正印", "偏印"),
    "财星": ("正财", "偏财"),
    "官杀": ("正官", "七杀"),
    "食伤": ("食神", "伤官"),
    "比劫": ("比肩", "劫财"),
}


def _group_label(cat: str) -> str:
    if cat == "印星":
        return "印"
    if cat == "财星":
        return "财"
    return cat


def _mix_label(cat: str, present_subs: List[str]) -> str:
    if len(present_subs) >= 2:
        if cat == "印星":
            return "正偏印混杂"
        if cat == "财星":
            return "正偏财混杂"
        if cat == "官杀":
            return "官杀混杂"
        if cat == "食伤":
            return "食伤混杂"
        if cat == "比劫":
            return "比劫混杂"
        return "混杂"
    if len(present_subs) == 1:
        only = present_subs[0]
        return f"纯{only}"
    return cat


def compute_dominant_traits(bazi: Dict[str, Dict[str, str]], day_gan: str) -> List[Dict[str, Any]]:
    """按业务口径计算主要性格 dominant_traits。

    只看原局（natal），不看大运/流年。

    - 统计位置：
      - 年干 / 月干 / 时干（排除日干）；
      - 四柱地支主气（年支 / 月支 / 日支 / 时支，通过主气代表天干计算十神）。
    - 权重使用 POSITION_WEIGHTS；
    - 输出：
      - 每个五大类的 total_percent；
      - 每个子类（正印/偏印、正财/偏财等）的 percent；
      - 每个子类的 stems_visible_count（年/月/时三干中透出的次数）；
      - breakdown: {"stems_percent","branches_percent"}；
      - 每个大类的 mix_label（“正偏财混杂” / “官杀混杂” / “纯偏印”等）。
    """
    # 初始化累加器
    total_weight = 0.0
    cat_weight: Dict[str, float] = {c: 0.0 for c in CATEGORIES}

    # 子类在“天干 / 地支”两部分的权重
    sub_stem_weight: Dict[str, Dict[str, float]] = {
        c: {sub: 0.0 for sub in CATEGORY_SUBS[c]} for c in CATEGORIES
    }
    sub_branch_weight: Dict[str, Dict[str, float]] = {
        c: {sub: 0.0 for sub in CATEGORY_SUBS[c]} for c in CATEGORIES
    }

    stems_visible_count: Dict[str, int] = {}

    # 1. 年干 / 月干 / 时干（排除日干）
    for pillar in ("year", "month", "hour"):
        gan = bazi[pillar]["gan"]
        key = f"{pillar}_gan"
        w = POSITION_WEIGHTS.get(key, 0.0)
        if w <= 0:
            continue

        ss = get_shishen(day_gan, gan)
        if not ss:
            continue

        cat = classify_shishen_category(ss)
        if not cat or cat not in CATEGORY_SUBS:
            continue

        total_weight += w
        cat_weight[cat] += w
        if ss in sub_stem_weight[cat]:
            sub_stem_weight[cat][ss] += w

        # 头上透出的次数（只看三天干）
        stems_visible_count[ss] = stems_visible_count.get(ss, 0) + 1

    # 2. 四柱地支主气
    for pillar in ("year", "month", "day", "hour"):
        zhi = bazi[pillar]["zhi"]
        key = f"{pillar}_zhi"
        w = POSITION_WEIGHTS.get(key, 0.0)
        if w <= 0:
            continue

        main_gan = get_branch_main_gan(zhi)
        if not main_gan:
            continue

        ss = get_shishen(day_gan, main_gan)
        if not ss:
            continue

        cat = classify_shishen_category(ss)
        if not cat or cat not in CATEGORY_SUBS:
            continue

        total_weight += w
        cat_weight[cat] += w
        if ss in sub_branch_weight[cat]:
            sub_branch_weight[cat][ss] += w

    # 若完全没有有效权重，直接返回空列表
    if total_weight <= 0:
        return []

    traits: List[Dict[str, Any]] = []

    for cat in CATEGORIES:
        cat_w = cat_weight.get(cat, 0.0)
        if cat_w <= 0:
            continue

        total_percent = round((cat_w / total_weight) * 100.0, 1)

        subs = CATEGORY_SUBS[cat]
        present_subs: List[str] = []
        detail_items: List[Dict[str, Any]] = []

        for sub in subs:
            stem_w = sub_stem_weight[cat].get(sub, 0.0)
            branch_w = sub_branch_weight[cat].get(sub, 0.0)
            sub_total_w = stem_w + branch_w
            if sub_total_w > 0:
                present_subs.append(sub)

            percent = round((sub_total_w / total_weight) * 100.0, 1)
            stems_percent = round((stem_w / total_weight) * 100.0, 1)
            branches_percent = round((branch_w / total_weight) * 100.0, 1)

            detail_items.append(
                {
                    "name": sub,
                    "percent": percent,
                    "stems_visible_count": stems_visible_count.get(sub, 0),
                    "breakdown": {
                        "stems_percent": stems_percent,
                        "branches_percent": branches_percent,
                    },
                }
            )

        mix_label = _mix_label(cat, present_subs)

        traits.append(
            {
                "group": _group_label(cat),
                "total_percent": total_percent,
                "mix_label": mix_label,
                "detail": detail_items,
            }
        )

    # 按 total_percent 降序排序，便于展示
    traits.sort(key=lambda t: t.get("total_percent", 0.0), reverse=True)
    return traits


