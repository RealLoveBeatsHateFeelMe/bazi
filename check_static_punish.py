# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck
from bazi.punishment import detect_natal_clashes_and_punishments

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"例B八字: {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

yongshen_elements = basic.get("yongshen_elements", [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)

liunian_2021 = None
for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2021:
            liunian_2021 = liunian
            break
    if liunian_2021:
        break

if liunian_2021:
    print(f"\n2021年流年: {liunian_2021.get('gan')}{liunian_2021.get('zhi')}")
    all_events = liunian_2021.get("all_events", [])
    
    # 检查动态刑
    punishment_events = [ev for ev in all_events if ev.get("type") == "punishment"]
    print(f"动态刑事件: {len(punishment_events)}个")
    for ev in punishment_events:
        print(f"  {ev.get('flow_branch')} {ev.get('target_branch')} risk={ev.get('risk_percent', 0.0)}%")
    
    # 检查静态刑激活
    static_punish_events = [ev for ev in all_events if ev.get("type") == "static_punish_activation"]
    print(f"静态刑激活事件: {len(static_punish_events)}个")
    for ev in static_punish_events:
        print(f"  {ev.get('flow_branch')} {ev.get('target_branch')} risk={ev.get('risk_percent', 0.0)}%")
    
    # 检查原局刑
    conflicts = detect_natal_clashes_and_punishments(bazi)
    natal_punishments = conflicts.get("punishments", [])
    print(f"\n原局刑: {len(natal_punishments)}个")
    for p in natal_punishments:
        print(f"  {p.get('flow_branch')} {p.get('target_branch')} risk={p.get('risk_percent', 0.0)}%")
    
    # 检查静态刑激活逻辑
    zhi_ln = liunian_2021.get("zhi")
    print(f"\n流年地支: {zhi_ln}")
    print("检查静态刑激活条件:")
    for natal_punish_ev in natal_punishments:
        natal_flow = natal_punish_ev.get("flow_branch")
        natal_target = natal_punish_ev.get("target_branch")
        ln_punish_targets = {ev.get("target_branch") for ev in punishment_events}
        condition1 = zhi_ln == natal_flow and natal_target in ln_punish_targets
        condition2 = zhi_ln == natal_target and natal_flow in ln_punish_targets
        print(f"  原局刑 {natal_flow}-{natal_target}: condition1={condition1}, condition2={condition2}, ln_punish_targets={ln_punish_targets}")

