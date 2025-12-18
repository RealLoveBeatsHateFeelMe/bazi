# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2021:
            print(f"例B 2021:")
            print(f"  total_risk: {liunian.get('total_risk_percent', 0.0)}")
            print(f"  risk_from_gan: {liunian.get('risk_from_gan', 0.0)}")
            print(f"  risk_from_zhi: {liunian.get('risk_from_zhi', 0.0)}")
            
            static_activation = liunian.get("patterns_static_activation", [])
            print(f"  静态模式激活数量: {len(static_activation)}")
            for ev in static_activation:
                print(f"    类型: {ev.get('pattern_type')}, risk={ev.get('risk_percent', 0.0)}, gan={ev.get('risk_from_gan', 0.0)}, zhi={ev.get('risk_from_zhi', 0.0)}")
            break
