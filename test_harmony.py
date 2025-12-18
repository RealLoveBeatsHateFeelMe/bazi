# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
print("Bazi:", basic["bazi"])
yongshen = basic["yongshen_elements"]
luck = analyze_luck(dt, True, yongshen)

for group in luck["groups"]:
    for ln in group.get("liunian", []):
        year = ln.get("year")
        if year in [2024, 2025, 2026]:
            zhi = ln.get("zhi")
            harmonies = ln.get("harmonies", [])
            print(f"\n{year}: zhi={zhi}")
            for h in harmonies:
                print(f"  {h.get('subtype')}: {h.get('matched_branches')}, group={h.get('group')}")
