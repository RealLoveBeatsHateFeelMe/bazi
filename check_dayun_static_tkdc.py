# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

for group in luck.get("groups", []):
    dayun = group.get("dayun", {})
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2059:
            print(f"2059年:")
            print(f"  大运: {dayun.get('gan')}{dayun.get('zhi')}")
            
            # 检查大运静态冲
            dayun_clashes = dayun.get("clashes_natal", [])
            for clash in dayun_clashes:
                if clash:
                    print(f"  大运静态冲:")
                    print(f"    flow_branch: {clash.get('flow_branch')}")
                    print(f"    target_branch: {clash.get('target_branch')}")
                    print(f"    tkdc_bonus_percent: {clash.get('tkdc_bonus_percent', 0.0)}")
                    tkdc_targets = clash.get("tkdc_targets", [])
                    print(f"    tkdc_targets: {[t.get('pillar') for t in tkdc_targets]}")
            
            # 检查流年冲
            clashes_natal = liunian.get("clashes_natal", [])
            for clash in clashes_natal:
                if clash:
                    print(f"  流年冲:")
                    print(f"    tkdc_bonus_percent: {clash.get('tkdc_bonus_percent', 0.0)}")
                    tkdc_targets = clash.get("tkdc_targets", [])
                    print(f"    tkdc_targets: {[t.get('pillar') for t in tkdc_targets]}")
            
            break
