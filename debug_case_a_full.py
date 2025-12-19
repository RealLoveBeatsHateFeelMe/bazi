# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import detect_natal_clashes_and_punishments, ALL_PUNISH_PAIRS, SELF_PUNISH_PAIRS

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"例A八字: {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 检查所有柱的地支
print("\n所有柱的地支:")
for pillar in ("year", "month", "day", "hour"):
    print(f"  {pillar}: {bazi[pillar]['zhi']}")

# 手动检查所有可能的刑组合
print("\n手动检查所有可能的刑组合:")
pillars = ["year", "month", "day", "hour"]
for i, pillar1 in enumerate(pillars):
    for pillar2 in pillars[i + 1 :]:
        zhi1 = bazi[pillar1]["zhi"]
        zhi2 = bazi[pillar2]["zhi"]
        if (zhi1, zhi2) in ALL_PUNISH_PAIRS:
            is_self = (zhi1, zhi2) in SELF_PUNISH_PAIRS
            print(f"  {pillar1}({zhi1}) - {pillar2}({zhi2}): 是刑, 自刑={is_self}")

conflicts = detect_natal_clashes_and_punishments(bazi)
punishments = conflicts.get("punishments", [])
print(f"\n检测到的原局刑: {len(punishments)}个")
for i, p in enumerate(punishments):
    flow = p.get("flow_branch")
    target = p.get("target_branch")
    risk = p.get("risk_percent", 0.0)
    targets = p.get("targets", [])
    print(f"  {i+1}. {flow} {target} risk={risk}% targets={[t.get('pillar') for t in targets]}")

# 检查酉酉自刑的数量
youyou_count = sum(1 for p in punishments if p.get("flow_branch") == "酉" and p.get("target_branch") == "酉")
print(f"\n酉酉自刑数量: {youyou_count}")
print(f"期望: 1个")
