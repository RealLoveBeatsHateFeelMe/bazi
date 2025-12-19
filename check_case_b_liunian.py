# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import detect_branch_punishments

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"例B八字: {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 检查原局中的戌
print("\n原局中的戌:")
for pillar in ("year", "month", "day", "hour"):
    if bazi[pillar]["zhi"] == "戌":
        print(f"  {pillar}: {bazi[pillar]['gan']}{bazi[pillar]['zhi']}")

# 检查流年丑检测到的刑事件
events = detect_branch_punishments(bazi, "丑", "liunian", 2021, "辛丑")
print(f"\n流年丑检测到的刑事件: {len(events)}个")
total_risk = 0.0
for ev in events:
    risk = ev.get("risk_percent", 0.0)
    total_risk += risk
    targets = ev.get("targets", [])
    print(f"  {ev.get('flow_branch')} {ev.get('target_branch')} risk={risk}% targets={[t.get('pillar') for t in targets]}")
print(f"总风险: {total_risk}%")
print(f"期望: 12%（两次丑戌刑，各6%），实际: {total_risk}%")

