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
print("\n流年丑(2021年)检测到的刑事件:")
events = detect_branch_punishments(bazi, "丑", "liunian", 2021, "辛丑")
print(f"  数量: {len(events)}个")
for ev in events:
    targets = ev.get("targets", [])
    print(f"  {ev.get('flow_branch')} {ev.get('target_branch')} risk={ev.get('risk_percent', 0.0)}% targets={[t.get('pillar') for t in targets]}")

# 检查流年丑与年柱和日柱的刑
print("\n检查流年丑与年柱和日柱的刑:")
print(f"  年柱地支: {bazi['year']['zhi']}")
print(f"  日柱地支: {bazi['day']['zhi']}")
print(f"  流年地支: 丑")

# 检查丑与年柱地支是否相刑
from bazi.punishment import ALL_PUNISH_PAIRS
if ("丑", bazi['year']['zhi']) in ALL_PUNISH_PAIRS:
    print(f"  丑-{bazi['year']['zhi']} 在刑列表中")
else:
    print(f"  丑-{bazi['year']['zhi']} 不在刑列表中")

if ("丑", bazi['day']['zhi']) in ALL_PUNISH_PAIRS:
    print(f"  丑-{bazi['day']['zhi']} 在刑列表中")
else:
    print(f"  丑-{bazi['day']['zhi']} 不在刑列表中")

