# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import detect_natal_clashes_and_punishments

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"例A八字: {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 检查哪些柱是酉
print("\n检查哪些柱是酉:")
for pillar in ("year", "month", "day", "hour"):
    if bazi[pillar]["zhi"] == "酉":
        print(f"  {pillar}: {bazi[pillar]['gan']}{bazi[pillar]['zhi']}")

conflicts = detect_natal_clashes_and_punishments(bazi)
punishments = conflicts.get("punishments", [])
print(f"\n检测到的原局刑: {len(punishments)}个")
for i, p in enumerate(punishments):
    flow = p.get("flow_branch")
    target = p.get("target_branch")
    risk = p.get("risk_percent", 0.0)
    targets = p.get("targets", [])
    print(f"  {i+1}. {flow} {target} risk={risk}% targets={[t.get('pillar') for t in targets]}")

# 检查自刑的逻辑
print("\n检查自刑检测逻辑:")
from bazi.punishment import SELF_PUNISH_PAIRS
pillars = ["year", "month", "day", "hour"]
self_punish_processed = set()
for i, pillar1 in enumerate(pillars):
    for pillar2 in pillars[i + 1 :]:
        zhi1 = bazi[pillar1]["zhi"]
        zhi2 = bazi[pillar2]["zhi"]
        if (zhi1, zhi2) in SELF_PUNISH_PAIRS:
            is_self = True
            print(f"  检测到: {pillar1}({zhi1}) - {pillar2}({zhi2})")
            if zhi1 in self_punish_processed:
                print(f"    跳过（zhi1={zhi1}已在处理集合中）")
                continue
            self_punish_processed.add(zhi1)
            self_punish_processed.add(zhi2)
            print(f"    添加刑事件，标记: {zhi1}, {zhi2}")
            print(f"    当前处理集合: {self_punish_processed}")
