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
print(f"\n检测到的原局刑: {len(punishments)}个")
for i, p in enumerate(punishments):
    flow = p.get("flow_branch")
    target = p.get("target_branch")
    risk = p.get("risk_percent", 0.0)
    targets = p.get("targets", [])
    print(f"  {i+1}. {flow} {target} risk={risk}% targets={[t.get('pillar') for t in targets]}")

