# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
yongshen_elements = basic.get("yongshen_elements", [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)

# 查找2030年的流年
liunian_2030 = None
for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2030:
            liunian_2030 = liunian
            break
    if liunian_2030:
        break

if liunian_2030:
    total_risk = liunian_2030.get("total_risk_percent", 0.0)
    risk_from_gan = liunian_2030.get("risk_from_gan", 0.0)
    risk_from_zhi = liunian_2030.get("risk_from_zhi", 0.0)
    tkdc_risk = liunian_2030.get("tkdc_risk_percent", 0.0)
    
    print(f"例B 2030年实际值:")
    print(f"  total_risk: {total_risk}")
    print(f"  risk_from_gan: {risk_from_gan}")
    print(f"  risk_from_zhi: {risk_from_zhi}")
    print(f"  tkdc_risk: {tkdc_risk}")
    print(f"  验证: {risk_from_gan} + {risk_from_zhi} + {tkdc_risk} = {risk_from_gan + risk_from_zhi + tkdc_risk}")
