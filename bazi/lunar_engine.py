# -*- coding: utf-8 -*-
"""封装 lunar_python：排四柱 + 日主强弱 + 用神 +（示例）大运 / 流年。"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List

from lunar_python import Solar  # 依赖：pip install lunar_python

from .config import GAN_LIST, ZHI_LIST, GAN_WUXING, ZHI_WUXING
from .strength import calc_day_master_strength
from .yongshen import calc_global_element_distribution, determine_yongshen
from .shishen import (
    get_shishen,
    get_branch_shishen,
    classify_shishen_category,
    compute_shishen_category_percentages,
    detect_stem_pattern_summary,
)
from .patterns import detect_natal_patterns
from .punishment import detect_natal_clashes_and_punishments
from .traits import compute_dominant_traits
from .harmony import detect_natal_harmonies


@dataclass
class Pillar:
    gan: str
    zhi: str


def _validate_bazi(bazi: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    for pillar in ("year", "month", "day", "hour"):
        gan = bazi[pillar]["gan"]
        zhi = bazi[pillar]["zhi"]
        if gan not in GAN_LIST:
            raise ValueError(f"天干异常: {pillar}.gan = {gan}")
        if zhi not in ZHI_LIST:
            raise ValueError(f"地支异常: {pillar}.zhi = {zhi}")
    return bazi


def get_bazi(birth_dt: datetime) -> Dict[str, Dict[str, str]]:
    """使用 lunar_python 根据公历出生时间排出四柱八字。

    假设传入的 birth_dt 已经是出生地当地时间（例如北京时间）。
    不做任何“智能纠错时辰”，你给几点就用几点。
    """
    solar = Solar(birth_dt.year, birth_dt.month, birth_dt.day,
                  birth_dt.hour, birth_dt.minute, birth_dt.second)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    bazi = {
        "year":  {"gan": ec.getYearGan(),  "zhi": ec.getYearZhi()},
        "month": {"gan": ec.getMonthGan(), "zhi": ec.getMonthZhi()},
        "day":   {"gan": ec.getDayGan(),   "zhi": ec.getDayZhi()},
        "hour":  {"gan": ec.getTimeGan(),  "zhi": ec.getTimeZhi()},
    }
    return _validate_bazi(bazi)


def _compute_yongshen_explain(
    bazi: Dict[str, Dict[str, str]],
    day_gan: str,
    yongshen_elements: List[str],
) -> Dict[str, Any]:
    """计算用神的十神解释与落点字清单。

    - 不包含日干本身；
    - 地支按主气十神（get_branch_shishen），展示地支字；
    - 元素判定：天干用 GAN_WUXING，地支用 ZHI_WUXING。
    """
    from .shishen import get_shishen as _get_ss_inner, classify_shishen_category as _classify_inner

    yong_set = set(yongshen_elements or [])

    # element -> {"element":..., "shishens": set(), "categories": set()}
    shishen_map: Dict[str, Dict[str, Any]] = {}

    # element -> list of positions
    tokens_map: Dict[str, List[Dict[str, Any]]] = {e: [] for e in yong_set}

    def _ensure_elem(elem: str) -> Dict[str, Any]:
        if elem not in shishen_map:
            shishen_map[elem] = {
                "element": elem,
                "shishens": set(),
                "categories": set(),
            }
        return shishen_map[elem]

    # 1. 三天干（排除日干）
    for pillar in ("year", "month", "hour"):
        gan = bazi[pillar]["gan"]
        elem = GAN_WUXING.get(gan)
        if elem not in yong_set:
            continue

        ss = _get_ss_inner(day_gan, gan)
        if not ss:
            continue

        cat = _classify_inner(ss)
        entry = _ensure_elem(elem)
        entry["shishens"].add(ss)
        if cat:
            entry["categories"].add(cat)

        tokens_map[elem].append(
            {
                "pillar": pillar,
                "kind": "gan",
                "char": gan,
                "element": elem,
                "shishen": ss,
            }
        )

    # 2. 四支主气（包含日支，但不包含日干）
    for pillar in ("year", "month", "day", "hour"):
        zhi = bazi[pillar]["zhi"]
        elem = ZHI_WUXING.get(zhi)
        if elem not in yong_set:
            continue

        tg = get_branch_shishen(bazi, zhi)
        if not tg:
            continue

        ss = tg.get("shishen")
        if not ss:
            continue

        cat = _classify_inner(ss)
        entry = _ensure_elem(elem)
        entry["shishens"].add(ss)
        if cat:
            entry["categories"].add(cat)

        tokens_map[elem].append(
            {
                "pillar": pillar,
                "kind": "zhi",
                "char": zhi,
                "element": elem,
                "shishen": ss,
            }
        )

    # 理论天干映射（用于不在原局的用神五行）
    ELEMENT_TO_THEORETICAL_GANS: Dict[str, List[str]] = {
        "木": ["甲", "乙"],
        "火": ["丙", "丁"],
        "土": ["戊", "己"],
        "金": ["庚", "辛"],
        "水": ["壬", "癸"],
    }

    yongshen_shishen: List[Dict[str, Any]] = []
    for elem in yongshen_elements:
        info = shishen_map.get(elem)
        if not info:
            # 该用神元素在盘中没有对应十神，使用理论天干推导十神
            theoretical_gans = ELEMENT_TO_THEORETICAL_GANS.get(elem, [])
            theoretical_shishens: set = set()
            theoretical_categories: set = set()

            for gan in theoretical_gans:
                ss = _get_ss_inner(day_gan, gan)
                if ss:
                    theoretical_shishens.add(ss)
                    cat = _classify_inner(ss)
                    if cat:
                        theoretical_categories.add(cat)

            yongshen_shishen.append(
                {
                    "element": elem,
                    "shishens": sorted(theoretical_shishens),
                    "categories": sorted(theoretical_categories),
                }
            )
            continue
        yongshen_shishen.append(
            {
                "element": elem,
                "shishens": sorted(info["shishens"]),
                "categories": sorted(info["categories"]),
            }
        )

    yongshen_tokens: List[Dict[str, Any]] = []
    for elem in yongshen_elements:
        positions = tokens_map.get(elem) or []
        yongshen_tokens.append(
            {
                "element": elem,
                "positions": positions,
            }
        )

    return {
        "yongshen_shishen": yongshen_shishen,
        "yongshen_tokens": yongshen_tokens,
    }


def analyze_basic(birth_dt: datetime) -> Dict[str, Any]:
    """综合：排盘 + 日主强弱 + 全局五行占比 + 用神五行。

    返回：
    {
      "bazi": {...},
      "day_master_element": "火",
      "strength_percent": 72.5,
      "strength_score_raw": 0.45,
      "support_percent": 30.0,
      "drain_percent": 70.0,
      "global_element_percentages": {...},
      "yongshen_elements": ["木","火"],
      ...
    }
    """
    bazi = get_bazi(birth_dt)
    strength = calc_day_master_strength(bazi)

    day_gan = bazi["day"]["gan"]
    day_master_element = GAN_WUXING.get(day_gan)

    global_dist = calc_global_element_distribution(bazi)
    yong = determine_yongshen(bazi, strength["strength_percent"], global_dist)

    # 计算十神类别力量占比
    shishen_cat = compute_shishen_category_percentages(bazi)

    # 天干格局提示
    stem_patterns = detect_stem_pattern_summary(bazi)

    # 主要性格：dominant_traits（只看原局，按五大类 + 子类拆分）
    dominant_traits = compute_dominant_traits(bazi, day_gan)

    # 用神列表（基础用神，后续可能被特殊规则补充）
    yongshen_elements = yong["yongshen_elements"].copy()

    # 原局十神模式识别
    natal_patterns = detect_natal_patterns(bazi, day_gan)

    # 原局冲刑识别
    natal_conflicts = detect_natal_clashes_and_punishments(bazi)

    # 原局六合三合识别（只解释，不计分）
    natal_harmonies = detect_natal_harmonies(bazi)

    # 特殊规则：壬癸水日主 + 官杀（土）> 40% + 身弱 → 用神加木
    special_rules = []

    # 保存基础用神（原始计算出的）
    base_yongshen_elements = yongshen_elements.copy()
    
    strength_percent = strength["strength_percent"]
    guansha_percent = shishen_cat.get("官杀", 0.0)

    # 特殊规则1：弱水 + 官杀重 → 补木
    if day_master_element == "水" and day_gan in ("壬", "癸"):
        if strength_percent < 50.0 and guansha_percent >= 40.0:
            if "木" not in yongshen_elements:
                yongshen_elements.append("木")
            special_rules.append("weak_water_heavy_guansha_add_wood")

    # 特殊规则2：弱木 + 强金（官杀%≥40%）+ 基础用神为水木 → 补火
    if day_master_element == "木" and day_gan in ("甲", "乙"):
        # 使用 support_percent < 50.0 判断身弱（必须）
        support_percent = strength.get("support_percent", 0.0)
        if support_percent < 50.0 and guansha_percent >= 40.0:
            # 检查基础用神是否为水木
            base_set = set(base_yongshen_elements)
            if base_set == {"水", "木"} or base_set == {"木", "水"}:
                if "火" not in yongshen_elements:
                    yongshen_elements.append("火")
                special_rules.append("weak_wood_heavy_metal_add_fire")

    # 最终用神（包含规则补充后的）
    final_yongshen_elements = yongshen_elements.copy()

    # 更新 yongshen_detail，明确 base/final
    yong["base_yongshen_elements"] = base_yongshen_elements
    yong["final_yongshen_elements"] = final_yongshen_elements
    # 保留旧的 yongshen_elements 字段以兼容（但建议使用 base_yongshen_elements）
    # yong["yongshen_elements"] 现在等于 base_yongshen_elements

    # 用神十神解释 + 落点字清单（供前端与 CLI 使用）
    # 统一按“最终用神”（包含特殊规则补充）来做 explain，避免顶层 vs explain 不一致
    yong_explain = _compute_yongshen_explain(bazi, day_gan, final_yongshen_elements)

    return {
        "bazi": bazi,
        "day_master_element": day_master_element,
        "strength_percent": strength["strength_percent"],
        "strength_score_raw": strength["strength_score_raw"],
        "support_percent": strength["support_percent"],
        "drain_percent": strength["drain_percent"],
        "global_element_percentages": global_dist,
        "yongshen_elements": final_yongshen_elements,  # 顶层 = final_yongshen_elements
        "yongshen_detail": yong,
        "yongshen_shishen": yong_explain["yongshen_shishen"],
        "yongshen_tokens": yong_explain["yongshen_tokens"],
        "shishen_category_percentages": shishen_cat,
        "stem_pattern_summary": stem_patterns,
        "dominant_traits": dominant_traits,
        "natal_patterns": natal_patterns,
        "natal_conflicts": natal_conflicts,
        "natal_harmonies": natal_harmonies,
        "special_rules": special_rules,
    }


# ==== 大运 / 流年示例封装（后续可以扩展用在你的权重模型里） ====


@dataclass
class DaYunInfo:
    index: int
    start_year: int
    start_age: int
    gan_zhi: str


@dataclass
class LiuNianInfo:
    year: int
    age: int
    gan_zhi: str


def get_yun_info(birth_dt: datetime, is_male: bool) -> Dict[str, Any]:
    """示范如何从 lunar_python 里取大运 / 流年信息。

    当前只返回：
    - 起运时间（相对出生多久起运）
    - 前若干步大运的起运年、起运年龄、干支
    - 第一步大运下的所有流年干支

    后续你可以基于这些结构增加自己的评分逻辑。
    """
    solar = Solar(birth_dt.year, birth_dt.month, birth_dt.day,
                  birth_dt.hour, birth_dt.minute, birth_dt.second)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    # sex 参数：以 lunar 官方 demo 习惯，1=男, 0=女
    yun = ec.getYun(1 if is_male else 0)

    start_year = yun.getStartYear()
    start_month = yun.getStartMonth()
    start_day = yun.getStartDay()
    start_solar = yun.getStartSolar().toYmd()

    da_yun_arr = yun.getDaYun()
    da_yun_list: List[DaYunInfo] = []
    for i, da_yun in enumerate(da_yun_arr):
        da_yun_list.append(
            DaYunInfo(
                index=i,
                start_year=da_yun.getStartYear(),
                start_age=da_yun.getStartAge(),
                gan_zhi=da_yun.getGanZhi(),
            )
        )

    liu_nian_list: List[LiuNianInfo] = []
    if da_yun_arr:
        first_da_yun = da_yun_arr[0]
        liu_nian_arr = first_da_yun.getLiuNian()
        for ln in liu_nian_arr:
            liu_nian_list.append(
                LiuNianInfo(
                    year=ln.getYear(),
                    age=ln.getAge(),
                    gan_zhi=ln.getGanZhi(),
                )
            )

    return {
        "start_offset": {
            "years": start_year,
            "months": start_month,
            "days": start_day,
            "start_solar": start_solar,
        },
        "dayun": [asdict(x) for x in da_yun_list],
        "liunian_first_dayun": [asdict(x) for x in liu_nian_list],
    }


def analyze_complete(
    birth_dt: datetime,
    is_male: bool,
    max_dayun: int = 8,
) -> Dict[str, Any]:
    """完整分析：整合 analyze_basic() + analyze_luck() + 数据丰富化。
    
    这是新的主入口函数，返回包含所有结构化数据的完整结果对象。
    
    参数:
        birth_dt: 出生日期时间
        is_male: 是否男性
        max_dayun: 最大大运数量（默认8步）
        
    返回:
        完整的分析结果字典，包含：
        - schema_version: 数据格式版本号
        - natal: 原局数据（包含新增字段）
        - luck: 大运/流年数据（包含新增字段）
        - turning_points: 大运转折点列表
    """
    from .luck import analyze_luck
    from .enrich import (
        enrich_natal,
        enrich_dayun,
        enrich_liunian,
        compute_turning_points,
    )
    
    # 1. 基础分析
    natal = analyze_basic(birth_dt)
    bazi = natal["bazi"]
    day_gan = bazi["day"]["gan"]
    yongshen_elements = natal["yongshen_elements"]
    
    # 2. 大运/流年分析
    luck = analyze_luck(birth_dt, is_male, yongshen_elements, max_dayun=max_dayun)
    
    # 3. 丰富原局数据
    natal_enriched = enrich_natal(natal, bazi, day_gan, is_male)
    natal.update(natal_enriched)
    
    # 4. 丰富大运和流年数据
    strength_percent = natal.get("strength_percent", 50.0)
    support_percent = natal.get("support_percent", 0.0)
    
    for group in luck.get("groups", []):
        # 丰富大运数据
        dayun = group.get("dayun", {})
        dayun_enriched = enrich_dayun(
            dayun=dayun,
            bazi=bazi,
            day_gan=day_gan,
            strength_percent=strength_percent,
            support_percent=support_percent,
            yongshen_elements=yongshen_elements,
        )
        dayun.update(dayun_enriched)
        
        # 丰富流年数据
        liunian_list = group.get("liunian", [])
        dayun_gan = dayun.get("gan", "")
        for liunian in liunian_list:
            liunian_enriched = enrich_liunian(
                liunian=liunian,
                bazi=bazi,
                day_gan=day_gan,
                is_male=is_male,
                dayun_gan=dayun_gan,
            )
            liunian.update(liunian_enriched)
    
    # 5. 计算转折点
    turning_points = compute_turning_points(luck.get("groups", []))
    
    # 6. 组装最终结果
    return {
        "schema_version": "1.0.0",  # 数据格式版本号
        "natal": natal,
        "luck": luck,
        "turning_points": turning_points,
    }
