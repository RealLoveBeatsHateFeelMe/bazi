# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

years_to_check = [2021, 2033, 2059]

for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") in years_to_check:
            year = liunian.get("year")
            print(f"\n{year}年:")
            print(f"  total_risk: {liunian.get('total_risk_percent', 0.0)}")
            print(f"  risk_from_gan: {liunian.get('risk_from_gan', 0.0)}")
            print(f"  risk_from_zhi: {liunian.get('risk_from_zhi', 0.0)}")
            
            # 检查流年冲
            clashes_natal = liunian.get("clashes_natal", [])
            for clash in clashes_natal:
                if clash:
                    tkdc_bonus = clash.get('tkdc_bonus_percent', 0.0)
                    tkdc_targets = clash.get("tkdc_targets", [])
                    if tkdc_bonus > 0 or tkdc_targets:
                        print(f"  流年冲:")
                        print(f"    tkdc_bonus_percent: {tkdc_bonus}")
                        print(f"    tkdc_targets: {[t.get('pillar') for t in tkdc_targets]}")
                        print(f"    is_tian_ke_di_chong: {clash.get('is_tian_ke_di_chong', False)}")
