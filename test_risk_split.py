# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

group = luck['groups'][0]
ln = group['liunian'][0]

print(f"year={ln['year']}")
print(f"total_risk={ln.get('total_risk_percent', 0.0)}")
print(f"risk_from_gan={ln.get('risk_from_gan', 0.0)}")
print(f"risk_from_zhi={ln.get('risk_from_zhi', 0.0)}")
