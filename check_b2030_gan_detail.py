# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

for group in luck.get("groups", []):
    dayun = group.get("dayun", {})
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2030:
            print(f"例B 2030年:")
            
            # 检查大运静态冲
            dayun_clashes = dayun.get("clashes_natal", [])
            for clash in dayun_clashes:
                if clash:
                    print(f"  大运静态冲:")
                    print(f"    tkdc_bonus_percent: {clash.get('tkdc_bonus_percent', 0.0)}")
                    tkdc_targets = clash.get("tkdc_targets", [])
                    print(f"    tkdc_targets: {[t.get('pillar') for t in tkdc_targets]}")
            
            # 检查运年相冲
            clashes_dayun = liunian.get("clashes_dayun", [])
            for clash in clashes_dayun:
                print(f"  运年相冲:")
                print(f"    base_risk_percent: {clash.get('base_risk_percent', 0.0)}")
                print(f"    grave_bonus_percent: {clash.get('grave_bonus_percent', 0.0)}")
                print(f"    tkdc_bonus_percent: {clash.get('tkdc_bonus_percent', 0.0)}")
                print(f"    risk_percent: {clash.get('risk_percent', 0.0)}")
            
            print(f"  risk_from_gan: {liunian.get('risk_from_gan', 0.0)}")
            print(f"  risk_from_zhi: {liunian.get('risk_from_zhi', 0.0)}")
            break
