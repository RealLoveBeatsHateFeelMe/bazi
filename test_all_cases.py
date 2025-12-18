# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

cases = [
    ("例A 2021", datetime(2005, 9, 20, 10, 0), 2021),
    ("例A 2033", datetime(2005, 9, 20, 10, 0), 2033),
    ("例A 2059", datetime(2005, 9, 20, 10, 0), 2059),
    ("例B 2021", datetime(2007, 1, 28, 12, 0), 2021),
    ("例B 2030", datetime(2007, 1, 28, 12, 0), 2030),
]

for case_name, dt, year in cases:
    basic = analyze_basic(dt)
    yongshen = basic.get('yongshen_elements', [])
    luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)
    
    for group in luck.get("groups", []):
        for liunian in group.get("liunian", []):
            if liunian.get("year") == year:
                print(f"{case_name}:")
                print(f"  total_risk: {liunian.get('total_risk_percent', 0.0)}")
                print(f"  risk_from_gan: {liunian.get('risk_from_gan', 0.0)}")
                print(f"  risk_from_zhi: {liunian.get('risk_from_zhi', 0.0)}")
                print()
                break
