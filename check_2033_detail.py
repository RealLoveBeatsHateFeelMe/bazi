# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
bazi = basic['bazi']
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

print("命局:", {k: f"{v['gan']}{v['zhi']}" for k, v in bazi.items()})

for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2033:
            print(f"\n2033年:")
            print(f"  流年: {liunian.get('gan')}{liunian.get('zhi')}")
            
            # 检查流年冲
            clashes_natal = liunian.get("clashes_natal", [])
            for clash in clashes_natal:
                if clash:
                    print(f"  流年冲:")
                    print(f"    flow_branch: {clash.get('flow_branch')}")
                    print(f"    target_branch: {clash.get('target_branch')}")
                    print(f"    base_power_percent: {clash.get('base_power_percent', 0.0)}")
                    print(f"    grave_bonus_percent: {clash.get('grave_bonus_percent', 0.0)}")
                    print(f"    tkdc_bonus_percent: {clash.get('tkdc_bonus_percent', 0.0)}")
                    tkdc_targets = clash.get("tkdc_targets", [])
                    print(f"    tkdc_targets: {[t.get('pillar') for t in tkdc_targets]}")
                    print(f"    risk_percent: {clash.get('risk_percent', 0.0)}")
            
            print(f"  total_risk: {liunian.get('total_risk_percent', 0.0)}")
            break
