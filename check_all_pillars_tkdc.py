# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

# 检查不同柱的天克地冲加成
dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
bazi = basic['bazi']
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

print("命局:", {k: f"{v['gan']}{v['zhi']}" for k, v in bazi.items()})

years_to_check = [2021, 2033, 2059]

for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") in years_to_check:
            year = liunian.get("year")
            print(f"\n{year}年:")
            print(f"  流年: {liunian.get('gan')}{liunian.get('zhi')}")
            
            clashes_natal = liunian.get("clashes_natal", [])
            for clash in clashes_natal:
                if clash:
                    tkdc_bonus = clash.get('tkdc_bonus_percent', 0.0)
                    tkdc_targets = clash.get("tkdc_targets", [])
                    print(f"  流年冲:")
                    print(f"    tkdc_bonus_percent: {tkdc_bonus}")
                    print(f"    tkdc_targets: {[(t.get('pillar'), t.get('target_gan')) for t in tkdc_targets]}")
                    print(f"    risk_percent: {clash.get('risk_percent', 0.0)}")
