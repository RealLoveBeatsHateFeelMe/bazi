# -*- coding: utf-8 -*-
"""大运 / 流年排盘 + 好运 / 坏运 + 冲信息（命局冲 & 运年相冲）。"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from lunar_python import Solar  # 依赖：pip install lunar_python

from .config import GAN_WUXING, ZHI_WUXING, ZHI_CHONG, POSITION_WEIGHTS
from .clash import detect_branch_clash
from .shishen import get_branch_shishen
from .harmony import detect_flow_harmonies
from .punishment import detect_branch_punishments
from .patterns import detect_liunian_patterns


def _split_ganzhi(gz: str) -> Tuple[Optional[str], Optional[str]]:
    """把 '癸亥' 拆成 ('癸','亥')。

    注意：lunar_python 有些大运/流年会返回空字符串 ''，
    代表“还没起运前的阶段”之类，这里直接返回 (None, None)，上层跳过。
    """
    if gz is None:
        return None, None
    s = str(gz).strip()
    if not s:
        return None, None
    if len(s) < 2:
        raise ValueError(f"不合法的干支: {gz!r}")
    return s[0], s[1]


def _get_active_pillar(age: int) -> str:
    """根据虚龄确定线运对应的宫位（active_pillar）。"""
    if age <= 16:
        return "year"
    elif age <= 32:
        return "month"
    elif age <= 48:
        return "day"
    else:
        return "hour"


def _compute_lineyun_bonus(
    age: int,
    base_events: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """计算线运加成。

    规则：
    - 根据 age 确定 active_pillar
    - 扫描所有 role="base" 的事件
    - 判定触发：存在至少一条 base 事件满足：
      1. 该事件命中 active_pillar（targets 里有 pillar==active_pillar）
      2. 且该事件 risk_percent >= 10.0
    - 触发后：lineyun_bonus = 6.0（全年最多一次）

    返回：
    {
      "type": "lineyun_bonus",
      "role": "lineyun",
      "risk_percent": 6.0,
      "active_pillar": "year"/"month"/"day"/"hour",
      "trigger_events": [<触发来源事件的简化引用>]
    }
    或 None（未触发）
    """
    active_pillar = _get_active_pillar(age)
    trigger_events: List[Dict[str, Any]] = []

    for ev in base_events:
        if ev.get("role") != "base":
            continue

        # 检查事件 risk_percent
        risk_percent = ev.get("risk_percent", 0.0)
        if risk_percent < 10.0:
            continue

        # 检查是否命中 active_pillar
        targets = ev.get("targets", [])
        for target in targets:
            if target.get("pillar") == active_pillar:
                # 触发条件满足
                trigger_events.append({
                    "type": ev.get("type"),
                    "flow_year": ev.get("flow_year"),
                    "flow_label": ev.get("flow_label"),
                    "target_pillar": active_pillar,
                    "risk_percent": risk_percent,
                })
                # 只要有一条满足就触发，全年只加一次
                return {
                    "type": "lineyun_bonus",
                    "role": "lineyun",
                    "risk_percent": 6.0,
                    "active_pillar": active_pillar,
                    "trigger_events": trigger_events,
                }

    return None


def calc_first_half_label(risk_from_gan: float, is_gan_yongshen: bool) -> str:
    """根据流年天干风险和是否用神，计算上半年标签。
    
    规则（§6.3）：
    - 天干是用神时：
      - risk_from_gan <= 15% → "好运"
      - 15% < risk_from_gan <= 30% → "好坏都有"
      - risk_from_gan > 30% → "坏运"
    - 天干不是用神时：
      - risk_from_gan <= 15% → "一般"
      - 15% < risk_from_gan <= 30% → "一般（有变动）"
      - risk_from_gan > 30% → "坏运"
    """
    if is_gan_yongshen:
        if risk_from_gan <= 15.0:
            return "好运"
        elif risk_from_gan <= 30.0:
            return "好坏都有"
        else:
            return "坏运"
    else:
        if risk_from_gan <= 15.0:
            return "一般"
        elif risk_from_gan <= 30.0:
            return "一般（有变动）"
        else:
            return "坏运"


def calc_second_half_label(risk_from_zhi: float, is_zhi_yongshen: bool) -> str:
    """根据流年地支风险和是否用神，计算下半年标签。
    
    规则（§6.4）：
    - 地支是用神时：
      - risk_from_zhi <= 15% → "好运"
      - 15% < risk_from_zhi <= 30% → "好坏都有"
      - risk_from_zhi > 30% → "坏运"
    - 地支不是用神时：
      - risk_from_zhi <= 15% → "一般"
      - 15% < risk_from_zhi <= 30% → "一般（有变动）"
      - risk_from_zhi > 30% → "坏运"
    """
    if is_zhi_yongshen:
        if risk_from_zhi <= 15.0:
            return "好运"
        elif risk_from_zhi <= 30.0:
            return "好坏都有"
        else:
            return "坏运"
    else:
        if risk_from_zhi <= 15.0:
            return "一般"
        elif risk_from_zhi <= 30.0:
            return "一般（有变动）"
        else:
            return "坏运"


def calc_year_label(first_half_label: str, second_half_label: str) -> str:
    """根据上半年和下半年标签，计算年度整体标签。
    
    规则（§6.5）：
    - 如果 first_half_label == "好运" 且 second_half_label == "好运" → "好运"
    - 如果 first_half_label == "坏运" 且 second_half_label == "坏运" → "坏运"
    - 其他所有组合 → "一般/混合"
    """
    if first_half_label == "好运" and second_half_label == "好运":
        return "好运"
    elif first_half_label == "坏运" and second_half_label == "坏运":
        return "坏运"
    else:
        return "一般/混合"


def calc_year_label_old(total_risk_percent: float) -> str:
    """根据全年 total_risk_percent 计算年度整体标签 year_label。

    仅影响 year_label，不改动 ledger / total / core 等内部计算：
    - total <= 15        → 档 1 文案（例如：平稳 / 低风险）；
    - 15 < total <= 30   → 档 2 文案（例如：有一定波动）；
    - 30 < total <= 60   → 档 3 文案（沿用当前“30 以上”的文案）；
    - total > 60         → "极高风险"。

    具体文案由上层在映射 year_label → 展示文案时决定，这里只负责分档名称：
    - "low"           ：<=15
    - "medium"        ：(15, 30]
    - "high"          ：(30, 60]
    - "极高风险"       ：>60
    """
    if total_risk_percent <= 15.0:
        return "low"
    if total_risk_percent <= 30.0:
        return "medium"
    if total_risk_percent <= 60.0:
        return "high"
    return "极高风险"


@dataclass
class DayunLuck:
    index: int           # 第几步大运（0 开始）
    gan: str
    zhi: str
    gan_element: Optional[str]
    zhi_element: Optional[str]
    start_year: int      # 起运年份（阳历）
    start_age: int       # 起运年龄（虚龄）
    gan_good: bool       # 天干是否用神
    zhi_good: bool       # 地支是否用神
    is_good: bool        # 这步大运总体算 好运(True) / 坏运(False)
    clashes_natal: List[Dict[str, Any]] = field(default_factory=list)  # 大运支 与 命局地支的冲


@dataclass
class LiunianLuck:
    year: int            # 公历年份
    age: int             # 当年虚龄
    gan: str
    zhi: str
    gan_element: Optional[str]
    zhi_element: Optional[str]
    first_half_good: bool   # 上半年（年干）是否用神 → 好运/坏运
    second_half_good: bool  # 下半年（年支）是否用神 → 好运/坏运
    clashes_natal: List[Dict[str, Any]] = field(default_factory=list)   # 流年支 与 命局地支的冲
    clashes_dayun: List[Dict[str, Any]] = field(default_factory=list)   # 流年支 与 所在大运支的冲


def analyze_luck(
    birth_dt: datetime,
    is_male: bool,
    yongshen_elements: List[str],
    max_dayun: int = 8,
) -> Dict[str, Any]:
    """综合分析大运 / 流年：好运 / 坏运 + 冲的信息。

    当前版本仅实现：
    - 用神标记：大运/流年的干支是否落在 `yongshen_elements` 中；
    - 冲信息：大运支 / 流年支 与命局地支的冲，以及大运支 ↔ 流年支 的简单相冲事件。

    返回结构按大运分组：
    {
      "groups": [
        {
          "dayun": {...DayunLuck...},
          "liunian": [{...LiunianLuck...}, ...]   # 该大运下的十年
        },
        ...
      ]
    }
    """

    solar = Solar(birth_dt.year, birth_dt.month, birth_dt.day,
                  birth_dt.hour, birth_dt.minute, birth_dt.second)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    # 本命四柱（供地支冲识别用）
    bazi = {
        "year":  {"gan": ec.getYearGan(),  "zhi": ec.getYearZhi()},
        "month": {"gan": ec.getMonthGan(), "zhi": ec.getMonthZhi()},
        "day":   {"gan": ec.getDayGan(),   "zhi": ec.getDayZhi()},
        "hour":  {"gan": ec.getTimeGan(),  "zhi": ec.getTimeZhi()},
    }
    
    day_gan = bazi["day"]["gan"]  # 用于模式检测

    # sex 参数：以 lunar 官方 demo 习惯，1=男, 0=女
    yun = ec.getYun(1 if is_male else 0)
    dayun_objs = yun.getDaYun()

    groups: List[Dict[str, Any]] = []

    for idx, dy in enumerate(dayun_objs[:max_dayun]):
        # ===== 当前这一步大运 =====
        gz_dy = dy.getGanZhi()
        gan_dy, zhi_dy = _split_ganzhi(gz_dy)
        if gan_dy is None or zhi_dy is None:
            continue

        gan_el_dy = GAN_WUXING.get(gan_dy)
        zhi_el_dy = ZHI_WUXING.get(zhi_dy)

        gan_good_dy = bool(gan_el_dy and gan_el_dy in yongshen_elements)
        zhi_good_dy = bool(zhi_el_dy and zhi_el_dy in yongshen_elements)

        # 你的规则：以地支为主判断好运/坏运
        if zhi_good_dy and (not gan_good_dy):
            is_good_dy = True
        elif gan_good_dy and (not zhi_good_dy):
            is_good_dy = False
        elif zhi_good_dy and gan_good_dy:
            is_good_dy = True
        else:
            is_good_dy = False

        # 大运支 与 命局地支 的冲
        clash_dy_natal = detect_branch_clash(
            bazi=bazi,
            flow_branch=zhi_dy,
            flow_type="dayun",
            flow_year=dy.getStartYear(),
            flow_label=gz_dy,
            flow_gan=gan_dy,  # 传入天干用于天克地冲检测
        )

        # 大运支与原局的六合/三合（只解释，不计分）
        harmonies_dy = detect_flow_harmonies(
            bazi=bazi,
            flow_branch=zhi_dy,
            flow_type="dayun",
            flow_year=dy.getStartYear(),
            flow_label=gz_dy,
        )

        dayun_luck = DayunLuck(
            index=idx,
            gan=gan_dy,
            zhi=zhi_dy,
            gan_element=gan_el_dy,
            zhi_element=zhi_el_dy,
            start_year=dy.getStartYear(),
            start_age=dy.getStartAge(),
            gan_good=gan_good_dy,
            zhi_good=zhi_good_dy,
            is_good=is_good_dy,
            clashes_natal=[clash_dy_natal] if clash_dy_natal else [],
        )

        # ===== 这个大运下面的十个流年 =====
        liunian_list: List[LiunianLuck] = []
        liu_arr = dy.getLiuNian()

        for ln in liu_arr:
            gz_ln = ln.getGanZhi()
            gan_ln, zhi_ln = _split_ganzhi(gz_ln)
            if gan_ln is None or zhi_ln is None:
                continue

            gan_el_ln = GAN_WUXING.get(gan_ln)
            zhi_el_ln = ZHI_WUXING.get(zhi_ln)

            gan_good_ln = bool(gan_el_ln and gan_el_ln in yongshen_elements)
            zhi_good_ln = bool(zhi_el_ln and zhi_el_ln in yongshen_elements)

            # 流年：天干管上半年，地支管下半年
            first_half_good = gan_good_ln
            second_half_good = zhi_good_ln

            # 流年支 与 命局地支 的冲
            clash_ln_natal = detect_branch_clash(
                bazi=bazi,
                flow_branch=zhi_ln,
                flow_type="liunian",
                flow_year=ln.getYear(),
                flow_label=gz_ln,
                flow_gan=gan_ln,  # 传入天干用于天克地冲检测
            )
            
            # 流年支 与 命局地支 的刑
            punishments_ln = detect_branch_punishments(
                bazi=bazi,
                flow_branch=zhi_ln,
                flow_type="liunian",
                flow_year=ln.getYear(),
                flow_label=gz_ln,
            )

            # 大运支 与 流年支 之间的冲（不牵涉宫位，但要标清楚是什么十神在冲）
            clashes_dayun: List[Dict[str, Any]] = []
            if ZHI_CHONG.get(zhi_ln) == zhi_dy:
                clashes_dayun.append(
                    {
                        "type": "dayun_liunian_branch_clash",
                        "dayun_branch": zhi_dy,
                        "liunian_branch": zhi_ln,
                        "dayun_shishen": get_branch_shishen(bazi, zhi_dy),
                        "liunian_shishen": get_branch_shishen(bazi, zhi_ln),
                    }
                )

            # 流年支与原局的六合/三合（只解释，不计分）
            harmonies_ln = detect_flow_harmonies(
                bazi=bazi,
                flow_branch=zhi_ln,
                flow_type="liunian",
                flow_year=ln.getYear(),
                flow_label=gz_ln,
            )

            # ===== §5.3.3 流年模式检测 =====
            pattern_events_ln = detect_liunian_patterns(
                bazi=bazi,
                day_gan=day_gan,
                dayun_gan=gan_dy,
                dayun_zhi=zhi_dy,
                liunian_gan=gan_ln,
                liunian_zhi=zhi_ln,
            )
            
            # 为模式事件添加 flow_year 和 flow_label
            for pat_ev in pattern_events_ln:
                pat_ev["flow_year"] = ln.getYear()
                pat_ev["flow_label"] = gz_ln

            # ===== §6.2 检查模式是否与冲事件重叠 =====
            # 如果同一对地支既是冲又是模式，在冲上+10%，不单独计模式
            pattern_events_filtered: List[Dict[str, Any]] = []
            clash_pattern_bonus = 0.0  # 冲+模式的额外加成
            
            if clash_ln_natal:
                clash_target_branch = clash_ln_natal.get("target_branch")
                clash_flow_branch = clash_ln_natal.get("flow_branch")
                
                for pat_ev in pattern_events_ln:
                    # 只检查地支层模式（天干层模式不会与地支冲重叠）
                    if pat_ev.get("kind") != "zhi":
                        pattern_events_filtered.append(pat_ev)
                        continue
                    
                    # 检查模式的两个位置是否与冲的一对地支匹配
                    pos1 = pat_ev.get("pos1", {})
                    pos2 = pat_ev.get("pos2", {})
                    
                    # 流年地支应该等于 clash_flow_branch
                    # 另一个位置应该是命局中的 clash_target_branch
                    liunian_char = pos1.get("char") if pos1.get("source") == "liunian" else pos2.get("char")
                    other_char = pos2.get("char") if pos1.get("source") == "liunian" else pos1.get("char")
                    other_pillar = pos2.get("pillar") if pos1.get("source") == "liunian" else pos1.get("pillar")
                    
                    if (liunian_char == clash_flow_branch and 
                        other_char == clash_target_branch and
                        other_pillar in ("year", "month", "day", "hour")):
                        # 重叠！在冲上+10%，不单独计模式
                        clash_pattern_bonus = 10.0
                        # 更新冲事件的风险
                        old_risk = clash_ln_natal.get("risk_percent", 0.0)
                        clash_ln_natal["risk_percent"] = old_risk + clash_pattern_bonus
                        clash_ln_natal["pattern_bonus_percent"] = clash_pattern_bonus
                        clash_ln_natal["is_pattern_overlap"] = True
                        clash_ln_natal["overlap_pattern_type"] = pat_ev.get("pattern_type")
                    else:
                        pattern_events_filtered.append(pat_ev)
            else:
                pattern_events_filtered = pattern_events_ln

            # 收集基础事件（用于线运计算）
            base_events: List[Dict[str, Any]] = []
            if clash_ln_natal:
                base_events.append(clash_ln_natal)
            # 刑事件也是基础事件
            for punish_ev in punishments_ln:
                # 过滤掉既冲又刑的情况（按规则只算冲）
                if clash_ln_natal:
                    # 检查是否与冲事件重叠（同一对地支）
                    clash_target = clash_ln_natal.get("target_branch")
                    if punish_ev.get("target_branch") == clash_target:
                        continue  # 跳过，只算冲
                base_events.append(punish_ev)
            # 模式事件也是基础事件（已过滤掉与冲重叠的）
            base_events.extend(pattern_events_filtered)

            # 计算线运加成
            lineyun_event = _compute_lineyun_bonus(ln.getAge(), base_events)
            lineyun_bonus = lineyun_event.get("risk_percent", 0.0) if lineyun_event else 0.0

            # ===== §6.1 风险拆分：天干算天干的，地支算地支的 =====
            # risk_from_zhi：流年地支引起的风险
            risk_from_zhi = 0.0
            if clash_ln_natal:
                # 冲的风险全部计入 risk_from_zhi（包括基础冲、墓库加成、天克地冲、模式重叠+10%等）
                risk_from_zhi += clash_ln_natal.get("risk_percent", 0.0)
            # 刑的风险全部计入 risk_from_zhi
            for punish_ev in punishments_ln:
                # 过滤掉既冲又刑的情况
                if clash_ln_natal:
                    clash_target = clash_ln_natal.get("target_branch")
                    if punish_ev.get("target_branch") == clash_target:
                        continue
                risk_from_zhi += punish_ev.get("risk_percent", 0.0)
            # 地支层模式风险计入 risk_from_zhi（不包括与冲重叠的，因为已经加到冲上了）
            for pat_ev in pattern_events_filtered:
                if pat_ev.get("kind") == "zhi":
                    risk_from_zhi += pat_ev.get("risk_percent", 0.0)
            # 线运加成：如果线运事件命中的是地支侧（冲/刑），则加到 risk_from_zhi
            # 目前线运只基于 base_events（冲和刑都是地支侧），所以线运加成加到 risk_from_zhi
            if lineyun_event:
                risk_from_zhi += lineyun_bonus

            # risk_from_gan：流年天干引起的风险
            risk_from_gan = 0.0
            # 天干层模式风险计入 risk_from_gan
            for pat_ev in pattern_events_filtered:
                if pat_ev.get("kind") == "gan":
                    risk_from_gan += pat_ev.get("risk_percent", 0.0)

            # 年度总风险 = risk_from_gan + risk_from_zhi（不封顶，可>100）
            total_risk_percent = risk_from_gan + risk_from_zhi

            # ===== §6.3-6.5 计算上半年/下半年/年度标签 =====
            first_half_label = calc_first_half_label(risk_from_gan, gan_good_ln)
            second_half_label = calc_second_half_label(risk_from_zhi, zhi_good_ln)
            year_label = calc_year_label(first_half_label, second_half_label)

            # 构建年度事件列表
            all_events: List[Dict[str, Any]] = []
            if clash_ln_natal:
                all_events.append(clash_ln_natal)
            # 添加刑事件（过滤掉既冲又刑的情况）
            for punish_ev in punishments_ln:
                if clash_ln_natal:
                    clash_target = clash_ln_natal.get("target_branch")
                    if punish_ev.get("target_branch") == clash_target:
                        continue
                all_events.append(punish_ev)
            # 添加模式事件（已过滤掉与冲重叠的）
            all_events.extend(pattern_events_filtered)
            if lineyun_event:
                all_events.append(lineyun_event)

            liunian_dict = {
                "year": ln.getYear(),
                "age": ln.getAge(),
                "gan": gan_ln,
                "zhi": zhi_ln,
                "gan_element": gan_el_ln,
                "zhi_element": zhi_el_ln,
                "first_half_good": first_half_good,  # 保留兼容字段（是否用神）
                "second_half_good": second_half_good,  # 保留兼容字段（是否用神）
                "risk_from_gan": risk_from_gan,  # §6.1 天干引起的风险
                "risk_from_zhi": risk_from_zhi,  # §6.1 地支引起的风险
                "first_half_label": first_half_label,  # §6.3 上半年标签（好运/一般/坏运等）
                "second_half_label": second_half_label,  # §6.4 下半年标签（好运/一般/坏运等）
                "year_label": year_label,  # §6.5 年度整体标签（好运/坏运/一般/混合）
                "clashes_natal": [clash_ln_natal] if clash_ln_natal else [],
                "clashes_dayun": clashes_dayun,
                "punishments_natal": punishments_ln,  # 流年支 与 命局地支 的刑
                "patterns_liunian": pattern_events_filtered,  # 流年模式事件（已过滤掉与冲重叠的）
                "harmonies_natal": harmonies_ln,  # 流年与原局的六合/三合/半合/三会（只解释，不计分）
                "harmonies_dayun": [],  # 流年与大运的合类（目前为空，后续可扩展）
                "lineyun_bonus": lineyun_bonus,
                "total_risk_percent": total_risk_percent,
                "all_events": all_events,
            }

            liunian_list.append(liunian_dict)

        # 一个大运 + 对应的十个流年
        dayun_dict = asdict(dayun_luck)
        dayun_dict["harmonies_natal"] = harmonies_dy  # 大运与原局的六合/三合/半合/三会（只解释，不计分）

        groups.append(
            {
                "dayun": dayun_dict,
                "liunian": liunian_list,  # 已经是 dict，不需要 asdict
            }
        )

    # 按大运起运年份排序（保险起见）
    groups.sort(key=lambda g: g["dayun"]["start_year"])

    return {"groups": groups}
