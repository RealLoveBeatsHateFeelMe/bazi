# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import detect_natal_clashes_and_punishments

# 检查例A：酉酉自刑
print("检查例A：1981-09-15 10:00")
dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"八字: {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

conflicts = detect_natal_clashes_and_punishments(bazi)
punishments = conflicts.get("punishments", [])
print(f"\n检测到的刑: {len(punishments)}个")
total_risk = 0.0
for p in punishments:
    flow = p.get("flow_branch", "")
    target = p.get("target_branch", "")
    risk = p.get("risk_percent", 0.0)
    is_grave = p.get("is_grave", False)
    print(f"  {flow} {target} risk={risk}% is_grave={is_grave}")
    total_risk += risk
print(f"总风险: {total_risk}%")

# 检查例B 2021年的刑风险
print("\n检查例B 2021年：2007-01-28 12:00")
from bazi.luck import analyze_luck
dt2 = datetime(2007, 1, 28, 12, 0)
basic2 = analyze_basic(dt2)
yongshen_elements = basic2.get("yongshen_elements", [])
luck = analyze_luck(dt2, is_male=True, yongshen_elements=yongshen_elements)

liunian_2021 = None
for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2021:
            liunian_2021 = liunian
            break
    if liunian_2021:
        break

if liunian_2021:
    all_events = liunian_2021.get("all_events", [])
    punishment_events = [ev for ev in all_events if ev.get("type") == "punishment"]
    punishment_risk = sum(ev.get("risk_percent", 0.0) for ev in punishment_events)
    print(f"流年2021年的刑风险: {punishment_risk}%")
    print(f"刑事件数量: {len(punishment_events)}")
    for ev in punishment_events:
        print(f"  {ev.get('flow_branch')} {ev.get('target_branch')} risk={ev.get('risk_percent', 0.0)}%")

