# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import detect_natal_clashes_and_punishments, SELF_PUNISH_PAIRS, ALL_PUNISH_PAIRS

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
    is_self = (flow, target) in SELF_PUNISH_PAIRS
    in_all = (flow, target) in ALL_PUNISH_PAIRS
    print(f"  {i+1}. {flow} {target} risk={risk}% is_self={is_self} in_all={in_all}")
    print(f"      targets: {[t.get('pillar') for t in targets]}")
    # 找到flow和target对应的柱
    flow_pillar = None
    for pillar in ("year", "month", "day", "hour"):
        if bazi[pillar]["zhi"] == flow:
            flow_pillar = pillar
            break
    target_pillar = targets[0].get("pillar", "") if targets else None
    print(f"      flow_pillar: {flow_pillar}, target_pillar: {target_pillar}")

