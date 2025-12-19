# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

# 检查2033年的天克地冲
for group in luck.get("groups", []):
    dayun = group.get("dayun", {})
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2033:
            print(f"2033年:")
            print(f"  大运: {dayun.get('gan')}{dayun.get('zhi')}")
            print(f"  流年: {liunian.get('gan')}{liunian.get('zhi')}")
            
            # 检查流年冲
            clashes_natal = liunian.get("clashes_natal", [])
            for clash in clashes_natal:
                if clash:
                    print(f"  流年冲:")
                    print(f"    flow_gan: {clash.get('flow_gan')}")
                    print(f"    flow_branch: {clash.get('flow_branch')}")
                    tkdc_targets = clash.get("tkdc_targets", [])
                    print(f"    tkdc_targets: {tkdc_targets}")
                    for target in tkdc_targets:
                        print(f"      pillar: {target.get('pillar')}, target_gan: {target.get('target_gan')}")
            break
