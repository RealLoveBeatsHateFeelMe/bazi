# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

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
    punishment_events = [ev for ev in all_events if ev.get("type") == "punishment"]
    print(f"刑事件数量: {len(punishment_events)}")
    for ev in punishment_events:
        print(f"  {ev.get('flow_branch')} {ev.get('target_branch')} risk={ev.get('risk_percent', 0.0)}% targets={[t.get('pillar') for t in ev.get('targets', [])]}")
    
    # 检查原局刑
    from bazi.punishment import detect_natal_clashes_and_punishments
    conflicts = detect_natal_clashes_and_punishments(bazi)
    natal_punishments = conflicts.get("punishments", [])
    print(f"\n原局刑: {len(natal_punishments)}个")
    for p in natal_punishments:
        print(f"  {p.get('flow_branch')} {p.get('target_branch')} risk={p.get('risk_percent', 0.0)}%")

