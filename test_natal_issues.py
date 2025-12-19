# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import detect_natal_clashes_and_punishments
from bazi.clash import detect_natal_tian_ke_di_chong
from bazi.config import PILLAR_PALACE_CN

# 测试例A：酉酉自刑
print("测试例A：1981-09-15 10:00")
dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"八字：{bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

conflicts = detect_natal_clashes_and_punishments(bazi)
punishments = conflicts.get("punishments", [])
print(f"检测到的刑：{len(punishments)}个")
for p in punishments:
    print(f"  {p.get('flow_branch')} {p.get('target_branch')} {p.get('risk_percent')}%")

# 测试例B：丑戌刑
print("\n测试例B：1985-10-17 10:00")
dt = datetime(1985, 10, 17, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"八字：{bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

conflicts = detect_natal_clashes_and_punishments(bazi)
punishments = conflicts.get("punishments", [])
print(f"检测到的刑：{len(punishments)}个")
for p in punishments:
    flow = p.get("flow_branch", "")
    target = p.get("target_branch", "")
    targets = p.get("targets", [])
    if targets:
        target_pillar = targets[0].get("pillar", "")
        # 找到flow对应的柱
        flow_pillar = None
        for pillar in ("year", "month", "day", "hour"):
            if bazi[pillar]["zhi"] == flow and pillar != target_pillar:
                flow_pillar = pillar
                break
        if flow == target:
            flow_pillar = target_pillar
        print(f"  {PILLAR_PALACE_CN.get(flow_pillar, '')}-{PILLAR_PALACE_CN.get(target_pillar, '')} {flow}{target} 刑 {p.get('risk_percent')}%")

