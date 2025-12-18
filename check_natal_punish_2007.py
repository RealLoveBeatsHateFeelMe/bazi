# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import detect_natal_clashes_and_punishments

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
bazi = basic['bazi']

print("命局:", {k: v['zhi'] for k, v in bazi.items()})

# 检测原局内部的静态刑
natal_static = detect_natal_clashes_and_punishments(bazi)
natal_punishments = natal_static.get("punishments", [])

print(f"\n原局内部静态刑数量: {len(natal_punishments)}")
for ev in natal_punishments:
    print(f"  原局刑: {ev.get('flow_branch')} vs {ev.get('target_branch')}, risk={ev.get('risk_percent', 0.0)}")
