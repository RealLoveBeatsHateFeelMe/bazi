# -*- coding: utf-8 -*-
"""命令行交互：输入生日 → 八字 + 日主 + 用神 + 大运/流年好运 + 冲的信息。"""

from __future__ import annotations

from datetime import datetime

from .lunar_engine import analyze_basic
from .luck import analyze_luck


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





def run_cli() -> None:
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
    if dominant_traits:
        # 辅助：按 group 索引
        trait_by_group = {t.get("group"): t for t in dominant_traits}

        def _stem_hits(trait: dict) -> int:
            detail = trait.get("detail") or []
            hits = sum(d.get("stems_visible_count", 0) for d in detail)
            return min(hits, 3)

        # 主要性格：满足 total_percent>=35 或 stem_hits>=2
        major = []
        for t in dominant_traits:
            total_percent = t.get("total_percent", 0.0)
            hits = _stem_hits(t)
            if total_percent >= 35.0 or hits >= 2:
                major.append(t)

        if major:
            print("\n—— 主要性格 ——")
            for trait in major:
                group = trait.get("group", "-")
                total_percent = trait.get("total_percent", 0.0)
                mix_label = trait.get("mix_label", "")
                hits = _stem_hits(trait)

                # 子类占比串
                detail = trait.get("detail") or []
                subs_str = "；子类占比 " + "，".join(
                    f"{d.get('name')} {d.get('percent', 0.0):.1f}%"
                    for d in detail
                )
                print(
                    f"{group}（{total_percent:.1f}%）：{mix_label}；"
                    f"三天干命中 {hits}/3{subs_str}"
                )

        # 其他性格：五大类全量（含 0%）
        print("\n—— 其他性格 ——")
        all_groups = ["财", "印", "官杀", "食伤", "比劫"]
        for g in all_groups:
            trait = trait_by_group.get(g, {})
            total_percent = trait.get("total_percent", 0.0)
            mix_label = trait.get("mix_label", "无")
            hits = 0
            detail = trait.get("detail") or []
            if detail:
                hits = min(sum(d.get("stems_visible_count", 0) for d in detail), 3)
                subs_str = "；子类占比 " + "，".join(
                    f"{d.get('name')} {d.get('percent', 0.0):.1f}%"
                    for d in detail
                )
            else:
                subs_str = "；子类占比 —"

            print(
                f"{g}（{total_percent:.1f}%）：{mix_label}；"
                f"三天干命中 {hits}/3{subs_str}"
            )

    print("\n—— 全局五行占比（八个字）——")
    global_dist = result["global_element_percentages"]
    for e in ["木", "火", "土", "金", "水"]:
        print(f"{e}：{global_dist.get(e, 0.0):.2f}%")

    # 合并用神信息打印
    print("\n—— 用神信息 ——")
    yong = result["yongshen_elements"]
    print("用神五行（候选）：", "、".join(yong))
    
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
    
    # 原局问题打印
    from .clash import detect_natal_tian_ke_di_chong
    
    natal_conflicts = result.get("natal_conflicts", {})
    natal_clashes = natal_conflicts.get("clashes", [])
    natal_punishments = natal_conflicts.get("punishments", [])
    natal_tkdc = detect_natal_tian_ke_di_chong(bazi)
    natal_patterns = result.get("natal_patterns", [])
    
    issues = []
    
    # 打印原局冲
    for clash in natal_clashes:
        targets = clash.get("targets", [])
        if targets:
            palaces = sorted({PILLAR_PALACE_CN.get(t.get("pillar", ""), "") for t in targets if t.get("pillar")})
            palaces_str = "、".join(palaces) if palaces else ""
            flow_branch = clash.get("flow_branch", "")
            target_branch = clash.get("target_branch", "")
            base_power = clash.get("base_power_percent", 0.0)
            grave_bonus = clash.get("grave_bonus_percent", 0.0)
            risk = base_power + grave_bonus
            if risk > 0.0:
                issues.append(f"{palaces_str} 冲 {risk:.1f}%")
    
    # 打印原局刑
    for punish in natal_punishments:
        targets = punish.get("targets", [])
        if targets:
            target_palace = PILLAR_PALACE_CN.get(targets[0].get("pillar", ""), "")
            flow_branch = punish.get("flow_branch", "")
            target_branch = punish.get("target_branch", "")
            # 找到flow_branch和target_branch对应的柱
            flow_pillar = None
            target_pillar = targets[0].get("pillar", "")
            for pillar in ("year", "month", "day", "hour"):
                if bazi[pillar]["zhi"] == flow_branch and pillar != target_pillar:
                    flow_pillar = pillar
                    break
            # 如果是自刑（flow_branch == target_branch），flow_pillar就是target_pillar
            if flow_branch == target_branch:
                flow_pillar = target_pillar
            flow_palace = PILLAR_PALACE_CN.get(flow_pillar, "") if flow_pillar else ""
            risk = punish.get("risk_percent", 0.0)
            if risk > 0.0:
                issues.append(f"{flow_palace}-{target_palace} 刑 {risk:.1f}%")
    
    # 打印原局天克地冲
    for tkdc in natal_tkdc:
        palace1 = PILLAR_PALACE_CN.get(tkdc.get("pillar1", ""), "")
        palace2 = PILLAR_PALACE_CN.get(tkdc.get("pillar2", ""), "")
        risk = tkdc.get("risk_percent", 0.0)
        if risk > 0.0:
            issues.append(f"{palace1}-{palace2} 天克地冲 {risk:.1f}%")
    
    # 打印原局模式
    for pattern_group in natal_patterns:
        pattern_type = pattern_group.get("pattern_type", "")
        pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
        pairs = pattern_group.get("pairs", [])
        if pairs:
            # 收集涉及的宫位
            palaces_set = set()
            for pair in pairs:
                pos1 = pair.get("pos1", {})
                pos2 = pair.get("pos2", {})
                pillar1 = pos1.get("pillar", "")
                pillar2 = pos2.get("pillar", "")
                if pillar1 in ("year", "month", "day", "hour"):
                    palaces_set.add(PILLAR_PALACE_CN.get(pillar1, ""))
                if pillar2 in ("year", "month", "day", "hour"):
                    palaces_set.add(PILLAR_PALACE_CN.get(pillar2, ""))
            palaces_str = "、".join(sorted(palaces_set)) if palaces_set else ""
            # 模式风险：天干层15%，地支层15%，如果涉及月柱则25%
            risk = 15.0  # 默认15%
            for pair in pairs:
                pos1 = pair.get("pos1", {})
                pos2 = pair.get("pos2", {})
                if (pos1.get("pillar") == "month" or pos2.get("pillar") == "month") and pos1.get("kind") == "zhi" and pos2.get("kind") == "zhi":
                    risk = 25.0
                    break
            issues.append(f"{pattern_name} {palaces_str} {risk:.1f}%")
    
    if issues:
        print("原局问题：" + "，".join(issues))

    # ===== 大运 / 流年 运势 + 冲信息 =====
    luck = analyze_luck(birth_dt, is_male, yongshen_elements=yong, max_dayun=8)

    print("\n======== 大运 & 流年（按大运分组） ========\n")

    for group in luck["groups"]:
        dy = group["dayun"]
        lns = group["liunian"]

        label = "好运" if dy["is_good"] else "坏运"
        gan_flag = "✓" if dy["gan_good"] else "×"
        zhi_flag = "✓" if dy["zhi_good"] else "×"

        print(
            f"【大运 {dy['index'] + 1}】 {dy['gan']}{dy['zhi']} "
            f"(起运年份 {dy['start_year']}, 虚龄 {dy['start_age']} 岁) → {label}  "
            f"[干 {dy['gan_element'] or '-'} {gan_flag} / "
            f"支 {dy['zhi_element'] or '-'} {zhi_flag}]"
        )
        
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
            parts.append(f"{matched_str}三会{group}")
            
            # 用空格连接各部分（按regression格式）
            result = " ".join(parts)
            print(f"    {result}。")
        
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
            first_label = "好运" if ln["first_half_good"] else "坏运"
            second_label = "好运" if ln["second_half_good"] else "坏运"

            print(
                f"    {ln['year']} 年 {ln['gan']}{ln['zhi']}（虚龄 {ln['age']} 岁）："
                f"上半年 {first_label}，下半年 {second_label}"
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
                
                # 开头：流年信息
                liunian_year = ev.get("liunian_year")
                if liunian_year:
                    parts.append(f"{liunian_year}年")
                
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
                parts.append(f"{matched_str}三会{group}")
                
                # 用空格连接各部分
                result = " ".join(parts)
                print(f"        {result}。")
            
            # 先打印危险系数
            total_risk = ln.get("total_risk_percent", 0.0)
            risk_from_gan = ln.get("risk_from_gan", 0.0)
            risk_from_zhi = ln.get("risk_from_zhi", 0.0)
            tkdc_risk = ln.get("tkdc_risk_percent", 0.0)
            print(f"        总危险系数：{total_risk:.1f}%")
            print(f"        上半年危险系数（天干引起）：{risk_from_gan:.1f}%")
            print(f"        下半年危险系数（地支引起）：{risk_from_zhi:.1f}%")
            print(f"        天克地冲危险系数：{tkdc_risk:.1f}%")
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
                
                # 打印静态冲激活（如果有）
                static_clash_risk = 0.0
                for static_ev in static_events:
                    if static_ev.get("type") == "static_clash_activation":
                        static_clash_risk = static_ev.get("risk_percent", 0.0)
                        if static_clash_risk > 0.0:
                            print(f"          静态冲激活：风险 {static_clash_risk:.1f}%")
                            break
                
                # 打印冲的总和
                if total_clash_dynamic > 0.0 or static_clash_risk > 0.0:
                    total_clash = total_clash_dynamic + static_clash_risk
                    print(f"          冲总影响：动态 {total_clash_dynamic:.1f}% + 静态 {static_clash_risk:.1f}% = {total_clash:.1f}%")
                
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
