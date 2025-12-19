# -*- coding: utf-8 -*-
"""查找测试用例：丑戌刑，需要年柱丑、月柱戌、日柱丑"""
from datetime import datetime
from bazi.lunar_engine import get_bazi
from bazi.punishment import detect_natal_clashes_and_punishments
from bazi.config import PILLAR_PALACE_CN

# 查找丑戌刑（年柱丑、月柱戌、日柱丑）
print("查找丑戌刑（年柱丑、月柱戌、日柱丑）...")
for year in range(1985, 2000):
    for month in range(1, 13):
        for day in range(1, 29):
            try:
                dt = datetime(year, month, day, 10, 0)
                bazi = get_bazi(dt)
                if bazi["year"]["zhi"] == "丑" and bazi["month"]["zhi"] == "戌" and bazi["day"]["zhi"] == "丑":
                    print(f"找到：{year}-{month:02d}-{day:02d} 10:00")
                    print(f"  八字：{bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")
                    conflicts = detect_natal_clashes_and_punishments(bazi)
                    punishments = conflicts.get("punishments", [])
                    print(f"  检测到的刑：")
                    for p in punishments:
                        flow = p.get("flow_branch", "")
                        target = p.get("target_branch", "")
                        targets = p.get("targets", [])
                        if targets:
                            target_pillar = targets[0].get("pillar", "")
                            # 找到flow对应的柱
                            flow_pillar = None
                            for pillar in ("year", "month", "day", "hour"):
                                if bazi[pillar]["zhi"] == flow:
                                    flow_pillar = pillar
                                    break
                            if flow_pillar:
                                print(f"    {PILLAR_PALACE_CN.get(flow_pillar, '')}-{PILLAR_PALACE_CN.get(target_pillar, '')} 刑 {p.get('risk_percent', 0.0):.1f}%")
                    break
            except:
                continue

