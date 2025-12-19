# -*- coding: utf-8 -*-
"""查找测试用例：酉酉自刑和丑戌刑"""
from datetime import datetime, timedelta
from bazi.lunar_engine import get_bazi
from bazi.punishment import detect_natal_clashes_and_punishments
from bazi.config import PILLAR_PALACE_CN

# 查找酉酉自刑（年柱和月柱都是酉）
print("查找酉酉自刑（年柱和月柱都是酉）...")
found_youyou = False
for year in range(1981, 2000):
    for month in range(1, 13):
        try:
            dt = datetime(year, month, 15, 10, 0)
            bazi = get_bazi(dt)
            if bazi["year"]["zhi"] == "酉" and bazi["month"]["zhi"] == "酉":
                print(f"找到：{year}-{month:02d}-15 10:00")
                print(f"  八字：{bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")
                conflicts = detect_natal_clashes_and_punishments(bazi)
                punishments = conflicts.get("punishments", [])
                for p in punishments:
                    if p.get("flow_branch") == "酉" and p.get("target_branch") == "酉":
                        targets = p.get("targets", [])
                        if targets:
                            print(f"  刑：{PILLAR_PALACE_CN.get('year', '')}-{PILLAR_PALACE_CN.get('month', '')} 刑 {p.get('risk_percent', 0.0):.1f}%")
                found_youyou = True
                break
        except:
            continue
    if found_youyou:
        break

# 查找丑戌刑（年柱丑、月柱戌、日柱丑或类似）
print("\n查找丑戌刑（年柱丑、月柱戌、日柱丑或类似）...")
found_chouxu = False
for year in range(1985, 2000):
    for month in range(1, 13):
        try:
            dt = datetime(year, month, 15, 10, 0)
            bazi = get_bazi(dt)
            if bazi["year"]["zhi"] == "丑" and bazi["month"]["zhi"] == "戌":
                print(f"找到：{year}-{month:02d}-15 10:00")
                print(f"  八字：{bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")
                conflicts = detect_natal_clashes_and_punishments(bazi)
                punishments = conflicts.get("punishments", [])
                for p in punishments:
                    flow = p.get("flow_branch", "")
                    target = p.get("target_branch", "")
                    if (flow == "丑" and target == "戌") or (flow == "戌" and target == "丑"):
                        targets = p.get("targets", [])
                        if targets:
                            pillar = targets[0].get("pillar", "")
                            # 找到flow对应的柱
                            flow_pillar = None
                            for p in ("year", "month", "day", "hour"):
                                if bazi[p]["zhi"] == flow:
                                    flow_pillar = p
                                    break
                            print(f"  刑：{PILLAR_PALACE_CN.get(flow_pillar, '')}-{PILLAR_PALACE_CN.get(pillar, '')} 刑 {p.get('risk_percent', 0.0):.1f}%")
                found_chouxu = True
                break
        except:
            continue
    if found_chouxu:
        break

