# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"例A八字: {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

yongshen_elements = basic.get("yongshen_elements", [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)

liunian_2017 = None
for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2017:
            liunian_2017 = liunian
            break
    if liunian_2017:
        break

if liunian_2017:
    print(f"\n2017年流年: {liunian_2017.get('gan')}{liunian_2017.get('zhi')}")
    all_events = liunian_2017.get("all_events", [])
    punishment_events = [ev for ev in all_events if ev.get("type") == "punishment"]
    print(f"刑事件数量: {len(punishment_events)}")
    for ev in punishment_events:
        targets = ev.get("targets", [])
        print(f"  {ev.get('flow_branch')} {ev.get('target_branch')} risk={ev.get('risk_percent', 0.0)}% targets={[t.get('pillar') for t in targets]}")
    
    # 检查原局刑
    from bazi.punishment import detect_natal_clashes_and_punishments
    conflicts = detect_natal_clashes_and_punishments(bazi)
    natal_punishments = conflicts.get("punishments", [])
    print(f"\n原局刑: {len(natal_punishments)}个")
    for p in natal_punishments:
        print(f"  {p.get('flow_branch')} {p.get('target_branch')} risk={p.get('risk_percent', 0.0)}%")
    
    # 计算总风险
    total_risk = liunian_2017.get("total_risk_percent", 0.0)
    risk_from_zhi = liunian_2017.get("risk_from_zhi", 0.0)
    print(f"\n总风险: {total_risk}%")
    print(f"地支风险: {risk_from_zhi}%")
    print(f"期望: 流年刑10%（酉与年柱、月柱都自刑，各5%），静态刑5%，总共15%")
