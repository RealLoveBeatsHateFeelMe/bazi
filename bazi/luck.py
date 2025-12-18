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
    static_activation_events: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """计算线运加成（§11.3：天干侧和地支侧分开计算，考虑静态影响）。

    规则：
    - 根据 age 确定 active_pillar
    - 分别扫描天干侧和地支侧的事件
    - 对于每个侧别，计算命中 active_pillar 的所有事件的风险总和（包括动态和静态）
    - 如果单柱的总风险（动态+静态）>= 10.0，才触发该侧别的线运加成 +6%
    - 如果同一根柱既有天干侧事件又有地支侧事件，可能分别获得天干侧和地支侧的线运加成（各+6%）

    返回：
    {
      "type": "lineyun_bonus",
      "role": "lineyun",
      "risk_percent": 6.0 | 12.0,  # 天干侧+地支侧的总加成
      "lineyun_bonus_gan": 6.0 | 0.0,  # 天干侧加成
      "lineyun_bonus_zhi": 6.0 | 0.0,  # 地支侧加成
      "active_pillar": "year"/"month"/"day"/"hour",
      "trigger_events_gan": [...],  # 天干侧触发事件
      "trigger_events_zhi": [...],  # 地支侧触发事件
    }
    或 None（未触发）
    """
    if static_activation_events is None:
        static_activation_events = []
    
    active_pillar = _get_active_pillar(age)
    trigger_events_gan: List[Dict[str, Any]] = []
    trigger_events_zhi: List[Dict[str, Any]] = []
    
    # 计算命中 active_pillar 的天干侧和地支侧风险总和
    total_risk_gan = 0.0
    total_risk_zhi = 0.0
    
    # 扫描基础事件（动态事件）
    for ev in base_events:
        if ev.get("role") != "base":
            continue

        # 判断事件是天干侧还是地支侧
        event_type = ev.get("type", "")
        kind = ev.get("kind")  # 模式事件有 kind 字段
        
        is_gan_side = False
        is_zhi_side = False
        
        if event_type == "pattern":
            # 模式事件：根据 kind 判断
            if kind == "gan":
                is_gan_side = True
            elif kind == "zhi":
                is_zhi_side = True
        elif event_type in ("branch_clash", "punishment", "dayun_liunian_branch_clash"):
            # 冲和刑都是地支侧
            is_zhi_side = True
        # 其他事件类型默认为地支侧（保守处理）
        else:
            is_zhi_side = True

        # 检查是否命中 active_pillar
        hit_active = False
        
        # 对于有targets字段的事件（如冲、刑），检查targets
        targets = ev.get("targets", [])
        if targets:
            for target in targets:
                if target.get("pillar") == active_pillar:
                    hit_active = True
                    break
        else:
            # 对于模式事件，检查pos1和pos2中的pillar
            pos1 = ev.get("pos1", {})
            pos2 = ev.get("pos2", {})
            if pos1.get("pillar") == active_pillar or pos2.get("pillar") == active_pillar:
                hit_active = True
        
        if not hit_active:
            continue

        # 累加风险
        risk_percent = ev.get("risk_percent", 0.0)
        if is_gan_side:
            total_risk_gan += risk_percent
        elif is_zhi_side:
            total_risk_zhi += risk_percent
    
    # 扫描静态激活事件（线运不算静态激活的风险）
    # 根据用户要求：线运以后不算静态的危险系数，因为静态危险系数没法归类到哪一柱
    # 所以这里不再扫描静态激活事件
    
    # 判断是否触发线运加成（单柱总风险 >= 10.0）
    lineyun_bonus_gan = 0.0
    lineyun_bonus_zhi = 0.0
    
    if total_risk_gan >= 10.0:
        lineyun_bonus_gan = 6.0
        trigger_events_gan.append({
            "type": "lineyun_trigger",
            "target_pillar": active_pillar,
            "total_risk_gan": total_risk_gan,
        })
    
    if total_risk_zhi >= 10.0:
        lineyun_bonus_zhi = 6.0
        trigger_events_zhi.append({
            "type": "lineyun_trigger",
            "target_pillar": active_pillar,
            "total_risk_zhi": total_risk_zhi,
        })

    # 如果没有任何加成，返回 None
    total_bonus = lineyun_bonus_gan + lineyun_bonus_zhi
    if total_bonus == 0.0:
        return None

    return {
        "type": "lineyun_bonus",
        "role": "lineyun",
        "risk_percent": total_bonus,  # 总加成（可能是 6.0 或 12.0）
        "lineyun_bonus_gan": lineyun_bonus_gan,  # 天干侧加成
        "lineyun_bonus_zhi": lineyun_bonus_zhi,  # 地支侧加成
        "active_pillar": active_pillar,
        "trigger_events_gan": trigger_events_gan,
        "trigger_events_zhi": trigger_events_zhi,
    }


# 已删除：calc_first_half_label, calc_second_half_label, calc_year_label, calc_year_label_old
# 这些函数用于计算上半年/下半年/年度标签，但用户要求删除天干地支分开的影响

def _deleted_calc_first_half_label(risk_from_gan: float, is_gan_yongshen: bool) -> str:
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


def _deleted_calc_second_half_label(risk_from_zhi: float, is_zhi_yongshen: bool) -> str:
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


def _deleted_calc_year_label(first_half_label: str, second_half_label: str) -> str:
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


def _deleted_calc_year_label_old(total_risk_percent: float) -> str:
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
    
    # 原局静态模式（用于 §9 静态模式激活检测）
    from .patterns import detect_natal_patterns
    natal_patterns = detect_natal_patterns(bazi, day_gan)

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

        # 旧规则（保留以兼容）：以地支为主判断好运/坏运
        # 新规则（§8）会在后面根据 risk_dayun_total 和用神情况计算 dayun_label
        if zhi_good_dy and (not gan_good_dy):
            is_good_dy_old = True
        elif gan_good_dy and (not zhi_good_dy):
            is_good_dy_old = False
        elif zhi_good_dy and gan_good_dy:
            is_good_dy_old = True
        else:
            is_good_dy_old = False

        # ===== §8.2 大运危险系数计算 =====
        # 大运支 与 命局地支 的冲
        clash_dy_natal = detect_branch_clash(
            bazi=bazi,
            flow_branch=zhi_dy,
            flow_type="dayun",
            flow_year=dy.getStartYear(),
            flow_label=gz_dy,
            flow_gan=gan_dy,  # 传入天干用于天克地冲检测
        )
        
        # 大运支 与 命局地支 的刑
        punishments_dy = detect_branch_punishments(
            bazi=bazi,
            flow_branch=zhi_dy,
            flow_type="dayun",
            flow_year=dy.getStartYear(),
            flow_label=gz_dy,
        )
        
        # 过滤掉既冲又刑的情况（按规则只算冲）
        punishments_dy_filtered: List[Dict[str, Any]] = []
        if clash_dy_natal:
            clash_target = clash_dy_natal.get("target_branch")
            for punish_ev in punishments_dy:
                if punish_ev.get("target_branch") != clash_target:
                    punishments_dy_filtered.append(punish_ev)
        else:
            punishments_dy_filtered = punishments_dy
        
        # 大运干/支 与 命局干/支 的模式（静态，用于展示和风险计算）
        from .patterns import detect_dayun_patterns
        dayun_patterns = detect_dayun_patterns(bazi, day_gan, gan_dy, zhi_dy)
        
        # 计算大运模式事件的风险（只计算大运 vs 命局的结构性模式）
        # 注意：这里需要检测大运干/支与命局干/支的模式，但不包括流年
        # 由于 detect_dayun_patterns 只返回静态模式列表，我们需要计算风险
        # 实际上，大运层的模式是静态的，不直接计分，但我们需要检测是否有模式重叠在冲上
        
        # 检查大运模式是否与冲重叠（类似流年的逻辑）
        dayun_pattern_events: List[Dict[str, Any]] = []
        clash_pattern_bonus_dy = 0.0
        
        # 遍历大运模式，检查是否有地支层模式与冲重叠
        for pattern_group in dayun_patterns:
            pattern_type = pattern_group.get("pattern_type")
            pairs = pattern_group.get("pairs", [])
            for pair in pairs:
                pos1 = pair.get("pos1", {})
                pos2 = pair.get("pos2", {})
                kind = pos1.get("kind")
                
                # 只处理地支层模式（天干层模式单独计算）
                if kind == "zhi" and clash_dy_natal:
                    clash_target_branch = clash_dy_natal.get("target_branch")
                    clash_flow_branch = clash_dy_natal.get("flow_branch")
                    
                    # 检查是否与冲重叠
                    dayun_char = pos1.get("char") if pos1.get("source") == "dayun" else pos2.get("char")
                    other_char = pos2.get("char") if pos1.get("source") == "dayun" else pos1.get("char")
                    other_pillar = pos2.get("pillar") if pos1.get("source") == "dayun" else pos1.get("pillar")
                    
                    if (dayun_char == clash_flow_branch and 
                        other_char == clash_target_branch and
                        other_pillar in ("year", "month", "day", "hour")):
                        # 重叠！在冲上+10%
                        clash_pattern_bonus_dy = 10.0
                        old_risk = clash_dy_natal.get("risk_percent", 0.0)
                        clash_dy_natal["risk_percent"] = old_risk + clash_pattern_bonus_dy
                        clash_dy_natal["pattern_bonus_percent"] = clash_pattern_bonus_dy
                        clash_dy_natal["is_pattern_overlap"] = True
                        clash_dy_natal["overlap_pattern_type"] = pattern_type
                    else:
                        # 不重叠，单独计算模式风险
                        risk = 15.0
                        # 如果涉及命局月支，则风险为25%
                        other_pos = pos2 if pos1.get("source") == "dayun" else pos1
                        if (other_pos.get("source") == "natal" and 
                            other_pillar == "month" and 
                            other_pos.get("kind") == "zhi"):
                            risk = 25.0
                        dayun_pattern_events.append({
                            "type": "pattern",
                            "pattern_type": pattern_type,
                            "kind": "zhi",
                            "risk_percent": risk,
                            "pos1": pos1,
                            "pos2": pos2,
                        })
                elif kind == "gan":
                    # 天干层模式，单独计算
                    risk = 15.0
                    dayun_pattern_events.append({
                        "type": "pattern",
                        "pattern_type": pattern_type,
                        "kind": "gan",
                        "risk_percent": risk,
                        "pos1": pos1,
                        "pos2": pos2,
                    })
        
        # 计算 risk_dayun_zhi（大运地支参与的事件）
        risk_dayun_zhi = 0.0
        if clash_dy_natal:
            risk_dayun_zhi += clash_dy_natal.get("risk_percent", 0.0)
        for punish_ev in punishments_dy_filtered:
            risk_dayun_zhi += punish_ev.get("risk_percent", 0.0)
        for pat_ev in dayun_pattern_events:
            if pat_ev.get("kind") == "zhi":
                risk_dayun_zhi += pat_ev.get("risk_percent", 0.0)
        
        # 计算 risk_dayun_gan（大运天干参与的事件）
        risk_dayun_gan = 0.0
        for pat_ev in dayun_pattern_events:
            if pat_ev.get("kind") == "gan":
                risk_dayun_gan += pat_ev.get("risk_percent", 0.0)
        
        # 计算 risk_dayun_total
        risk_dayun_total = risk_dayun_zhi + risk_dayun_gan
        
        # ===== §8.4 大运好坏判定逻辑 =====
        is_dayun_zhi_yongshen = zhi_good_dy
        is_dayun_gan_yongshen = gan_good_dy
        
        if is_dayun_zhi_yongshen:
            if risk_dayun_total < 30.0:
                dayun_label = "好运"
            else:
                dayun_label = "坏运（用神过旺/变动过大）"
            
            # 检查是否"非常好运"
            is_very_good = False
            if is_dayun_zhi_yongshen and is_dayun_gan_yongshen and risk_dayun_total < 30.0:
                is_very_good = True
        else:
            if risk_dayun_total <= 15.0:
                dayun_label = "一般"
            elif risk_dayun_total <= 30.0:
                dayun_label = "一般（有变动）"
            else:
                dayun_label = "坏运"
            is_very_good = False

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
            is_good=is_good_dy_old,  # 保留旧字段以兼容（会在后面根据 §4.4 更新）
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

            # 大运支 与 流年支 之间的冲（需要计算风险）
            clash_dayun_liunian = None
            if ZHI_CHONG.get(zhi_ln) == zhi_dy:
                # 运年相冲：基础风险为 10%（固定值，不涉及宫位）
                base_risk = 10.0
                
                # 检查是否为墓库冲（辰戌、丑未）
                from .clash import _is_grave_clash
                is_grave_clash = _is_grave_clash(zhi_dy, zhi_ln)
                grave_bonus = 0.0
                if is_grave_clash:
                    # 墓库加成：+5%
                    grave_bonus = 5.0
                
                # 检测运年天克地冲（大运天干与流年天干互克，且地支互冲）
                from .clash import _check_tian_ke_di_chong
                tkdc_bonus = 0.0
                is_tkdc = False
                if _check_tian_ke_di_chong(gan_dy, zhi_dy, gan_ln, zhi_ln):
                    # 运年天克地冲：在天克地冲的基础上额外+10%
                    # 即：基础天克地冲+10%，运年天克地冲再+10%，总共+20%
                    tkdc_bonus = 20.0  # 10%（天克地冲）+ 10%（运年天克地冲额外）
                    is_tkdc = True
                
                total_risk = base_risk + grave_bonus + tkdc_bonus
                
                clash_dayun_liunian = {
                    "type": "dayun_liunian_branch_clash",
                    "role": "base",  # 标记为基础事件，用于线运计算
                    "dayun_branch": zhi_dy,
                    "liunian_branch": zhi_ln,
                    "dayun_gan": gan_dy,
                    "liunian_gan": gan_ln,
                    "dayun_shishen": get_branch_shishen(bazi, zhi_dy),
                    "liunian_shishen": get_branch_shishen(bazi, zhi_ln),
                    "base_risk_percent": base_risk,
                    "grave_bonus_percent": grave_bonus,
                    "tkdc_bonus_percent": tkdc_bonus,
                    "is_tian_ke_di_chong": is_tkdc,
                    "risk_percent": total_risk,
                    "flow_year": ln.getYear(),
                    "flow_label": gz_ln,
                    # 注意：运年相冲不涉及命局宫位，所以 targets 为空
                    "targets": [],
                }
            
            clashes_dayun: List[Dict[str, Any]] = [clash_dayun_liunian] if clash_dayun_liunian else []
            
            # ===== 静态冲/刑激活检测 =====
            # 当流年与命局相冲/刑时，如果大运与命局之间也有静态冲/刑（且涉及相同的命局地支），则静态冲/刑被激活
            static_clash_activation_risk = 0.0  # 静态冲的地支部分（base_power的一半）
            static_tkdc_activation_risk_zhi = 0.0  # 静态天克地冲的地支部分（tkdc的一半）
            static_tkdc_activation_risk_gan = 0.0  # 静态天克地冲的天干部分（天克的一半）
            static_punish_activation_risk = 0.0
            
            # 检查静态冲激活：有两种触发方式
            # 1. 流年地支与命局地支相冲，且大运与命局之间也有静态冲（涉及相同的命局地支）
            # 2. 流年地支与大运地支相冲，且大运与命局之间也有静态冲（激活大运静态冲）
            if clash_dy_natal:
                should_activate_clash = False
                
                # 情况1：流年与命局相冲，且涉及相同的命局地支
                if clash_ln_natal:
                    clash_ln_target = clash_ln_natal.get("target_branch")
                    clash_dy_target = clash_dy_natal.get("target_branch")
                    if clash_ln_target == clash_dy_target:
                        should_activate_clash = True
                
                # 情况2：流年与大运相冲，激活大运与命局之间的静态冲
                if clash_dayun_liunian:
                    should_activate_clash = True
                
                if should_activate_clash:
                    # 静态冲被激活：每个被冲的柱都算一半
                    # 根据用户说明：墓库冲的力量是15%每次（base_power 10% + grave_bonus 5%）
                    # 如果有两个柱，就是两次，激活时每个算一半，所以是 15% * 0.5 * 2 = 15%
                    targets = clash_dy_natal.get("targets", [])
                    base_power_percent = clash_dy_natal.get("base_power_percent", 0.0)
                    grave_bonus_percent = clash_dy_natal.get("grave_bonus_percent", 0.0)
                    
                    # 计算每个柱的完整风险（base_power + grave_bonus）
                    # base_power_percent 是所有柱的权重累加，需要按柱数分配
                    if len(targets) > 0:
                        # 每个柱的base_power（平均分配）
                        pillar_base_power = base_power_percent / len(targets)
                        # 每个柱的完整风险 = base_power + grave_bonus
                        pillar_full_risk = pillar_base_power + grave_bonus_percent
                        # 每个柱的激活风险 = 完整风险的一半
                        for target in targets:
                            static_clash_activation_risk += pillar_full_risk * 0.5
                    
                    # 静态天克地冲：如果大运静态冲有天克地冲，则静态天克地冲也被激活
                    static_tkdc_bonus = clash_dy_natal.get("tkdc_bonus_percent", 0.0)
                    if static_tkdc_bonus > 0.0:
                        static_tkdc_activation_risk_total = static_tkdc_bonus * 0.5
                        static_tkdc_activation_risk_zhi = static_tkdc_activation_risk_total
            
            # 检查静态刑激活：有三种触发方式
            # 1. 流年地支与命局地支相刑，且大运与命局之间也有静态刑（涉及相同的命局地支）
            # 2. 流年地支与大运地支相刑，且大运与命局之间也有静态刑（激活大运静态刑）
            # 3. 流年地支与命局地支相刑，且原局内部也有静态刑（激活原局内部静态刑）
            
            # 检测原局内部的静态刑
            from .punishment import detect_natal_clashes_and_punishments
            natal_static = detect_natal_clashes_and_punishments(bazi)
            natal_punishments = natal_static.get("punishments", [])
            
            should_activate_punish = False
            activated_punish_evs = []
            
            # 情况1：流年与命局相刑，且大运与命局之间也有静态刑（涉及相同的命局地支）
            if punishments_dy_filtered and punishments_ln:
                ln_punish_targets = {ev.get("target_branch") for ev in punishments_ln}
                for punish_ev in punishments_dy_filtered:
                    dy_punish_target = punish_ev.get("target_branch")
                    if dy_punish_target in ln_punish_targets:
                        should_activate_punish = True
                        activated_punish_evs.append(punish_ev)
            
            # 情况2：流年与大运相刑，激活大运与命局之间的静态刑
            if punishments_dy_filtered:
                from .punishment import _get_punish_targets
                liunian_punish_targets = _get_punish_targets(zhi_ln)
                if zhi_dy in liunian_punish_targets:
                    should_activate_punish = True
                    # 激活所有大运静态刑
                    for punish_ev in punishments_dy_filtered:
                        if punish_ev not in activated_punish_evs:
                            activated_punish_evs.append(punish_ev)
            
            # 情况3：流年与命局相刑，且原局内部也有静态刑（激活原局内部静态刑）
            if punishments_ln and natal_punishments:
                # 检查流年刑是否与原局内部刑相同
                ln_punish_pairs = {(ev.get("flow_branch"), ev.get("target_branch")) for ev in punishments_ln}
                for natal_punish_ev in natal_punishments:
                    # 原局内部刑的格式：flow_branch 和 target_branch 是原局的两个柱
                    natal_flow = natal_punish_ev.get("flow_branch")
                    natal_target = natal_punish_ev.get("target_branch")
                    # 检查是否与流年刑相同（流年地支与原局内部刑的其中一个地支相同）
                    if (zhi_ln == natal_flow and natal_target in {ev.get("target_branch") for ev in punishments_ln}) or \
                       (zhi_ln == natal_target and natal_flow in {ev.get("target_branch") for ev in punishments_ln}):
                        should_activate_punish = True
                        activated_punish_evs.append(natal_punish_ev)
            
            if should_activate_punish:
                # 静态刑被激活，风险为原风险的一半
                for punish_ev in activated_punish_evs:
                    static_punish_risk = punish_ev.get("risk_percent", 0.0) * 0.5
                    static_punish_activation_risk += static_punish_risk

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
            # 运年相冲也是基础事件
            if clash_dayun_liunian:
                base_events.append(clash_dayun_liunian)
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

            # ===== §9 静态模式被流年激活检测 =====
            from .config import PATTERN_GAN_RISK_STATIC, PATTERN_ZHI_RISK_STATIC
            
            # 按模式类型分组流年模式事件
            liunian_patterns_by_type: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
            for pat_ev in pattern_events_filtered:
                pattern_type = pat_ev.get("pattern_type")
                kind = pat_ev.get("kind")
                if pattern_type not in liunian_patterns_by_type:
                    liunian_patterns_by_type[pattern_type] = {"gan": [], "zhi": []}
                liunian_patterns_by_type[pattern_type][kind].append(pat_ev)
            
            # 按模式类型分组原局静态模式
            natal_patterns_by_type: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
            for pattern_group in natal_patterns:
                pattern_type = pattern_group.get("pattern_type")
                pairs = pattern_group.get("pairs", [])
                if pattern_type not in natal_patterns_by_type:
                    natal_patterns_by_type[pattern_type] = {"gan": [], "zhi": []}
                for pair in pairs:
                    pos1 = pair.get("pos1", {})
                    kind = pos1.get("kind")
                    natal_patterns_by_type[pattern_type][kind].append(pair)
            
            # 按模式类型分组大运静态模式
            dayun_patterns_by_type: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
            for pattern_group in dayun_patterns:
                pattern_type = pattern_group.get("pattern_type")
                pairs = pattern_group.get("pairs", [])
                if pattern_type not in dayun_patterns_by_type:
                    dayun_patterns_by_type[pattern_type] = {"gan": [], "zhi": []}
                for pair in pairs:
                    pos1 = pair.get("pos1", {})
                    kind = pos1.get("kind")
                    dayun_patterns_by_type[pattern_type][kind].append(pair)
            
            # 检测静态模式激活并计算风险
            static_activation_events: List[Dict[str, Any]] = []
            
            for pattern_type in ["hurt_officer", "pianyin_eatgod"]:
                liunian_gan_pairs = liunian_patterns_by_type.get(pattern_type, {}).get("gan", [])
                liunian_zhi_pairs = liunian_patterns_by_type.get(pattern_type, {}).get("zhi", [])
                natal_gan_pairs = natal_patterns_by_type.get(pattern_type, {}).get("gan", [])
                natal_zhi_pairs = natal_patterns_by_type.get(pattern_type, {}).get("zhi", [])
                dayun_gan_pairs = dayun_patterns_by_type.get(pattern_type, {}).get("gan", [])
                dayun_zhi_pairs = dayun_patterns_by_type.get(pattern_type, {}).get("zhi", [])
                
                # 天干层激活检测
                activated_natal_gan_pairs: List[Dict[str, Any]] = []
                activated_dayun_gan_pairs: List[Dict[str, Any]] = []
                
                if len(liunian_gan_pairs) > 0:
                    # 对每个流年天干 pair，检查是否激活静态 pair
                    for liunian_pair in liunian_gan_pairs:
                        liunian_chars = {liunian_pair["pos1"]["char"], liunian_pair["pos2"]["char"]}
                        
                        # 检查原局静态 pair
                        for natal_pair in natal_gan_pairs:
                            natal_chars = {natal_pair["pos1"]["char"], natal_pair["pos2"]["char"]}
                            if natal_chars == liunian_chars:
                                # 激活！只记录一次
                                if natal_pair not in activated_natal_gan_pairs:
                                    activated_natal_gan_pairs.append(natal_pair)
                        
                        # 检查大运静态 pair
                        for dayun_pair in dayun_gan_pairs:
                            dayun_chars = {dayun_pair["pos1"]["char"], dayun_pair["pos2"]["char"]}
                            if dayun_chars == liunian_chars:
                                # 激活！只记录一次
                                if dayun_pair not in activated_dayun_gan_pairs:
                                    activated_dayun_gan_pairs.append(dayun_pair)
                
                # 地支层激活检测
                activated_natal_zhi_pairs: List[Dict[str, Any]] = []
                activated_dayun_zhi_pairs: List[Dict[str, Any]] = []
                
                if len(liunian_zhi_pairs) > 0:
                    # 对每个流年地支 pair，检查是否激活静态 pair
                    for liunian_pair in liunian_zhi_pairs:
                        liunian_chars = {liunian_pair["pos1"]["char"], liunian_pair["pos2"]["char"]}
                        
                        # 检查原局静态 pair
                        for natal_pair in natal_zhi_pairs:
                            natal_chars = {natal_pair["pos1"]["char"], natal_pair["pos2"]["char"]}
                            if natal_chars == liunian_chars:
                                # 激活！只记录一次
                                if natal_pair not in activated_natal_zhi_pairs:
                                    activated_natal_zhi_pairs.append(natal_pair)
                        
                        # 检查大运静态 pair
                        for dayun_pair in dayun_zhi_pairs:
                            dayun_chars = {dayun_pair["pos1"]["char"], dayun_pair["pos2"]["char"]}
                            if dayun_chars == liunian_chars:
                                # 激活！只记录一次
                                if dayun_pair not in activated_dayun_zhi_pairs:
                                    activated_dayun_zhi_pairs.append(dayun_pair)
                
                # 计算静态激活风险（只加10%，不管是否涉及月支）
                static_risk_gan = PATTERN_GAN_RISK_STATIC * (len(activated_natal_gan_pairs) + len(activated_dayun_gan_pairs))
                static_risk_zhi = PATTERN_ZHI_RISK_STATIC * (len(activated_natal_zhi_pairs) + len(activated_dayun_zhi_pairs))
                
                # 如果有激活的静态模式，生成汇总事件
                if static_risk_gan > 0.0 or static_risk_zhi > 0.0:
                    static_activation_events.append({
                        "type": "pattern_static_activation",
                        "pattern_type": pattern_type,
                        "risk_percent": static_risk_gan + static_risk_zhi,
                        "risk_from_gan": static_risk_gan,
                        "risk_from_zhi": static_risk_zhi,
                        "activated_natal_gan_pairs": activated_natal_gan_pairs,
                        "activated_dayun_gan_pairs": activated_dayun_gan_pairs,
                        "activated_natal_zhi_pairs": activated_natal_zhi_pairs,
                        "activated_dayun_zhi_pairs": activated_dayun_zhi_pairs,
                        "liunian_pairs_trigger_gan": liunian_gan_pairs,
                        "liunian_pairs_trigger_zhi": liunian_zhi_pairs,
                        "flow_year": ln.getYear(),
                        "flow_label": gz_ln,
                    })

            # 计算线运加成（§11.3：天干侧和地支侧分开计算，考虑静态影响）
            lineyun_event = _compute_lineyun_bonus(ln.getAge(), base_events, static_activation_events)
            lineyun_bonus = lineyun_event.get("risk_percent", 0.0) if lineyun_event else 0.0
            lineyun_bonus_gan = lineyun_event.get("lineyun_bonus_gan", 0.0) if lineyun_event else 0.0
            lineyun_bonus_zhi = lineyun_event.get("lineyun_bonus_zhi", 0.0) if lineyun_event else 0.0

            # ===== 计算年度总风险 =====
            # 直接累加所有事件的风险（不拆分天干地支）
            total_risk_percent = 0.0
            
            # 冲的风险
            if clash_ln_natal:
                total_risk_percent += clash_ln_natal.get("risk_percent", 0.0)
            # 运年相冲的风险
            if clash_dayun_liunian:
                total_risk_percent += clash_dayun_liunian.get("risk_percent", 0.0)
            # 静态冲激活风险
            total_risk_percent += static_clash_activation_risk
            # 静态天克地冲风险
            total_risk_percent += static_tkdc_activation_risk_zhi + static_tkdc_activation_risk_gan
            # 静态刑激活风险
            total_risk_percent += static_punish_activation_risk
            # 刑的风险
            for punish_ev in punishments_ln:
                # 过滤掉既冲又刑的情况
                if clash_ln_natal:
                    clash_target = clash_ln_natal.get("target_branch")
                    if punish_ev.get("target_branch") == clash_target:
                        continue
                total_risk_percent += punish_ev.get("risk_percent", 0.0)
            # 模式风险
            for pat_ev in pattern_events_filtered:
                total_risk_percent += pat_ev.get("risk_percent", 0.0)
            # 静态模式激活风险
            for static_ev in static_activation_events:
                total_risk_percent += static_ev.get("risk_percent", 0.0)
            # 线运加成
            total_risk_percent += lineyun_bonus
            
            # ===== §4.4 流年好运判断（简单规则：用神+风险≤15%） =====
            # 如果天干或地支的五行中至少有一个落在用神列表中，且 total_risk_percent ≤ 15，则标记为"好运"
            is_good_ln = False
            if (gan_good_ln or zhi_good_ln) and total_risk_percent <= 15.0:
                is_good_ln = True
            
            # 删除不再使用的标签计算函数调用
            # first_half_label, second_half_label, year_label 已删除

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
            # 添加静态模式激活事件
            all_events.extend(static_activation_events)
            # 添加静态冲/刑激活事件（如果有）
            if static_clash_activation_risk > 0.0:
                all_events.append({
                    "type": "static_clash_activation",
                    "role": "base",
                    "risk_percent": static_clash_activation_risk,
                    "flow_year": ln.getYear(),
                    "flow_label": gz_ln,
                    "source": "dayun_natal_clash",
                })
            if static_punish_activation_risk > 0.0:
                all_events.append({
                    "type": "static_punish_activation",
                    "role": "base",
                    "risk_percent": static_punish_activation_risk,
                    "flow_year": ln.getYear(),
                    "flow_label": gz_ln,
                    "source": "dayun_natal_punish",
                })
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
                "is_good": is_good_ln,  # §4.4 流年好运判断（用神+风险≤15%）
                "clashes_natal": [clash_ln_natal] if clash_ln_natal else [],
                "clashes_dayun": clashes_dayun,
                "punishments_natal": punishments_ln,  # 流年支 与 命局地支 的刑
                "patterns_liunian": pattern_events_filtered,  # 流年模式事件（已过滤掉与冲重叠的）
                "patterns_static_activation": static_activation_events,  # §9 静态模式被流年激活的事件
                "harmonies_natal": harmonies_ln,  # 流年与原局的六合/三合/半合/三会（只解释，不计分）
                "harmonies_dayun": [],  # 流年与大运的合类（目前为空，后续可扩展）
                "lineyun_bonus": lineyun_bonus,  # 总加成（天干侧+地支侧）
                "lineyun_bonus_gan": lineyun_bonus_gan,  # §11.3 天干侧线运加成
                "lineyun_bonus_zhi": lineyun_bonus_zhi,  # §11.3 地支侧线运加成
                "total_risk_percent": total_risk_percent,
                "all_events": all_events,
            }

            liunian_list.append(liunian_dict)

        # 一个大运 + 对应的十个流年
        dayun_dict = asdict(dayun_luck)
        dayun_dict["harmonies_natal"] = harmonies_dy  # 大运与原局的六合/三合/半合/三会（只解释，不计分）
        
        # ===== §4.4 大运好运判断（简单规则：用神+平均风险≤15%） =====
        # 计算该步大运下所有流年的平均风险
        total_risk_sum = 0.0
        risk_count = 0
        for liunian_dict in liunian_list:
            total_risk_sum += liunian_dict.get("total_risk_percent", 0.0)
            risk_count += 1
        total_risk_average = total_risk_sum / risk_count if risk_count > 0 else 0.0
        
        # 如果天干或地支的五行中至少有一个落在用神列表中，且平均风险 ≤ 15%，则标记为"好运"
        is_good_dy_simple = False
        if (gan_good_dy or zhi_good_dy) and total_risk_average <= 15.0:
            is_good_dy_simple = True
        
        # ===== §8 大运风险与好坏判定字段 =====
        dayun_dict["risk_dayun_zhi"] = risk_dayun_zhi
        dayun_dict["risk_dayun_gan"] = risk_dayun_gan
        dayun_dict["risk_dayun_total"] = risk_dayun_total
        dayun_dict["total_risk_average"] = total_risk_average  # §4.4 该步大运下所有流年的平均风险
        dayun_dict["is_good"] = is_good_dy_simple  # §4.4 大运好运判断（用神+平均风险≤15%）
        dayun_dict["dayun_label"] = dayun_label  # §8 "好运" | "坏运" | "一般" | "一般（有变动）" | "坏运（用神过旺/变动过大）"
        dayun_dict["is_very_good"] = is_very_good  # 是否"非常好运"（干支皆用神且风险<30%）
        dayun_dict["punishments_natal"] = punishments_dy_filtered  # 大运支 与 命局地支 的刑
        dayun_dict["patterns_dayun"] = dayun_pattern_events  # 大运干/支 与 命局干/支 的模式事件

        groups.append(
            {
                "dayun": dayun_dict,
                "liunian": liunian_list,  # 已经是 dict，不需要 asdict
            }
        )

    # 按大运起运年份排序（保险起见）
    groups.sort(key=lambda g: g["dayun"]["start_year"])

    return {"groups": groups}
