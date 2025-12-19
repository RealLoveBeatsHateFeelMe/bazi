# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

# 检查例B 2030年的运年天克地冲
dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2030:
            print(f"例B 2030年:")
            print(f"  流年: {liunian.get('gan')}{liunian.get('zhi')}")
            
            # 检查运年相冲
            clashes_dayun = liunian.get("clashes_dayun", [])
            for clash in clashes_dayun:
                print(f"  运年相冲:")
                print(f"    tkdc_bonus_percent: {clash.get('tkdc_bonus_percent', 0.0)}")
                print(f"    is_tian_ke_di_chong: {clash.get('is_tian_ke_di_chong', False)}")
            
            print(f"  total_risk: {liunian.get('total_risk_percent', 0.0)}")
            print(f"  risk_from_gan: {liunian.get('risk_from_gan', 0.0)}")
            print(f"  risk_from_zhi: {liunian.get('risk_from_zhi', 0.0)}")
            break
