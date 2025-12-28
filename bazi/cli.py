# -*- coding: utf-8 -*-
"""命令行交互：输入生日 → 八字 + 日主 + 用神 + 大运/流年好运 + 冲的信息。"""

from __future__ import annotations

from datetime import datetime

from .lunar_engine import analyze_basic
from .luck import analyze_luck
from .config import ZHI_WUXING


def _generate_marriage_suggestion(yongshen_elements: list[str]) -> str:
    """根据用神五行生成婚配建议。
    
    参数:
        yongshen_elements: 用神五行列表，例如 ["木", "火"]
    
    返回:
        婚配建议字符串，例如 "【婚配建议】推荐：虎兔蛇马；或 木，火旺的人。"
    """
    if not yongshen_elements:
        return ""
    
    # 地支到生肖的映射
    zhi_to_zodiac = {
        "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔",
        "辰": "龙", "巳": "蛇", "午": "马", "未": "羊",
        "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
    }
    
    # 五行到地支的映射（只用主五行）
    element_to_zhi = {
        "水": ["亥", "子"],
        "金": ["申", "酉"],
        "木": ["寅", "卯"],
        "火": ["巳", "午"],
        "土": ["辰", "戌", "丑", "未"],
    }
    
    # 收集每个五行对应的生肖
    zodiac_blocks = {
        "水": [],  # 猪鼠
        "金": [],  # 猴鸡
        "木": [],  # 虎兔
        "火": [],  # 蛇马
        "土": [],  # 龙狗牛羊
    }
    
    for elem in yongshen_elements:
        if elem in element_to_zhi:
            for zhi in element_to_zhi[elem]:
                zodiac = zhi_to_zodiac.get(zhi, "")
                if zodiac and zodiac not in zodiac_blocks[elem]:
                    zodiac_blocks[elem].append(zodiac)
    
    # 按顺序拼接生肖块
    result_parts = []
    
    # 1. 先拼 水块(猪鼠) + 金块(猴鸡)
    if zodiac_blocks["水"]:
        result_parts.extend(zodiac_blocks["水"])
    if zodiac_blocks["金"]:
        result_parts.extend(zodiac_blocks["金"])
    
    # 2. 再拼 木块(虎兔) + 火块(蛇马)
    if zodiac_blocks["木"]:
        result_parts.extend(zodiac_blocks["木"])
    if zodiac_blocks["火"]:
        result_parts.extend(zodiac_blocks["火"])
    
    # 3. 最后拼 土块(龙狗牛羊)
    if zodiac_blocks["土"]:
        result_parts.extend(zodiac_blocks["土"])
    
    # 构建推荐生肖串
    zodiac_str = "".join(result_parts) if result_parts else ""
    
    # 构建"旺的人"文案：按候选五行顺序，用中文顿号分隔
    wang_str = "，".join(yongshen_elements)
    
    if zodiac_str:
        return f"【婚配建议】推荐：{zodiac_str}；或 {wang_str}旺的人。"
    else:
        return f"【婚配建议】推荐：或 {wang_str}旺的人。"


def _calc_half_year_label(risk: float, is_yongshen: bool) -> str:
    """计算半年判词。
    
    参数:
        risk: 半年危险系数（H1 或 H2）
        is_yongshen: 是否是用神
    
    返回:
        判词：好运、一般、有轻微变动、凶（棘手/意外）
    """
    if risk <= 10.0:
        return "好运" if is_yongshen else "一般"
    elif risk < 20.0:
        return "有轻微变动"
    else:  # risk >= 20.0
        return "凶（棘手/意外）"


def _calc_year_title_line(
    total_risk: float,
    risk_from_gan: float,
    risk_from_zhi: float,
    is_gan_yongshen: bool,
    is_zhi_yongshen: bool,
) -> tuple[str, bool]:
    """计算年度标题行。
    
    参数:
        total_risk: 总危险系数 Y
        risk_from_gan: 上半年危险系数 H1
        risk_from_zhi: 下半年危险系数 H2
        is_gan_yongshen: 天干是否用神
        is_zhi_yongshen: 地支是否用神
    
    返回:
        (title_line, should_print_suggestion)
        title_line: 年度标题行文本
        should_print_suggestion: 是否打印建议行（Y >= 40）
    """
    Y = total_risk
    
    # A) 若 Y >= 40：全年 凶（棘手/意外）
    if Y >= 40.0:
        return ("全年 凶（棘手/意外）", True)
    
    # B) 若 25 <= Y < 40：全年 明显变动（可克服）
    if Y >= 25.0:
        return ("全年 明显变动（可克服）", False)
    
    # C) 若 Y < 25：才允许输出上/下半年
    H1 = risk_from_gan
    H2 = risk_from_zhi
    
    S1 = _calc_half_year_label(H1, is_gan_yongshen)
    S2 = _calc_half_year_label(H2, is_zhi_yongshen)
    
    return (f"上半年 {S1}，下半年 {S2}", False)


def _print_sanhe_sanhui_clash_bonus(sanhe_sanhui_bonus_ev: dict) -> None:
    """打印三合/三会逢冲额外加分信息。
    
    打印顺序：
    1. 哪个字属于哪个三合/三会、哪个是单独字
    2. 单独字是不是用神（如果有单独字）
    3. 本规则本年额外加分是多少（+15 或 +35），并声明本年封顶已用掉
    """
    bonus_percent = sanhe_sanhui_bonus_ev.get("risk_percent", 0.0)
    if bonus_percent <= 0.0:
        return
    
    flow_branch = sanhe_sanhui_bonus_ev.get("flow_branch", "")
    target_branch = sanhe_sanhui_bonus_ev.get("target_branch", "")
    group_type = sanhe_sanhui_bonus_ev.get("group_type", "")  # "sanhe" or "sanhui"
    group_name = sanhe_sanhui_bonus_ev.get("group_name", "")  # 例如"火局"、"木会"
    group_members = sanhe_sanhui_bonus_ev.get("group_members", [])  # 三合/三会的三个成员字
    flow_in_group = sanhe_sanhui_bonus_ev.get("flow_in_group", False)
    target_in_group = sanhe_sanhui_bonus_ev.get("target_in_group", False)
    standalone_zhi = sanhe_sanhui_bonus_ev.get("standalone_zhi")
    standalone_is_yongshen = sanhe_sanhui_bonus_ev.get("standalone_is_yongshen")
    
    # 构建三合/三会名称（例如"寅午戌三合火局"或"巳午未三会火会"）
    group_members_str = "".join(group_members)
    if group_type == "sanhe":
        group_full_name = f"{group_members_str}三合{group_name}"
    else:  # sanhui
        group_full_name = f"{group_members_str}三会{group_name}"
    
    # 打印：哪个字属于哪个三合/三会、哪个是单独字
    if flow_in_group and target_in_group:
        # 两个字都属于局/会
        print(f"          {group_full_name}被冲到：冲对中'{flow_branch}'和'{target_branch}'都属于{group_full_name}")
    elif flow_in_group:
        # flow_branch属于局/会，target_branch是单独字
        print(f"          {group_full_name}被冲到：冲对中'{flow_branch}'属于{group_full_name}；'{target_branch}'是单独字")
    else:  # target_in_group
        # target_branch属于局/会，flow_branch是单独字
        print(f"          {group_full_name}被冲到：冲对中'{target_branch}'属于{group_full_name}；'{flow_branch}'是单独字")
    
    # 打印：单独字是不是用神（如果有单独字）
    if standalone_zhi:
        yongshen_status = "是用神" if standalone_is_yongshen else "不是用神"
        print(f"          单独字{standalone_zhi}：{yongshen_status}")
    
    # 打印：本规则本年额外加分是多少（+15 或 +35），并声明本年封顶已用掉
    print(f"          三合/三会逢冲额外：+{bonus_percent:.0f}%（本年只加一次）")


def _format_clash_natal(ev: dict) -> str:
    """把命局冲的信息整理成一行文字。
    
    打印顺序：基础冲 → 墓库加成 → 天克地冲 → 总影响
    """
    palaces = sorted(
        {t["palace"] for t in ev.get("targets", []) if t.get("palace")}
    )
    palaces_str = "、".join(palaces) if palaces else "—"

    level = ev.get("impact_level", "unknown")
    level_map = {
        "minor": "轻微变化",
        "moderate": "较大变化",
        "major": "重大变化",
    }
    level_label = level_map.get(level, level)

    # 从 breakdown 或直接字段获取数值
    breakdown = ev.get("breakdown", {})
    base = breakdown.get("base_percent", ev.get("base_power_percent", ev.get("power_percent", 0.0)))
    grave_bonus = breakdown.get("grave_bonus_percent", ev.get("grave_bonus_percent", 0.0))
    tkdc_bonus = breakdown.get("tkdc_bonus_percent", ev.get("tkdc_bonus_percent", ev.get("tian_ke_di_chong_bonus_percent", 0.0)))
    risk = ev.get("risk_percent", base + grave_bonus + tkdc_bonus)

    # 十神信息
    tg = ev.get("shishens", {}) or {}
    flow_tg = tg.get("flow_branch") or {}
    target_tg = tg.get("target_branch") or {}

    flow_ss = flow_tg.get("shishen")
    target_ss = target_tg.get("shishen")

    if flow_ss or target_ss:
        shishen_part = f" 十神：流年 {flow_ss or '-'} / 命局 {target_ss or '-'}"
    else:
        shishen_part = ""

    # 构建一行总览：总冲影响：{total}%（基础冲 {base} + 墓库 {grave} + TKDC {tkdc}）
    clash_detail_parts = [f"基础冲 {base:.2f}"]
    if grave_bonus > 0:
        clash_detail_parts.append(f"墓库 {grave_bonus:.2f}")
    if tkdc_bonus > 0:
        clash_detail_parts.append(f"TKDC {tkdc_bonus:.2f}")
    
    clash_detail_str = " + ".join(clash_detail_parts)
    clash_summary = f"总冲影响：{risk:.2f}%（{clash_detail_str}）"
    
    return (
        f"冲：{ev['flow_branch']}{ev['target_branch']}冲，"
        f"{clash_summary}，"
        f"等级：{level_label}，"
        f"宫位：{palaces_str}"
        f"{shishen_part}"
    )





def run_cli(birth_dt: datetime = None, is_male: bool = None) -> None:
    """运行CLI，可以接受参数（用于测试）或从输入获取（用于交互）。
    
    参数:
        birth_dt: 出生日期时间（可选，如果不提供则从输入获取）
        is_male: 是否为男性（可选，如果不提供则从输入获取）
    """
    if birth_dt is None or is_male is None:
        # 交互模式
        print("=== Hayyy 八字 · 日主强弱 + 用神 + 大运流年 MVP ===")
        print("当前版本：")
        print("  - 只支持【阳历】输入")
        print("  - 时间默认按【出生地当地时间 / 北京时间】理解")
        print("")

        date_str = input("请输入阳历生日 (YYYY-MM-DD)：").strip()
        time_str = input("请输入出生时间 (HH:MM，例如 09:30，未知可写 00:00)：").strip()

        if not date_str:
            print("日期不能为空。")
            return
        if not time_str:
            time_str = "00:00"

        try:
            birth_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            print("日期或时间格式错误，请按 YYYY-MM-DD 和 HH:MM 格式输入。")
            return

        sex_str = input("请输入性别 (M/F)：").strip().upper()
        is_male = True if sex_str != "F" else False

    # ===== 本命 + 用神 =====
    result = analyze_basic(birth_dt)
    bazi = result["bazi"]

    print("\n—— 四柱八字 ——")
    print(f"年柱：{bazi['year']['gan']}{bazi['year']['zhi']}")
    print(f"月柱：{bazi['month']['gan']}{bazi['month']['zhi']}")
    print(f"日柱：{bazi['day']['gan']}{bazi['day']['zhi']}  （日主）")
    print(f"时柱：{bazi['hour']['gan']}{bazi['hour']['zhi']}")

    print("\n—— 日主信息 ——")
    print(f"日主：{bazi['day']['gan']} 日（五行：{result['day_master_element']}）")
    print(f"日主综合强弱：{result['strength_percent']:.2f}%")
    print(f"（内部原始得分：{result['strength_score_raw']:.4f}）")
    print(f"生扶力量占比：{result['support_percent']:.2f}%")
    print(f"消耗力量占比：{result['drain_percent']:.2f}%")

    # 主要性格 / 其他性格
    dominant_traits = result.get("dominant_traits") or []
    yongshen_elements = result.get("yongshen_elements", [])
    
    if dominant_traits:
        # 辅助：按 group 索引
        trait_by_group = {t.get("group"): t for t in dominant_traits}

        def _stem_hits(trait: dict) -> int:
            """计算该大类总透干次数（所有子类透干次数之和）"""
            detail = trait.get("detail") or []
            hits = sum(d.get("stems_visible_count", 0) for d in detail)
            return min(hits, 3)

        def _format_trait_line1(trait: dict, is_major_by_rule3: bool = False) -> str:
            """格式化第1行：{大类}（{total_percent:.1f}%）：{子类标签}；{透干柱位列表}透干×{n}；{得月令字段}；{子类百分比摘要}"""
            group = trait.get("group", "-")
            total_percent = trait.get("total_percent", 0.0)
            sub_label = trait.get("sub_label", trait.get("mix_label", ""))
            detail = trait.get("detail") or []
            de_yueling = trait.get("de_yueling")
            
            # 如果力量为0，显示"八字中没有{大类}星"
            if total_percent == 0.0:
                # 根据大类名称生成对应的星名
                star_name_map = {
                    "财": "财星",
                    "印": "印星",
                    "官杀": "官杀星",
                    "食伤": "食伤星",
                    "比劫": "比劫星",
                }
                star_name = star_name_map.get(group, f"{group}星")
                sub_label = f"八字中没有{star_name}"
            
            # 收集所有透出的柱位（合并所有子类的透出柱位）
            all_stem_pillars = []
            total_stem_hits = 0
            for d in detail:
                stem_pillars = d.get("stem_pillars", [])
                all_stem_pillars.extend(stem_pillars)
                total_stem_hits += d.get("stems_visible_count", 0)
            
            # 去重并保持顺序（年柱→月柱→时柱）
            pillar_order = ["年柱", "月柱", "时柱"]
            seen = set()
            ordered_pillars = []
            for p in pillar_order:
                if p in all_stem_pillars and p not in seen:
                    ordered_pillars.append(p)
                    seen.add(p)
            
            # 构建透干信息
            stem_part = ""
            if total_stem_hits >= 1:
                pillars_str = "，".join(ordered_pillars)
                stem_part = f"；{pillars_str}透干×{total_stem_hits}"
                if is_major_by_rule3:
                    stem_part += "，且为用神"
            
            # 得月令字段
            de_yueling_part = ""
            if de_yueling:
                de_yueling_part = f"；{de_yueling}"
            
            # 子类百分比摘要
            present_subs = [d for d in detail if d.get("percent", 0.0) > 0.0]
            if len(present_subs) == 1:
                # 纯：纯{子类}{percent:.1f}%
                sub_name = present_subs[0].get("name", "")
                sub_percent = present_subs[0].get("percent", 0.0)
                subs_summary = f"纯{sub_name}{sub_percent:.1f}%"
            elif len(present_subs) >= 2:
                # 混：两个子类的百分比，用逗号分隔
                # 固定顺序：正/偏、正官/七杀、食神/伤官、比肩/劫财、正印/偏印
                sub_pairs = []
                for d in detail:
                    if d.get("percent", 0.0) > 0.0:
                        sub_pairs.append((d.get("name", ""), d.get("percent", 0.0)))
                # 按固定顺序排序（正/偏、正官/七杀等，正在前，偏/杀在后）
                # 但用户期望输出显示"偏财20.0%，正财15.0%"，说明应该按占比降序
                # 重新理解：用户说"固定顺序：正/偏、正官/七杀、食神/伤官、比肩/劫财、正印/偏印"
                # 但实际期望输出是"偏财20.0%，正财15.0%"，说明应该按占比从高到低排序
                sub_pairs.sort(key=lambda x: -x[1])  # 按占比降序排序
                subs_summary = "，".join(f"{name}{percent:.1f}%" for name, percent in sub_pairs)
            else:
                subs_summary = "—"
            
            return f"{group}（{total_percent:.1f}%）：{sub_label}{stem_part}{de_yueling_part}；{subs_summary}"
        
        def _format_trait_line2(trait: dict) -> str:
            """格式化第2行：{大类}的五行：{element}；{大类}{为/不为}用神"""
            group = trait.get("group", "-")
            element = trait.get("element", "")
            # 即使 element 为 None 或空，也要显示（当力量为0时，element 应该已经通过定义计算出来了）
            if not element:
                element = "None"  # 如果还是没有，显示 None（但理论上不应该出现）
            is_yongshen = element in yongshen_elements if element and element != "None" else False
            yongshen_status = "为用神" if is_yongshen else "不为用神"
            return f"- {group}的五行：{element}；{group}{yongshen_status}"

        # 主要性格：满足 total_percent>=35 或 stem_hits>=2 或 (stem_hits>=1 且为用神)
        major = []
        major_by_rule3 = set()  # 记录因为规则3（透干>=1且为用神）而晋级的主要性格
        
        for t in dominant_traits:
            total_percent = t.get("total_percent", 0.0)
            hits = _stem_hits(t)
            element = t.get("element", "")
            is_yongshen = element in yongshen_elements if element else False
            
            is_major = False
            if total_percent >= 35.0 or hits >= 2:
                is_major = True
            elif hits >= 1 and is_yongshen:
                is_major = True
                major_by_rule3.add(t.get("group"))
            
            if is_major:
                major.append(t)

        # 收集已经在"主要性格"里打印过的性格大类，用于"其他性格"去重
        main_groups = {t.get("group") for t in major} if major else set()

        if major:
            print("\n—— 主要性格 ——")
            for trait in major:
                group = trait.get("group", "")
                is_major_by_rule3 = group in major_by_rule3 and (
                    trait.get("total_percent", 0.0) < 35.0 and _stem_hits(trait) < 2
                )
                print(_format_trait_line1(trait, is_major_by_rule3))
                print(_format_trait_line2(trait))

        # 其他性格：五大类全量（含 0%）
        print("\n—— 其他性格 ——")
        all_groups = ["财", "印", "官杀", "食伤", "比劫"]
        for g in all_groups:
            # 已经在"主要性格"中打印过的性格大类，这里跳过，避免重复
            if g in main_groups:
                continue
            trait = trait_by_group.get(g, {})
            if not trait:
                # 如果该大类不存在，创建一个空的
                trait = {
                    "group": g,
                    "total_percent": 0.0,
                    "sub_label": "无",
                    "detail": [],
                    "de_yueling": None,
                    "element": None,
                }
            
            print(_format_trait_line1(trait, False))
            print(_format_trait_line2(trait))

    # 六亲助力：只输出用神十神大类
    print("\n—— 六亲助力 ——")
    
    def _get_liuqin_source(group: str, detail: List[Dict[str, Any]], total_percent: float, is_male: bool) -> str:
        """获取六亲助力的来源清单"""
        present_subs = [d for d in detail if d.get("percent", 0.0) > 0.0]
        
        if group == "印":
            if total_percent == 0:
                # 原局没有印星：合并输出
                return "母亲/长辈/贵人/老师，学历证书/名誉背书/正统学习/学校体系，技术型/非传统学习与灵感路径（偏印）"
            else:
                zhengyin_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正印"), 0.0)
                pianyin_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "偏印"), 0.0)
                
                if zhengyin_percent > 0 and pianyin_percent == 0:
                    # 纯正印
                    return "母亲/长辈/贵人/老师，学历证书/名誉背书/正统学习/学校体系"
                elif pianyin_percent > 0 and zhengyin_percent == 0:
                    # 纯偏印
                    return "母亲/长辈/贵人/老师，技术型/非传统学习与灵感路径（偏印）"
                else:
                    # 混杂
                    return "母亲/长辈/贵人/老师，学历证书/名誉背书/正统学习/学校体系 ＋ 技术型/非传统学习与灵感路径（偏印）"
        
        elif group == "比劫":
            # 比肩/劫财/比劫混杂，都用统一来源（不再区分）
            if total_percent == 0:
                # 原局没有比劫星（去掉末尾逗号）
                return "兄弟姐妹/同辈朋友/同学同事，自我/独立/同行合伙/同类支持"
            else:
                # 比肩/劫财/混杂，都用统一来源
                return "兄弟姐妹/同辈朋友/同学同事，自我/独立/同行合伙/同类支持"
        
        elif group == "食伤":
            if total_percent == 0:
                # 原局没有食伤星：统一新文案
                return "子女/晚辈/技术，合理宣泄/才艺产出，表达/创新/输出型技术，考试发挥/即兴发挥/临场表现"
            else:
                shishen_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "食神"), 0.0)
                shangguan_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "伤官"), 0.0)
                
                if shishen_percent > 0 and shangguan_percent == 0:
                    # 纯食神：保留原来的更细分来源
                    return "子女/晚辈，享受/口福/温和表达/才艺产出/疗愈与松弛"
                elif shangguan_percent > 0 and shishen_percent == 0:
                    # 纯伤官：保留原来的更细分来源
                    return "子女/晚辈，表达欲/叛逆/创新/挑规则/锋芒与口舌是非/输出型技术"
                else:
                    # 混杂：统一新文案
                    return "子女/晚辈/技术，合理宣泄/才艺产出，表达/创新/输出型技术，考试发挥/即兴发挥/临场表现"
        
        elif group == "财":
            if total_percent == 0:
                # 原局没有财星
                if is_male:
                    return "父亲/爸爸，妻子/老婆/伴侣，钱与资源/收入/项目机会/交换"
                else:
                    return "父亲/爸爸，钱与资源/收入/项目机会/交换"
            else:
                zhengcai_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正财"), 0.0)
                piancai_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "偏财"), 0.0)
                
                if zhengcai_percent > 0 and piancai_percent == 0:
                    # 纯正财
                    if is_male:
                        return "父亲/爸爸，妻子/老婆/伴侣，稳定收入/打工/正规渠道获得的钱/可控资源与交换/长期投入回报"
                    else:
                        return "父亲/爸爸，稳定收入/打工/正规渠道获得的钱/可控资源与交换/长期投入回报"
                elif piancai_percent > 0 and zhengcai_percent == 0:
                    # 纯偏财
                    if is_male:
                        return "父亲/爸爸，妻子/老婆/伴侣，外财/机会财/项目/做生意/社交资源/流动性/投机"
                    else:
                        return "父亲/爸爸，外财/机会财/项目/做生意/社交资源/流动性/投机"
                else:
                    # 混杂（合并输出）
                    if is_male:
                        return "父亲/爸爸，妻子/老婆/伴侣，稳定收入/打工/正规渠道获得的钱/可控资源与交换/长期投入回报，外财/机会财/项目/做生意/社交资源/流动性/投机"
                    else:
                        return "父亲/爸爸，稳定收入/打工/正规渠道获得的钱/可控资源与交换/长期投入回报，外财/机会财/项目/做生意/社交资源/流动性/投机"
        
        elif group == "官杀":
            if total_percent == 0:
                # 原局没有官杀星
                if is_male:
                    return "领导/上司/官职/体制/规则/名气/声望"
                else:
                    return "老公/丈夫/男友，领导/上司/官职/体制/规则/名气/声望"
            else:
                zhengguan_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正官"), 0.0)
                qisha_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "七杀"), 0.0)
                
                if zhengguan_percent > 0 and qisha_percent == 0:
                    # 纯正官
                    if is_male:
                        return "领导/上司/官职/职位/体制/规则/名气/声望/责任与自我约束"
                    else:
                        return "老公/丈夫/男友，领导/上司/官职/职位/体制/规则/名气/声望/责任与自我约束"
                elif qisha_percent > 0 and zhengguan_percent == 0:
                    # 纯七杀
                    if is_male:
                        return "领导/上司/强权压力/竞争与执行/风险与突破，官职/体制/规则/名气"
                    else:
                        return "老公/丈夫/男友，领导/上司/强权压力/竞争与执行/风险与突破，官职/体制/规则/名气"
                else:
                    # 混杂（合并输出）
                    if is_male:
                        return "领导/上司/强权压力/竞争与执行/风险与突破，官职/职位/体制/规则/名气/声望/责任与自我约束"
                    else:
                        return "老公/丈夫/男友，领导/上司/强权压力/竞争与执行/风险与突破，官职/职位/体制/规则/名气/声望/责任与自我约束"
        
        return ""
    
    def _get_liuqin_status(group: str, detail: List[Dict[str, Any]], total_percent: float) -> str:
        """获取六亲助力的括号状态"""
        if total_percent == 0:
            star_name_map = {
                "财": "财星",
                "印": "印星",
                "官杀": "官杀星",
                "食伤": "食伤星",
                "比劫": "比劫星",
            }
            star_name = star_name_map.get(group, f"{group}星")
            return f"（原局没有{star_name}）"
        
        present_subs = [d for d in detail if d.get("percent", 0.0) > 0.0]
        
        if group == "印":
            zhengyin_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正印"), 0.0)
            pianyin_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "偏印"), 0.0)
            if zhengyin_percent > 0 and pianyin_percent == 0:
                return "（正印）"
            elif pianyin_percent > 0 and zhengyin_percent == 0:
                return "（偏印）"
            else:
                return "（正偏印混杂）"
        
        elif group == "财":
            zhengcai_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正财"), 0.0)
            piancai_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "偏财"), 0.0)
            if zhengcai_percent > 0 and piancai_percent == 0:
                return "（正财）"
            elif piancai_percent > 0 and zhengcai_percent == 0:
                return "（偏财）"
            else:
                return "（正偏财混杂）"
        
        elif group == "官杀":
            zhengguan_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "正官"), 0.0)
            qisha_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "七杀"), 0.0)
            if zhengguan_percent > 0 and qisha_percent == 0:
                return "（正官）"
            elif qisha_percent > 0 and zhengguan_percent == 0:
                return "（七杀）"
            else:
                return "（官杀混杂）"
        
        elif group == "食伤":
            shishen_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "食神"), 0.0)
            shangguan_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "伤官"), 0.0)
            if shishen_percent > 0 and shangguan_percent == 0:
                return "（食神）"
            elif shangguan_percent > 0 and shishen_percent == 0:
                return "（伤官）"
            else:
                return "（食伤混杂）"
        
        elif group == "比劫":
            bijian_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "比肩"), 0.0)
            jiecai_percent = next((d.get("percent", 0.0) for d in detail if d.get("name") == "劫财"), 0.0)
            if bijian_percent > 0 and jiecai_percent == 0:
                return "（比肩）"
            elif jiecai_percent > 0 and bijian_percent == 0:
                return "（劫财）"
            elif bijian_percent > 0 and jiecai_percent > 0:
                return "（比劫混杂）"
            else:
                return ""
        
        return ""
    
    def _get_strength_text(total_percent: float, group: str) -> str:
        """获取强度话术"""
        if total_percent == 0:
            return f"该助力有心帮助但能力一般；走到{group}运/年会有额外帮助。"
        elif total_percent < 30:
            return "用神有力，助力较多。"
        else:
            return "用神力量很大，助力非常非常大。"
    
    # 获取所有五大类，检查哪些是用神
    all_categories = ["印", "财", "官杀", "食伤", "比劫"]
    liuqin_traits = []
    
    for cat in all_categories:
        trait = trait_by_group.get(cat, {})
        if not trait:
            # 如果该大类不存在，创建一个空的
            trait = {
                "group": cat,
                "total_percent": 0.0,
                "sub_label": "无",
                "detail": [],
                "de_yueling": None,
                "element": None,
            }
            # 需要计算该大类的五行（通过定义）
            from .traits import _get_category_element_by_definition
            bazi = result.get("bazi", {})
            day_gan = bazi.get("day", {}).get("gan", "")
            if day_gan:
                # 将显示名称转换为内部类别名称
                cat_internal = "印星" if cat == "印" else "财星" if cat == "财" else cat
                trait["element"] = _get_category_element_by_definition(cat_internal, day_gan)
        
        element = trait.get("element", "")
        if element and element in yongshen_elements:
            # 该大类是用神，加入六亲助力
            liuqin_traits.append(trait)
    
    # 打印六亲助力
    for trait in liuqin_traits:
        group = trait.get("group", "")
        total_percent = trait.get("total_percent", 0.0)
        detail = trait.get("detail", [])
        
        # 名称字段：比劫在原局有星时显示"比肩"，否则显示"比劫"
        display_name = group
        if group == "比劫" and total_percent > 0:
            # 只要原局有比劫星（total_percent > 0），就显示"比肩"
            display_name = "比肩"
        
        # 括号状态
        status = _get_liuqin_status(group, detail, total_percent)
        
        # 强度话术
        strength_text = _get_strength_text(total_percent, group)
        
        # 第1行
        print(f"{display_name}{status}：{strength_text}")
        
        # 第2行（缩进两个空格）
        source = _get_liuqin_source(group, detail, total_percent, is_male)
        print(f"  来源：{source}")

    print("\n—— 全局五行占比（八个字）——")
    global_dist = result["global_element_percentages"]
    for e in ["木", "火", "土", "金", "水"]:
        print(f"{e}：{global_dist.get(e, 0.0):.2f}%")

    # 合并用神信息打印
    print("\n—— 用神信息 ——")
    yong = result["yongshen_elements"]
    yong_str = "、".join(yong)
    marriage_suggestion = _generate_marriage_suggestion(yong)
    print(f"用神五行（候选）： {yong_str} {marriage_suggestion}")
    
    # 用神（五行→十神）
    yong_ss = result.get("yongshen_shishen") or []
    if yong_ss:
        ss_parts = []
        for entry in yong_ss:
            elem = entry.get("element", "-")
            cats = entry.get("categories") or []
            specifics = entry.get("shishens") or []
            cats_str = "、".join(cats) if cats else "-"
            specs_str = "、".join(specifics) if specifics else "-"
            ss_parts.append(f"{elem}：{cats_str}（{specs_str}）")
        print("用神（五行→十神）：" + "，".join(ss_parts))
    
    # 用神落点
    yong_tokens = result.get("yongshen_tokens") or []
    pillar_label = {
        "year": "年柱",
        "month": "月柱",
        "day": "日柱",
        "hour": "时柱",
    }
    kind_label = {"gan": "干", "zhi": "支"}
    tokens_by_elem = {e.get("element"): e.get("positions", []) for e in yong_tokens}
    
    luodian_parts = []
    for elem in yong:
        positions = tokens_by_elem.get(elem, [])
        if not positions:
            luodian_parts.append(f"{elem}：原局没有")
            continue
        parts = []
        for pos in positions:
            pillar = pillar_label.get(pos.get("pillar", ""), pos.get("pillar", ""))
            kind = kind_label.get(pos.get("kind", ""), pos.get("kind", ""))
            char = pos.get("char", "?")
            ss = pos.get("shishen", "-")
            parts.append(f"{pillar}{kind} {char}({ss})")
        luodian_parts.append(f"{elem}：" + "，".join(parts))
    if luodian_parts:
        print("用神落点：" + "，".join(luodian_parts))
    
    # ===== 原局六合（只解释，不计分） =====
    from .config import PILLAR_PALACE_CN
    natal_harmonies = result.get("natal_harmonies", []) or []
    # 原局六合
    natal_liuhe_lines = []
    for ev in natal_harmonies:
        if ev.get("type") != "branch_harmony":
            continue
        if ev.get("subtype") != "liuhe":
            continue
        targets = ev.get("targets", [])
        if len(targets) < 2:
            continue
        t1, t2 = targets[0], targets[1]
        palace1 = t1.get("palace", "")
        palace2 = t2.get("palace", "")
        members = ev.get("members") or ev.get("matched_branches") or []
        if len(members) >= 2:
            pair_str = f"{members[0]}{members[1]}合"
        else:
            pair_str = f"{t1.get('target_branch', '')}{t2.get('target_branch', '')}合"
        if palace1 and palace2:
            natal_liuhe_lines.append(f"{palace1}和{palace2}合（{pair_str}）")
    if natal_liuhe_lines:
        # 只去掉完全重复的，同一宫位组合要保留
        uniq_lines = sorted(set(natal_liuhe_lines))
        print("原局六合：" + "，".join(uniq_lines))

    # 原局半合
    natal_banhe_lines = []
    for ev in natal_harmonies:
        if ev.get("type") != "branch_harmony":
            continue
        if ev.get("subtype") != "banhe":
            continue
        targets = ev.get("targets", [])
        if len(targets) < 2:
            continue
        t1, t2 = targets[0], targets[1]
        palace1 = t1.get("palace", "")
        palace2 = t2.get("palace", "")
        matched = ev.get("matched_branches", [])
        if len(matched) >= 2:
            pair_str = f"{matched[0]}{matched[1]}半合"
        else:
            pair_str = f"{t1.get('target_branch', '')}{t2.get('target_branch', '')}半合"
        if palace1 and palace2:
            natal_banhe_lines.append(f"{palace1} 与 {palace2} 半合（{pair_str}）")
    if natal_banhe_lines:
        uniq_banhe = sorted(set(natal_banhe_lines))
        print("原局半合：" + "，".join(uniq_banhe))
    
    # ===== 原局天干五合（只识别+打印，不影响风险） =====
    from .gan_wuhe import GanPosition, detect_gan_wuhe, format_gan_wuhe_event
    from .shishen import get_shishen
    
    day_gan = bazi["day"]["gan"]
    natal_gan_positions = []
    # 原局入口使用"年柱天干"格式
    pillar_labels = {"year": "年柱天干", "month": "月柱天干", "day": "日柱天干", "hour": "时柱天干"}
    for pillar in ["year", "month", "day", "hour"]:
        gan = bazi[pillar]["gan"]
        shishen = get_shishen(day_gan, gan) or "-"
        natal_gan_positions.append(GanPosition(
            source="natal",
            label=pillar_labels[pillar],
            gan=gan,
            shishen=shishen
        ))
    
    natal_wuhe_events = detect_gan_wuhe(natal_gan_positions)
    if natal_wuhe_events:
        for ev in natal_wuhe_events:
            # 原局入口不再带“原局”前缀，只打印柱位+字+五合+十神关系
            line = format_gan_wuhe_event(ev, incoming_shishen=None)
            print(f"原局天干五合：{line}")
    
    # 原局问题打印
    from .clash import detect_natal_tian_ke_di_chong
    
    natal_conflicts = result.get("natal_conflicts", {})
    natal_clashes = natal_conflicts.get("clashes", [])
    natal_punishments = natal_conflicts.get("punishments", [])
    natal_tkdc = detect_natal_tian_ke_di_chong(bazi)
    natal_patterns = result.get("natal_patterns", [])
    
    def _get_clash_explanation(palace1: str, palace2: str) -> str:
        """获取特定冲的解释文本"""
        # 标准化宫位名称（处理"事业家庭宫"和"家庭事业宫"的差异）
        def normalize_palace(p: str) -> str:
            if p == "事业家庭宫":
                return "家庭事业宫"
            return p
        
        p1 = normalize_palace(palace1)
        p2 = normalize_palace(palace2)
        
        # 创建宫位对（不区分顺序）
        palace_pair = frozenset([p1, p2])
        
        # 4种特定冲的解释
        clash_explanations = {
            frozenset(["祖上宫", "婚姻宫"]): "少年时期成长坎坷，家庭变故多",
            frozenset(["婚姻宫", "夫妻宫"]): "感情、婚姻矛盾多，变故频频",
            frozenset(["夫妻宫", "家庭事业宫"]): "中年后家庭生活不和谐，和子女关系不好或者没有子女",
            frozenset(["祖上宫", "夫妻宫"]): "婚姻生活易受上一辈、早年经历影响",
        }
        
        return clash_explanations.get(palace_pair, "")
    
    issues = []
    
    # 打印原局冲
    for clash in natal_clashes:
        targets = clash.get("targets", [])
        flow_branch = clash.get("flow_branch", "")
        target_branch = clash.get("target_branch", "")
        
        if targets and flow_branch and target_branch:
            # 获取被冲的宫位（targets中的）
            target_palaces = sorted({PILLAR_PALACE_CN.get(t.get("pillar", ""), "") for t in targets if t.get("pillar")})
            
            # 获取主动冲的宫位（flow_branch对应的柱）
            flow_palace = None
            for pillar in ("year", "month", "day", "hour"):
                if bazi[pillar]["zhi"] == flow_branch:
                    flow_palace = PILLAR_PALACE_CN.get(pillar, "")
                    break
            
            # 收集所有涉及的宫位
            all_palaces = set(target_palaces)
            if flow_palace:
                all_palaces.add(flow_palace)
            palaces = sorted(list(all_palaces))
            
            if len(palaces) >= 2:
                # 多个宫位被冲，两两组合打印
                for i in range(len(palaces)):
                    for j in range(i + 1, len(palaces)):
                        palace1 = palaces[i]
                        palace2 = palaces[j]
                        explanation = _get_clash_explanation(palace1, palace2)
                        # 格式：宫位A-宫位B 地支字冲 解释（如果有）
                        clash_text = f"{palace1}-{palace2} {flow_branch}{target_branch}冲"
                        if explanation:
                            issues.append(f"{clash_text} {explanation}")
                        else:
                            issues.append(clash_text)
            elif len(palaces) == 1:
                # 只有一个宫位（理论上不应该出现，但保留兼容）
                issues.append(f"{palaces[0]} {flow_branch}{target_branch}冲")
    
    # 打印原局刑
    # 对于自刑，需要收集所有自刑地支，然后两两组合打印
    self_punish_processed = set()  # 记录已处理的自刑地支，避免重复打印
    
    for punish in natal_punishments:
        targets = punish.get("targets", [])
        if targets:
            flow_branch = punish.get("flow_branch", "")
            target_branch = punish.get("target_branch", "")
            # 不再检查risk，只要存在就打印
            # 如果是自刑（flow_branch == target_branch），需要找到所有包含该地支的柱，然后两两组合打印
            if flow_branch == target_branch:
                # 检查是否已经处理过这个自刑地支
                if flow_branch in self_punish_processed:
                    continue  # 跳过，已经处理过
                self_punish_processed.add(flow_branch)
                
                # 自刑：找到所有包含该地支的柱
                involved_pillars = []
                for pillar in ("year", "month", "day", "hour"):
                    if bazi[pillar]["zhi"] == flow_branch:
                        involved_pillars.append(pillar)
                
                # 自刑应该至少有两个柱，两两组合打印
                if len(involved_pillars) >= 2:
                    # 两两组合：年-月、年-日、年-时、月-日、月-时、日-时
                    for i in range(len(involved_pillars)):
                        for j in range(i + 1, len(involved_pillars)):
                            pillar1 = involved_pillars[i]
                            pillar2 = involved_pillars[j]
                            palace1 = PILLAR_PALACE_CN.get(pillar1, "")
                            palace2 = PILLAR_PALACE_CN.get(pillar2, "")
                            # 检查是否是祖上宫-婚姻宫 刑（不区分顺序）
                            palace_pair = frozenset([palace1, palace2])
                            is_zu_shang_marriage = palace_pair == frozenset(["祖上宫", "婚姻宫"])
                            # 格式：宫位A-宫位B 地支字自刑 [解释]
                            punish_text = f"{palace1}-{palace2} {flow_branch}{target_branch}自刑"
                            if is_zu_shang_marriage:
                                punish_text += " 成长过程中波折较多，压力偏大"
                            issues.append(punish_text)
                else:
                    # 如果只找到一个柱，使用原来的逻辑
                    target_palace = PILLAR_PALACE_CN.get(targets[0].get("pillar", ""), "")
                    issues.append(f"{target_palace} {flow_branch}{target_branch}自刑")
            else:
                # 非自刑：使用原来的逻辑
                target_palace = PILLAR_PALACE_CN.get(targets[0].get("pillar", ""), "")
                # 找到flow_branch对应的柱
                flow_pillar = None
                target_pillar = targets[0].get("pillar", "")
                for pillar in ("year", "month", "day", "hour"):
                    if bazi[pillar]["zhi"] == flow_branch and pillar != target_pillar:
                        flow_pillar = pillar
                        break
                flow_palace = PILLAR_PALACE_CN.get(flow_pillar, "") if flow_pillar else ""
                # 检查是否是祖上宫-婚姻宫 刑（不区分顺序）
                palace_pair = frozenset([flow_palace, target_palace])
                is_zu_shang_marriage = palace_pair == frozenset(["祖上宫", "婚姻宫"])
                # 格式：宫位A-宫位B 地支字刑 [解释]
                punish_text = f"{flow_palace}-{target_palace} {flow_branch}{target_branch}刑"
                if is_zu_shang_marriage:
                    punish_text += " 成长过程中波折较多，压力偏大"
                issues.append(punish_text)
    
    # 打印原局天克地冲（不再打印，因为天克地冲已经包含在冲里了）
    # 注释掉，因为用户要求只打印冲和刑，天克地冲应该已经包含在冲里了
    # for tkdc in natal_tkdc:
    #     palace1 = PILLAR_PALACE_CN.get(tkdc.get("pillar1", ""), "")
    #     palace2 = PILLAR_PALACE_CN.get(tkdc.get("pillar2", ""), "")
    #     issues.append(f"{palace1}-{palace2} 天克地冲")
    
    # 打印原局模式（不再打印，用户要求只打印冲和刑）
    # for pattern_group in natal_patterns:
    #     ...
    
    if issues:
        print("\n—— 原局问题 ——")
        for issue in issues:
            print(issue)
    
    # ===== 婚恋结构提示 =====
    from .shishen import get_shishen, get_branch_main_gan, get_shishen_label, get_branch_shishen
    
    day_gan = bazi["day"]["gan"]
    marriage_hint = None
    
    if not is_male:
        # 女命：检查官杀混杂
        gan_shishens = []  # 天干十神列表
        zhi_shishens = []  # 地支主气十神列表
        
        # 检查天干（年/月/日/时干，不包括日干自己）
        for pillar in ("year", "month", "hour"):
            gan = bazi[pillar]["gan"]
            ss = get_shishen(day_gan, gan)
            if ss:
                gan_shishens.append(ss)
        
        # 检查地支主气（年/月/日/时支）
        for pillar in ("year", "month", "day", "hour"):
            zhi = bazi[pillar]["zhi"]
            main_gan = get_branch_main_gan(zhi)
            if main_gan:
                ss = get_shishen(day_gan, main_gan)
                if ss:
                    zhi_shishens.append(ss)
        
        # 检查天干中是否同时出现正官和七杀
        gan_has_zhengguan = "正官" in gan_shishens
        gan_has_qisha = "七杀" in gan_shishens
        if gan_has_zhengguan and gan_has_qisha:
            marriage_hint = "官杀混杂"
        
        # 检查地支主气中是否同时出现正官和七杀
        zhi_has_zhengguan = "正官" in zhi_shishens
        zhi_has_qisha = "七杀" in zhi_shishens
        if zhi_has_zhengguan and zhi_has_qisha:
            marriage_hint = "官杀混杂"
    else:
        # 男命：检查正偏财混杂
        gan_shishens = []  # 天干十神列表
        zhi_shishens = []  # 地支主气十神列表
        
        # 检查天干（年/月/日/时干，不包括日干自己）
        for pillar in ("year", "month", "hour"):
            gan = bazi[pillar]["gan"]
            ss = get_shishen(day_gan, gan)
            if ss:
                gan_shishens.append(ss)
        
        # 检查地支主气（年/月/日/时支）
        for pillar in ("year", "month", "day", "hour"):
            zhi = bazi[pillar]["zhi"]
            main_gan = get_branch_main_gan(zhi)
            if main_gan:
                ss = get_shishen(day_gan, main_gan)
                if ss:
                    zhi_shishens.append(ss)
        
        # 检查天干中是否同时出现正财和偏财
        gan_has_zhengcai = "正财" in gan_shishens
        gan_has_piancai = "偏财" in gan_shishens
        if gan_has_zhengcai and gan_has_piancai:
            marriage_hint = "正偏财混杂"
        
        # 检查地支主气中是否同时出现正财和偏财
        zhi_has_zhengcai = "正财" in zhi_shishens
        zhi_has_piancai = "偏财" in zhi_shishens
        if zhi_has_zhengcai and zhi_has_piancai:
            marriage_hint = "正偏财混杂"
    
    # ===== 天干五合争合/双合婚恋提醒（原局层） =====
    from .marriage_wuhe import detect_marriage_wuhe_hints
    
    # 收集原局四柱天干（包括日干）
    natal_gans = [
        bazi["year"]["gan"],
        bazi["month"]["gan"],
        bazi["day"]["gan"],  # 包括日干
        bazi["hour"]["gan"],
    ]
    
    natal_wuhe_hints = detect_marriage_wuhe_hints(natal_gans, day_gan, is_male)
    
    # 打印婚恋结构提示（混杂 + 五合提醒）
    marriage_hints_list = []
    if marriage_hint:
        marriage_hints_list.append(f"婚恋结构提示：{marriage_hint}，桃花多，易再婚，找不对配偶难走下去")
    
    # 添加五合提醒（原局层）
    for hint in natal_wuhe_hints:
        if marriage_hints_list:
            # 第一行已带"婚恋结构提示："，后续行缩进对齐
            marriage_hints_list.append(f"  婚恋结构提示：{hint['hint_text']}")
        else:
            marriage_hints_list.append(f"婚恋结构提示：{hint['hint_text']}")
    
    for hint_line in marriage_hints_list:
        print(hint_line)

    # ===== 大运 / 流年 运势 + 冲信息 =====
    luck = analyze_luck(birth_dt, is_male, yongshen_elements=yong, max_dayun=8)

    print("\n======== 大运 & 流年（按大运分组） ========\n")

    # 获取生扶力量和身强/身弱信息（用于用神互换提示）
    support_percent = result.get("support_percent", 0.0)
    strength_percent = result.get("strength_percent", 50.0)
    day_gan = bazi["day"]["gan"]

    for group in luck["groups"]:
        dy = group["dayun"]
        lns = group["liunian"]

        # 大运判词：用神=好运，非用神=一般
        if dy.get("zhi_good", False):
            label = "好运"
        else:
            label = "一般"
        gan_flag = "✓" if dy["gan_good"] else "×"
        zhi_flag = "✓" if dy["zhi_good"] else "×"

        print(
            f"【大运 {dy['index'] + 1}】 {dy['gan']}{dy['zhi']} "
            f"(起运年份 {dy['start_year']}, 虚龄 {dy['start_age']} 岁) → {label}  "
            f"[干 {dy['gan_element'] or '-'} {gan_flag} / "
            f"支 {dy['zhi_element'] or '-'} {zhi_flag}]"
        )
        
        # ===== 用神互换提示（只打印，不影响计算） =====
        from .yongshen_swap import should_print_yongshen_swap_hint, format_yongshen_swap_hint
        
        dayun_zhi = dy.get("zhi", "")
        hint_info = should_print_yongshen_swap_hint(
            day_gan=day_gan,
            strength_percent=strength_percent,
            support_percent=support_percent,
            yongshen_elements=yong,
            dayun_zhi=dayun_zhi,
        )
        if hint_info:
            hint_line = format_yongshen_swap_hint(hint_info)
            print(f"    {hint_line}")
        
        # 大运六合（只解释，不计分）
        dayun_liuhe_lines = []
        dayun_banhe_lines = []
        for ev in dy.get("harmonies_natal", []) or []:
            if ev.get("type") != "branch_harmony":
                continue
            subtype = ev.get("subtype")
            flow_branch = ev.get("flow_branch", dy.get("zhi", ""))
            if subtype not in ("liuhe", "banhe"):
                continue
            for t in ev.get("targets", []):
                palace = t.get("palace", "")
                target_branch = t.get("target_branch", "")
                if not palace or not target_branch:
                    continue
                if subtype == "liuhe":
                    # 例如：大运和夫妻宫合（午未合）
                    line = f"    大运和{palace}合（{flow_branch}{target_branch}合）"
                    dayun_liuhe_lines.append(line)
                elif subtype == "banhe":
                    # 例如：大运 与 夫妻宫 半合（巳酉半合）
                    line = f"    大运 与 {palace} 半合（{flow_branch}{target_branch}半合）"
                    dayun_banhe_lines.append(line)
        if dayun_liuhe_lines:
            for line in sorted(set(dayun_liuhe_lines)):
                print(line)
        if dayun_banhe_lines:
            for line in sorted(set(dayun_banhe_lines)):
                print(line)
        
        # 大运完整三合局
        for ev in dy.get("sanhe_complete", []) or []:
            if ev.get("subtype") != "sanhe":
                continue
            sources = ev.get("sources", [])
            if not sources:
                continue
            
            # 构建输出句子
            parts = []
            
            # 按三合局的顺序列出每个字的来源
            matched_branches = ev.get("matched_branches", [])
            for zhi in matched_branches:
                zhi_sources = [s for s in sources if s.get("zhi") == zhi]
                zhi_parts = []
                for src in zhi_sources:
                    src_type = src.get("source_type")
                    if src_type == "dayun":
                        zhi_parts.append(f"大运 {zhi}")
                    elif src_type == "liunian":
                        zhi_parts.append(f"流年 {zhi}")
                    elif src_type == "natal":
                        pillar_name = src.get("pillar_name", "")
                        palace = src.get("palace", "")
                        if pillar_name and palace:
                            zhi_parts.append(f"{pillar_name}（{palace}）{zhi}")
                        elif pillar_name:
                            zhi_parts.append(f"{pillar_name}{zhi}")
                
                if zhi_parts:
                    # 如果同一字在多个位置出现，用"和"连接
                    if len(zhi_parts) > 1:
                        parts.append("和".join(zhi_parts))
                    else:
                        parts.append(zhi_parts[0])
            
            # 结尾：三合局名称
            group = ev.get("group", "")
            matched_str = "".join(matched_branches)
            parts.append(f"{matched_str}三合{group}")
            
            # 用逗号连接各部分
            result = "，".join(parts)
            print(f"    {result}。")
        
        # 大运完整三会局
        for ev in dy.get("sanhui_complete", []) or []:
            if ev.get("subtype") != "sanhui":
                continue
            sources = ev.get("sources", [])
            if not sources:
                continue
            
            # 构建输出句子
            parts = []
            
            # 开头：大运信息
            dayun_index = ev.get("dayun_index")
            if dayun_index is not None:
                parts.append(f"大运{dayun_index + 1}")
            
            # 按三会局的顺序列出每个字的来源
            matched_branches = ev.get("matched_branches", [])
            for zhi in matched_branches:
                zhi_sources = [s for s in sources if s.get("zhi") == zhi]
                zhi_parts = []
                for src in zhi_sources:
                    src_type = src.get("source_type")
                    if src_type == "dayun":
                        zhi_parts.append(f"大运 {zhi}")
                    elif src_type == "liunian":
                        zhi_parts.append(f"流年 {zhi}")
                    elif src_type == "natal":
                        pillar_name = src.get("pillar_name", "")
                        palace = src.get("palace", "")
                        if pillar_name and palace:
                            zhi_parts.append(f"{pillar_name}（{palace}）{zhi}")
                        elif pillar_name:
                            zhi_parts.append(f"{pillar_name}{zhi}")
                
                if zhi_parts:
                    # 如果同一字在多个位置出现，分别列出（不合并）
                    for zp in zhi_parts:
                        parts.append(zp)
            
            # 结尾：三会局名称
            group = ev.get("group", "")
            matched_str = "".join(matched_branches)
            parts.append(f"{matched_str}三会{group.replace('会', '局')}")
            
            # 用空格连接各部分（按regression格式）
            result = " ".join(parts)
            print(f"    {result}。")
        
        # ===== 大运天干五合（只识别+打印，不影响风险） =====
        dayun_gan = dy.get("gan", "")
        if dayun_gan:
            dayun_shishen = get_shishen(day_gan, dayun_gan) or "-"
            # 大运入口使用"年干"格式（不是"年柱天干"），且本行不再重复打印“大运6，庚辰大运”
            dayun_gan_positions = []
            pillar_labels_dayun = {"year": "年干", "month": "月干", "day": "日干", "hour": "时干"}
            for pillar in ["year", "month", "day", "hour"]:
                gan = bazi[pillar]["gan"]
                shishen = get_shishen(day_gan, gan) or "-"
                dayun_gan_positions.append(GanPosition(
                    source="natal",
                    label=pillar_labels_dayun[pillar],
                    gan=gan,
                    shishen=shishen
                ))
            dayun_gan_positions.append(GanPosition(
                source="dayun",
                label="大运天干",
                gan=dayun_gan,
                shishen=dayun_shishen
            ))
            dayun_wuhe_events = detect_gan_wuhe(dayun_gan_positions)
            if dayun_wuhe_events:
                for ev in dayun_wuhe_events:
                    # 只打印涉及大运天干的五合
                    dayun_involved = any(pos.source == "dayun" for pos in ev["many_side"] + ev["few_side"])
                    if dayun_involved:
                        # 行内只保留“年干，月干，时干 乙 争合 大运天干 庚 ...”
                        line = format_gan_wuhe_event(ev, incoming_shishen=dayun_shishen)
                        print(f"    {line}")
        
        # ===== 天干五合争合/双合婚恋提醒（大运层） =====
        # 收集大运层天干：原局四柱天干 + 当前大运天干
        dayun_layer_gans = [
            bazi["year"]["gan"],
            bazi["month"]["gan"],
            bazi["day"]["gan"],
            bazi["hour"]["gan"],
        ]
        trigger_gans_dayun = []
        if dayun_gan:
            dayun_layer_gans.append(dayun_gan)
            trigger_gans_dayun.append(dayun_gan)  # 大运天干作为引动
        
        dayun_wuhe_hints = detect_marriage_wuhe_hints(dayun_layer_gans, day_gan, is_male, trigger_gans=trigger_gans_dayun)
        for hint in dayun_wuhe_hints:
            print(f"    婚恋变化提醒（如恋爱）：{hint['hint_text']}")
        
        # 大运本身与命局的冲
        for ev in dy.get("clashes_natal", []):
            if not ev:
                continue
            print("    命局冲（大运）：", _format_clash_natal(ev))
            
            # 打印大运与命局天克地冲详细信息
            tkdc_targets = ev.get("tkdc_targets", [])
            if tkdc_targets:
                from .config import PILLAR_PALACE
                flow_branch = ev.get("flow_branch", "")
                flow_gan = ev.get("flow_gan", "")
                for target in tkdc_targets:
                    target_pillar = target.get("pillar", "")
                    target_gan = target.get("target_gan", "")
                    palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                    pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                    print(f"      天克地冲：大运 {flow_gan}{flow_branch} 与 命局{pillar_name}（{palace}）{target_gan}{ev.get('target_branch', '')} 天克地冲")

        # 该大运下面的十个流年
        print("    —— 该大运对应的流年 ——")
        for ln in lns:
            # 计算年度标题行（新逻辑）
            total_risk = ln.get("total_risk_percent", 0.0)
            risk_from_gan = ln.get("risk_from_gan", 0.0)
            risk_from_zhi = ln.get("risk_from_zhi", 0.0)
            gan_element = ln.get("gan_element", "")
            zhi_element = ln.get("zhi_element", "")
            is_gan_yongshen = gan_element in yongshen_elements if gan_element else False
            is_zhi_yongshen = zhi_element in yongshen_elements if zhi_element else False
            
            title_line, should_print_suggestion = _calc_year_title_line(
                total_risk, risk_from_gan, risk_from_zhi,
                is_gan_yongshen, is_zhi_yongshen
            )
            
            print(
                f"    {ln['year']} 年 {ln['gan']}{ln['zhi']}（虚龄 {ln['age']} 岁）：{title_line}"
            )
            
            # 流年六合 / 半合（只解释，不计分）：流年支与原局四宫位
            liunian_lines = []
            for ev in ln.get("harmonies_natal", []) or []:
                if ev.get("type") != "branch_harmony":
                    continue
                subtype = ev.get("subtype")
                if subtype not in ("liuhe", "banhe"):
                    continue
                flow_branch = ev.get("flow_branch", ln.get("zhi", ""))
                for t in ev.get("targets", []):
                    palace = t.get("palace", "")
                    target_branch = t.get("target_branch", "")
                    if not palace or not target_branch:
                        continue
                    if subtype == "liuhe":
                        # 例如：流年和婚姻宫合（辰酉合）
                        pair_str = f"{flow_branch}{target_branch}合"
                        line = f"        流年和{palace}合（{pair_str}）"
                    else:
                        # 例如：流年 与 祖上宫 半合（巳酉半合）
                        matched = ev.get("matched_branches", [])
                        if len(matched) >= 2:
                            pair_str = f"{matched[0]}{matched[1]}半合"
                        else:
                            pair_str = f"{flow_branch}{target_branch}半合"
                        line = f"        流年 与 {palace} 半合（{pair_str}）"
                    liunian_lines.append(line)
            if liunian_lines:
                for line in sorted(set(liunian_lines)):
                    print(line)
            
            # 流年完整三合局（包括大运+流年+原局的情况）
            for ev in ln.get("sanhe_complete", []) or []:
                if ev.get("subtype") != "sanhe":
                    continue
                sources = ev.get("sources", [])
                if not sources:
                    continue
                
                # 构建输出句子
                parts = []
                
                # 按三合局的顺序列出每个字的来源
                matched_branches = ev.get("matched_branches", [])
                for zhi in matched_branches:
                    zhi_sources = [s for s in sources if s.get("zhi") == zhi]
                    zhi_parts = []
                    for src in zhi_sources:
                        src_type = src.get("source_type")
                        if src_type == "dayun":
                            zhi_parts.append(f"大运 {zhi}")
                        elif src_type == "liunian":
                            zhi_parts.append(f"流年 {zhi}")
                        elif src_type == "natal":
                            pillar_name = src.get("pillar_name", "")
                            palace = src.get("palace", "")
                            if pillar_name and palace:
                                zhi_parts.append(f"{pillar_name}（{palace}）{zhi}")
                            elif pillar_name:
                                zhi_parts.append(f"{pillar_name}{zhi}")
                    
                    if zhi_parts:
                        # 如果同一字在多个位置出现，分别列出（不合并），用逗号分隔
                        for zp in zhi_parts:
                            parts.append(zp)
                
                # 结尾：三合局名称
                group = ev.get("group", "")
                matched_str = "".join(matched_branches)
                parts.append(f"{matched_str}三合{group}")
                
                # 用逗号连接各部分
                result = "，".join(parts)
                print(f"        {result}。")
            
            # 流年完整三会局（包括大运+流年+原局的情况）
            for ev in ln.get("sanhui_complete", []) or []:
                if ev.get("subtype") != "sanhui":
                    continue
                sources = ev.get("sources", [])
                if not sources:
                    continue
                
                # 构建输出句子
                parts = []
                
                # 按三会局的顺序列出每个字的来源
                matched_branches = ev.get("matched_branches", [])
                for zhi in matched_branches:
                    zhi_sources = [s for s in sources if s.get("zhi") == zhi]
                    zhi_parts = []
                    for src in zhi_sources:
                        src_type = src.get("source_type")
                        if src_type == "dayun":
                            zhi_parts.append(f"大运 {zhi}")
                        elif src_type == "liunian":
                            zhi_parts.append(f"流年 {zhi}")
                        elif src_type == "natal":
                            pillar_name = src.get("pillar_name", "")
                            palace = src.get("palace", "")
                            if pillar_name and palace:
                                zhi_parts.append(f"{pillar_name}（{palace}）{zhi}")
                            elif pillar_name:
                                zhi_parts.append(f"{pillar_name}{zhi}")
                    
                    if zhi_parts:
                        # 如果同一字在多个位置出现，分别列出（不合并）
                        for zp in zhi_parts:
                            parts.append(zp)
                
                # 结尾：三会局名称
                group = ev.get("group", "")
                matched_str = "".join(matched_branches)
                parts.append(f"{matched_str}三会{group.replace('会', '局')}")
                
                # 用空格连接各部分
                result = " ".join(parts)
                print(f"        {result}。")
            
            # ===== 流年天干五合（只识别+打印，不影响风险） =====
            liunian_gan = ln.get("gan", "")
            if liunian_gan:
                liunian_shishen = get_shishen(day_gan, liunian_gan) or "-"
                # 流年入口使用"年干"格式（不是"年柱天干"），本行不再重复打印“2050年”等年份
                liunian_gan_positions = []
                pillar_labels_liunian = {"year": "年干", "month": "月干", "day": "日干", "hour": "时干"}
                for pillar in ["year", "month", "day", "hour"]:
                    gan = bazi[pillar]["gan"]
                    shishen = get_shishen(day_gan, gan) or "-"
                    liunian_gan_positions.append(GanPosition(
                        source="natal",
                        label=pillar_labels_liunian[pillar],
                        gan=gan,
                        shishen=shishen
                    ))
                # 添加大运天干
                dayun_gan = dy.get("gan", "")
                if dayun_gan:
                    dayun_shishen = get_shishen(day_gan, dayun_gan) or "-"
                    liunian_gan_positions.append(GanPosition(
                        source="dayun",
                        label="大运天干",
                        gan=dayun_gan,
                        shishen=dayun_shishen
                    ))
                # 添加流年天干
                liunian_gan_positions.append(GanPosition(
                    source="liunian",
                    label="流年天干",
                    gan=liunian_gan,
                    shishen=liunian_shishen
                ))
                liunian_wuhe_events = detect_gan_wuhe(liunian_gan_positions)
                if liunian_wuhe_events:
                    for ev in liunian_wuhe_events:
                        # 只打印涉及流年天干的五合
                        liunian_involved = any(pos.source == "liunian" for pos in ev["many_side"] + ev["few_side"])
                        if liunian_involved:
                            # 行内只保留"年干，月干，时干 乙 争合 流年天干，大运天干 庚 ..."
                            line = format_gan_wuhe_event(ev, incoming_shishen=liunian_shishen)
                            print(f"        {line}")
            
            # ===== 天干五合争合/双合婚恋提醒（流年层） =====
            # 收集流年层天干：原局四柱天干 + 当前大运天干 + 当前流年天干
            liunian_layer_gans = [
                bazi["year"]["gan"],
                bazi["month"]["gan"],
                bazi["day"]["gan"],
                bazi["hour"]["gan"],
            ]
            if dayun_gan:
                liunian_layer_gans.append(dayun_gan)
            if liunian_gan:
                liunian_layer_gans.append(liunian_gan)
            
            # 流年层只检查流年天干是否引动（避免重复打印大运层已打印的提醒）
            # 只有当流年天干是X或Y时才触发
            trigger_gans_liunian = []
            if liunian_gan:
                trigger_gans_liunian.append(liunian_gan)  # 只检查流年天干引动
            
            liunian_wuhe_hints = detect_marriage_wuhe_hints(liunian_layer_gans, day_gan, is_male, trigger_gans=trigger_gans_liunian)
            for hint in liunian_wuhe_hints:
                print(f"        婚恋变化提醒（如恋爱）：{hint['hint_text']}")
            
            # 事件区结束后固定只留 1 个空行
            print()
            
            # ===== 危险系数块（新格式） =====
            total_risk = ln.get("total_risk_percent", 0.0)
            risk_from_gan = ln.get("risk_from_gan", 0.0)
            risk_from_zhi = ln.get("risk_from_zhi", 0.0)
            tkdc_risk = ln.get("tkdc_risk_percent", 0.0)
            
            # 计算流年天干十神和用神
            liunian_gan = ln.get("gan", "")
            gan_shishen = get_shishen(day_gan, liunian_gan) if liunian_gan else None
            gan_element = ln.get("gan_element", "")
            is_gan_yongshen = gan_element in yongshen_elements if gan_element else False
            gan_label = get_shishen_label(gan_shishen, is_gan_yongshen) if gan_shishen else ""
            
            # 计算流年地支主气十神和用神
            liunian_zhi = ln.get("zhi", "")
            zhi_main_gan = get_branch_main_gan(liunian_zhi) if liunian_zhi else None
            zhi_shishen = get_shishen(day_gan, zhi_main_gan) if zhi_main_gan else None
            zhi_element = ln.get("zhi_element", "")
            is_zhi_yongshen = zhi_element in yongshen_elements if zhi_element else False
            zhi_label = get_shishen_label(zhi_shishen, is_zhi_yongshen) if zhi_shishen else ""
            
            # 打印总危险系数（带分隔线）
            print(f"        --- 总危险系数：{total_risk:.1f}% ---")
            
            # 如果 Y >= 40，打印建议行
            if should_print_suggestion:
                print("        建议：买保险/不投机/守法/不轻易辞职/控制情绪/三思后行")
            
            # 打印天干十神行
            gan_yongshen_str = "是" if is_gan_yongshen else "否"
            if gan_shishen:
                label_str = f"｜标签：{gan_label}" if gan_label else ""
                print(f"        天干 {liunian_gan}｜十神 {gan_shishen}｜用神 {gan_yongshen_str}{label_str}")
            else:
                print(f"        天干 {liunian_gan}｜十神 -｜用神 {gan_yongshen_str}")
            
            # 打印上半年危险系数
            print(f"        - 上半年危险系数（天干引起）：{risk_from_gan:.1f}%")
            
            # 打印地支十神行
            zhi_yongshen_str = "是" if is_zhi_yongshen else "否"
            if zhi_shishen:
                label_str = f"｜标签：{zhi_label}" if zhi_label else ""
                print(f"        地支 {liunian_zhi}｜十神 {zhi_shishen}｜用神 {zhi_yongshen_str}{label_str}")
            else:
                print(f"        地支 {liunian_zhi}｜十神 -｜用神 {zhi_yongshen_str}")
            
            # 打印下半年危险系数
            print(f"        - 下半年危险系数（地支引起）：{risk_from_zhi:.1f}%")
            
            # 打印天克地冲危险系数
            print(f"        - 天克地冲危险系数：{tkdc_risk:.1f}%")
            print("")
            
            # 组织所有事件
            all_events = ln.get("all_events", [])
            gan_events = []
            zhi_events = []
            static_events = []
            
            for ev in all_events:
                ev_type = ev.get("type", "")
                if ev_type in ("static_clash_activation", "static_punish_activation", "pattern_static_activation", "static_tkdc_activation"):
                    static_events.append(ev)
                elif ev_type == "pattern":
                    kind = ev.get("kind", "")
                    if kind == "gan":
                        gan_events.append(ev)
                    elif kind == "zhi":
                        zhi_events.append(ev)
                elif ev_type == "lineyun_bonus":
                    lineyun_bonus_gan = ev.get("lineyun_bonus_gan", 0.0)
                    lineyun_bonus_zhi = ev.get("lineyun_bonus_zhi", 0.0)
                    if lineyun_bonus_gan > 0.0:
                        gan_events.append(ev)
                    if lineyun_bonus_zhi > 0.0:
                        zhi_events.append(ev)
                elif ev_type in ("branch_clash", "dayun_liunian_branch_clash", "punishment"):
                    zhi_events.append(ev)
            
            # 打印上半年事件（天干相关）
            has_gan_events = gan_events or any(ev.get("type") == "pattern_static_activation" and (ev.get("risk_from_gan", 0.0) > 0.0) for ev in static_events)
            
            if has_gan_events:
                print("        上半年事件（天干引起）：")
                
                # 收集所有动态天干模式，按类型分组
                pattern_gan_dynamic = {}  # {pattern_type: [events]}
                for ev in gan_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "pattern":
                        pattern_type = ev.get("pattern_type", "")
                        if pattern_type not in pattern_gan_dynamic:
                            pattern_gan_dynamic[pattern_type] = []
                        pattern_gan_dynamic[pattern_type].append(ev)
                
                # 打印所有动态天干模式
                for pattern_type, events in pattern_gan_dynamic.items():
                    pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
                    total_dynamic_risk = 0.0
                    for ev in events:
                        risk = ev.get("risk_percent", 0.0)
                        total_dynamic_risk += risk
                        print(f"          模式（天干层）：{pattern_name}，风险 {risk:.1f}%")
                    
                    # 打印对应的静态模式激活（如果有）
                    static_risk_gan = 0.0
                    for static_ev in static_events:
                        if static_ev.get("type") == "pattern_static_activation":
                            static_pattern_type = static_ev.get("pattern_type", "")
                            if static_pattern_type == pattern_type:
                                static_risk_gan = static_ev.get("risk_from_gan", 0.0)
                                if static_risk_gan > 0.0:
                                    print(f"          静态模式激活（天干）：{pattern_name}，风险 {static_risk_gan:.1f}%")
                                    break
                    
                    # 打印总和
                    total_pattern_risk = total_dynamic_risk + static_risk_gan
                    if total_pattern_risk > 0.0:
                        print(f"          {pattern_name}总影响：动态 {total_dynamic_risk:.1f}% + 静态 {static_risk_gan:.1f}% = {total_pattern_risk:.1f}%")
                
                # 打印天干线运加成
                for ev in gan_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "lineyun_bonus":
                        lineyun_bonus_gan = ev.get("lineyun_bonus_gan", 0.0)
                        if lineyun_bonus_gan > 0.0:
                            print(f"          线运加成（天干）：{lineyun_bonus_gan:.1f}%")
                
                print("")
            
            # 打印下半年事件（地支相关）
            has_zhi_events = zhi_events or any(ev.get("type") in ("static_clash_activation", "static_punish_activation") or (ev.get("type") == "pattern_static_activation" and ev.get("risk_from_zhi", 0.0) > 0.0) for ev in static_events)
            # 检查是否有冲或刑
            if ln.get("clashes_natal") or ln.get("clashes_dayun"):
                has_zhi_events = True
            
            if has_zhi_events:
                print("        下半年事件（地支引起）：")
                
                # 先打印所有动态冲
                total_clash_dynamic = 0.0
                from .config import PILLAR_PALACE
                sanhe_sanhui_bonus_printed = False  # 标记是否已打印三合/三会逢冲额外加分
                
                # 流年与命局的冲
                for ev in ln.get("clashes_natal", []):
                    if not ev:
                        continue
                    flow_branch = ev.get("flow_branch", "")
                    target_branch = ev.get("target_branch", "")
                    base_power = ev.get("base_power_percent", 0.0)
                    grave_bonus = ev.get("grave_bonus_percent", 0.0)
                    clash_risk_zhi = base_power + grave_bonus
                    if clash_risk_zhi > 0.0:
                        total_clash_dynamic += clash_risk_zhi
                        targets = ev.get("targets", [])
                        target_info = []
                        for target in targets:
                            target_pillar = target.get("pillar", "")
                            palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                            pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                            target_info.append(f"{pillar_name}（{palace}）")
                        target_str = "、".join(target_info)
                        print(f"          冲：流年 {flow_branch} 冲 命局{target_str} {target_branch}，风险 {clash_risk_zhi:.1f}%")
                        
                        # 检查这个冲是否触发三合/三会逢冲额外加分（只打印一次）
                        if not sanhe_sanhui_bonus_printed:
                            sanhe_sanhui_bonus_ev = ln.get("sanhe_sanhui_clash_bonus_event")
                            if sanhe_sanhui_bonus_ev:
                                bonus_flow = sanhe_sanhui_bonus_ev.get("flow_branch", "")
                                bonus_target = sanhe_sanhui_bonus_ev.get("target_branch", "")
                                # 检查是否匹配当前冲
                                if (bonus_flow == flow_branch and bonus_target == target_branch) or \
                                   (bonus_flow == target_branch and bonus_target == flow_branch):
                                    _print_sanhe_sanhui_clash_bonus(sanhe_sanhui_bonus_ev)
                                    sanhe_sanhui_bonus_printed = True
                
                # 运年相冲
                for ev in ln.get("clashes_dayun", []):
                    if not ev:
                        continue
                    dayun_branch = ev.get("dayun_branch", "")
                    liunian_branch = ev.get("liunian_branch", "")
                    base_risk = ev.get("base_risk_percent", 0.0)
                    grave_bonus = ev.get("grave_bonus_percent", 0.0)
                    clash_risk_zhi = base_risk + grave_bonus
                    if clash_risk_zhi > 0.0:
                        total_clash_dynamic += clash_risk_zhi
                        dg = ev.get("dayun_shishen") or {}
                        lg = ev.get("liunian_shishen") or {}
                        dg_ss = dg.get("shishen") or "-"
                        lg_ss = lg.get("shishen") or "-"
                        print(f"          运年相冲：大运支 {dayun_branch}（{dg_ss}） 与 流年支 {liunian_branch}（{lg_ss}） 相冲，风险 {clash_risk_zhi:.1f}%")
                        
                        # 检查这个冲是否触发三合/三会逢冲额外加分（只打印一次）
                        if not sanhe_sanhui_bonus_printed:
                            sanhe_sanhui_bonus_ev = ln.get("sanhe_sanhui_clash_bonus_event")
                            if sanhe_sanhui_bonus_ev:
                                bonus_flow = sanhe_sanhui_bonus_ev.get("flow_branch", "")
                                bonus_target = sanhe_sanhui_bonus_ev.get("target_branch", "")
                                # 检查是否匹配当前冲（运年相冲中，flow_branch可能是dayun_branch，target_branch可能是liunian_branch）
                                if (bonus_flow == dayun_branch and bonus_target == liunian_branch) or \
                                   (bonus_flow == liunian_branch and bonus_target == dayun_branch):
                                    _print_sanhe_sanhui_clash_bonus(sanhe_sanhui_bonus_ev)
                                    sanhe_sanhui_bonus_printed = True
                
                # 打印静态冲激活（如果有）
                static_clash_risk = 0.0
                for static_ev in static_events:
                    if static_ev.get("type") == "static_clash_activation":
                        static_clash_risk = static_ev.get("risk_percent", 0.0)
                        if static_clash_risk > 0.0:
                            print(f"          静态冲激活：风险 {static_clash_risk:.1f}%")
                            break
                
                # 打印冲的总和（包含三合/三会逢冲额外加分）
                sanhe_sanhui_bonus_for_clash = ln.get("sanhe_sanhui_clash_bonus", 0.0)
                if total_clash_dynamic > 0.0 or static_clash_risk > 0.0 or sanhe_sanhui_bonus_for_clash > 0.0:
                    total_clash = total_clash_dynamic + static_clash_risk + sanhe_sanhui_bonus_for_clash
                    parts = []
                    if total_clash_dynamic > 0.0:
                        parts.append(f"动态 {total_clash_dynamic:.1f}%")
                    if static_clash_risk > 0.0:
                        parts.append(f"静态 {static_clash_risk:.1f}%")
                    if sanhe_sanhui_bonus_for_clash > 0.0:
                        parts.append(f"三合/三会逢冲 {sanhe_sanhui_bonus_for_clash:.1f}%")
                    parts_str = " + ".join(parts)
                    print(f"          冲总影响：{parts_str} = {total_clash:.1f}%")
                
                # 先打印所有动态刑
                total_punish_dynamic = 0.0
                for ev in zhi_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "punishment":
                        risk = ev.get("risk_percent", 0.0)
                        total_punish_dynamic += risk
                        flow_branch = ev.get("flow_branch", "")
                        target_branch = ev.get("target_branch", "")
                        targets = ev.get("targets", [])
                        target_info = []
                        for target in targets:
                            target_pillar = target.get("pillar", "")
                            palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                            pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                            target_info.append(f"{pillar_name}（{palace}）")
                        target_str = "、".join(target_info)
                        print(f"          刑：{flow_branch} 刑 {target_str} {target_branch}，风险 {risk:.1f}%")
                
                # 打印静态刑激活（如果有）
                static_punish_risk = 0.0
                for static_ev in static_events:
                    if static_ev.get("type") == "static_punish_activation":
                        static_punish_risk = static_ev.get("risk_percent", 0.0)
                        if static_punish_risk > 0.0:
                            print(f"          静态刑激活：风险 {static_punish_risk:.1f}%")
                            break
                
                # 打印刑的总和
                if total_punish_dynamic > 0.0 or static_punish_risk > 0.0:
                    total_punish = total_punish_dynamic + static_punish_risk
                    print(f"          刑总影响：动态 {total_punish_dynamic:.1f}% + 静态 {static_punish_risk:.1f}% = {total_punish:.1f}%")
                
                # 收集所有动态地支模式，按类型分组
                pattern_zhi_dynamic = {}  # {pattern_type: [events]}
                for ev in zhi_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "pattern":
                        pattern_type = ev.get("pattern_type", "")
                        if pattern_type not in pattern_zhi_dynamic:
                            pattern_zhi_dynamic[pattern_type] = []
                        pattern_zhi_dynamic[pattern_type].append(ev)
                
                # 打印所有动态地支模式
                for pattern_type, events in pattern_zhi_dynamic.items():
                    pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
                    total_dynamic_risk = 0.0
                    for ev in events:
                        risk = ev.get("risk_percent", 0.0)
                        total_dynamic_risk += risk
                        print(f"          模式（地支层）：{pattern_name}，风险 {risk:.1f}%")
                    
                    # 打印对应的静态模式激活（如果有）
                    static_risk_zhi = 0.0
                    for static_ev in static_events:
                        if static_ev.get("type") == "pattern_static_activation":
                            static_pattern_type = static_ev.get("pattern_type", "")
                            if static_pattern_type == pattern_type:
                                static_risk_zhi = static_ev.get("risk_from_zhi", 0.0)
                                if static_risk_zhi > 0.0:
                                    print(f"          静态模式激活（地支）：{pattern_name}，风险 {static_risk_zhi:.1f}%")
                                    break
                    
                    # 打印总和
                    total_pattern_risk = total_dynamic_risk + static_risk_zhi
                    if total_pattern_risk > 0.0:
                        print(f"          {pattern_name}总影响：动态 {total_dynamic_risk:.1f}% + 静态 {static_risk_zhi:.1f}% = {total_pattern_risk:.1f}%")
                
                # 打印地支线运加成
                for ev in zhi_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "lineyun_bonus":
                        lineyun_bonus_zhi = ev.get("lineyun_bonus_zhi", 0.0)
                        if lineyun_bonus_zhi > 0.0:
                            print(f"          线运加成（地支）：{lineyun_bonus_zhi:.1f}%")
                
                print("")
            
            # 打印天克地冲事件（单独列出）
            if tkdc_risk > 0.0:
                print("        天克地冲事件：")
                
                # 检查流年与命局的冲中的天克地冲
                for ev_clash in ln.get("clashes_natal", []):
                    if not ev_clash:
                        continue
                    tkdc_targets = ev_clash.get("tkdc_targets", [])
                    if tkdc_targets:
                        from .config import PILLAR_PALACE
                        flow_branch = ev_clash.get("flow_branch", "")
                        flow_gan = ev_clash.get("flow_gan", "")
                        for target in tkdc_targets:
                            target_pillar = target.get("pillar", "")
                            target_gan = target.get("target_gan", "")
                            palace = PILLAR_PALACE.get(target_pillar, target_pillar)
                            pillar_name = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(target_pillar, target_pillar)
                            # 计算该柱的天克地冲加成
                            if target_pillar == "year":
                                tkdc_per_pillar = 0.0  # 年柱不加成
                            elif target_pillar == "day":
                                tkdc_per_pillar = 20.0  # 日柱20%
                            else:
                                tkdc_per_pillar = 10.0  # 其他柱10%
                            if tkdc_per_pillar > 0.0:
                                print(f"          天克地冲：流年 {flow_gan}{flow_branch} 与 命局{pillar_name}（{palace}）{target_gan}{ev_clash.get('target_branch', '')} 天克地冲，风险 {tkdc_per_pillar:.1f}%")
                
                # 检查运年相冲中的天克地冲
                for ev_clash in ln.get("clashes_dayun", []):
                    if not ev_clash:
                        continue
                    if ev_clash.get("is_tian_ke_di_chong", False):
                        dayun_gan = ev_clash.get("dayun_gan", "")
                        liunian_gan = ev_clash.get("liunian_gan", "")
                        dayun_branch = ev_clash.get("dayun_branch", "")
                        liunian_branch = ev_clash.get("liunian_branch", "")
                        # 运年天克地冲总共20%（基础10% + 运年额外10%）
                        print(f"          天克地冲：大运 {dayun_gan}{dayun_branch} 与 流年 {liunian_gan}{liunian_branch} 天克地冲，风险 20.0%")
                
                # 打印静态天克地冲激活
                for ev in static_events:
                    if ev.get("type") == "static_tkdc_activation":
                        risk_tkdc_static = ev.get("risk_from_gan", 0.0)  # 静态天克地冲全部计入tkdc_risk
                        if risk_tkdc_static > 0.0:
                            print(f"          静态天克地冲激活：风险 {risk_tkdc_static:.1f}%")
                
                print("")


        print("")  # 每个大运分隔一行
