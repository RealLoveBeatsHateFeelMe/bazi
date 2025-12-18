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

    print("\n—— 用神建议 ——")
    yong = result["yongshen_elements"]
    print("用神五行（候选）：", "、".join(yong))

    # 用神（五行→十神）
    yong_ss = result.get("yongshen_shishen") or []
    if yong_ss:
        print("\n—— 用神（五行→十神） ——")
        for entry in yong_ss:
            elem = entry.get("element", "-")
            cats = entry.get("categories") or []
            specifics = entry.get("shishens") or []
            cats_str = "、".join(cats) if cats else "-"
            specs_str = "、".join(specifics) if specifics else "-"
            print(f"{elem}：{cats_str}（{specs_str}）")

    # 用神落点字
    yong_tokens = result.get("yongshen_tokens") or []
    if yong_tokens:
        print("\n—— 用神落点字 ——")
        pillar_label = {
            "year": "年柱",
            "month": "月柱",
            "day": "日柱",
            "hour": "时柱",
        }
        kind_label = {"gan": "干", "zhi": "支"}
        tokens_by_elem = {e.get("element"): e.get("positions", []) for e in yong_tokens}

        for elem in yong:
            positions = tokens_by_elem.get(elem, [])
            if not positions:
                print(f"{elem}：—")
                continue
            parts = []
            for pos in positions:
                pillar = pillar_label.get(pos.get("pillar", ""), pos.get("pillar", ""))
                kind = kind_label.get(pos.get("kind", ""), pos.get("kind", ""))
                char = pos.get("char", "?")
                ss = pos.get("shishen", "-")
                parts.append(f"{pillar}{kind} {char}({ss})")
            print(f"{elem}：" + "，".join(parts))

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

        # 大运本身与命局的冲
        for ev in dy.get("clashes_natal", []):
            if not ev:
                continue
            print("    命局冲（大运）：", _format_clash_natal(ev))

        # 该大运下面的十个流年
        print("    —— 该大运对应的流年 ——")
        for ln in lns:
            first_label = "好运" if ln["first_half_good"] else "坏运"
            second_label = "好运" if ln["second_half_good"] else "坏运"

            print(
                f"    {ln['year']} 年 {ln['gan']}{ln['zhi']}（虚龄 {ln['age']} 岁）："
                f"上半年 {first_label}，下半年 {second_label}"
            )

            # 流年支 与 命局地支 的冲
            for ev in ln.get("clashes_natal", []):
                if not ev:
                    continue
                print("        命局冲（流年）：", _format_clash_natal(ev))

            # 大运支 与 流年支 之间的冲（附带十神）
            for ev in ln.get("clashes_dayun", []):
                if not ev:
                    continue
                dg = ev.get("dayun_shishen") or {}
                lg = ev.get("liunian_shishen") or {}
                dg_ss = dg.get("shishen") or "-"
                lg_ss = lg.get("shishen") or "-"
                print(
                    f"        运年相冲：大运支 {ev['dayun_branch']}（{dg_ss}） 与 "
                    f"流年支 {ev['liunian_branch']}（{lg_ss}） 相冲"
                )
            
            # 打印危险系数（按新顺序）
            total_risk = ln.get("total_risk_percent", 0.0)
            risk_from_gan = ln.get("risk_from_gan", 0.0)
            risk_from_zhi = ln.get("risk_from_zhi", 0.0)
            print(f"        总危险系数：{total_risk:.1f}%")
            print(f"        上半年危险系数（天干引起）：{risk_from_gan:.1f}%")
            
            # 打印上半年事件（天干相关）
            all_events = ln.get("all_events", [])
            gan_events = []
            zhi_events = []
            static_events = []
            
            for ev in all_events:
                ev_type = ev.get("type", "")
                if ev_type in ("static_clash_activation", "static_punish_activation", "pattern_static_activation"):
                    static_events.append(ev)
                elif ev_type == "pattern":
                    kind = ev.get("kind", "")
                    if kind == "gan":
                        gan_events.append(ev)
                    elif kind == "zhi":
                        zhi_events.append(ev)
                elif ev_type == "lineyun_bonus":
                    lineyun_bonus_gan = ev.get("lineyun_bonus_gan", 0.0)
                    if lineyun_bonus_gan > 0.0:
                        gan_events.append(ev)
                elif ev_type in ("branch_clash", "dayun_liunian_branch_clash", "punishment"):
                    zhi_events.append(ev)
            
            # 打印上半年事件（天干相关）
            if gan_events or any(ev.get("type") == "pattern_static_activation" and ev.get("risk_from_gan", 0.0) > 0.0 for ev in static_events):
                print("        上半年事件（天干）：")
                for ev in gan_events:
                    ev_type = ev.get("type", "")
                    risk = ev.get("risk_percent", 0.0)
                    if ev_type == "pattern":
                        pattern_type = ev.get("pattern_type", "")
                        pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
                        print(f"          模式（天干层）：{pattern_name}，风险 {risk:.1f}%")
                    elif ev_type == "lineyun_bonus":
                        lineyun_bonus_gan = ev.get("lineyun_bonus_gan", 0.0)
                        if lineyun_bonus_gan > 0.0:
                            print(f"          线运加成（天干）：{lineyun_bonus_gan:.1f}%")
                
                # 打印静态模式激活的天干部分
                for ev in static_events:
                    if ev.get("type") == "pattern_static_activation":
                        risk_from_gan_static = ev.get("risk_from_gan", 0.0)
                        if risk_from_gan_static > 0.0:
                            pattern_type = ev.get("pattern_type", "")
                            pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
                            print(f"          静态模式激活（天干）：{pattern_name}，风险 {risk_from_gan_static:.1f}%")
            
            print(f"        下半年危险系数（地支引起）：{risk_from_zhi:.1f}%")
            
            # 打印下半年事件（地支相关）
            if zhi_events or any(ev.get("type") in ("static_clash_activation", "static_punish_activation") or (ev.get("type") == "pattern_static_activation" and ev.get("risk_from_zhi", 0.0) > 0.0) for ev in static_events):
                print("        下半年事件（地支）：")
                for ev in zhi_events:
                    ev_type = ev.get("type", "")
                    risk = ev.get("risk_percent", 0.0)
                    if ev_type == "branch_clash":
                        print(f"          冲：{ev.get('flow_branch')}{ev.get('target_branch')}，风险 {risk:.1f}%")
                    elif ev_type == "dayun_liunian_branch_clash":
                        print(f"          运年相冲：{ev.get('dayun_branch')}{ev.get('liunian_branch')}，风险 {risk:.1f}%")
                    elif ev_type == "punishment":
                        print(f"          刑：{ev.get('flow_branch')}{ev.get('target_branch')}，风险 {risk:.1f}%")
                    elif ev_type == "pattern":
                        pattern_type = ev.get("pattern_type", "")
                        pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
                        print(f"          模式（地支层）：{pattern_name}，风险 {risk:.1f}%")
                    elif ev_type == "lineyun_bonus":
                        lineyun_bonus_zhi = ev.get("lineyun_bonus_zhi", 0.0)
                        if lineyun_bonus_zhi > 0.0:
                            print(f"          线运加成（地支）：{lineyun_bonus_zhi:.1f}%")
                
                # 打印静态激活事件（地支相关）
                for ev in static_events:
                    ev_type = ev.get("type", "")
                    if ev_type == "static_clash_activation":
                        risk = ev.get("risk_percent", 0.0)
                        print(f"          静态冲激活：风险 {risk:.1f}%")
                    elif ev_type == "static_punish_activation":
                        risk = ev.get("risk_percent", 0.0)
                        print(f"          静态刑激活：风险 {risk:.1f}%")
                    elif ev_type == "pattern_static_activation":
                        risk_from_zhi_static = ev.get("risk_from_zhi", 0.0)
                        if risk_from_zhi_static > 0.0:
                            pattern_type = ev.get("pattern_type", "")
                            pattern_name = "伤官见官" if pattern_type == "hurt_officer" else "枭神夺食" if pattern_type == "pianyin_eatgod" else pattern_type
                            print(f"          静态模式激活（地支）：{pattern_name}，风险 {risk_from_zhi_static:.1f}%")


        print("")  # 每个大运分隔一行
