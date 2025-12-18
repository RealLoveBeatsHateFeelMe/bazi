# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
bazi = basic['bazi']

print("命局详细:")
for k, v in bazi.items():
    print(f"  {k}: {v['gan']}{v['zhi']}")

zhi_list = [bazi[k]['zhi'] for k in ['year', 'month', 'day', 'hour']]
print(f"\n地支列表: {zhi_list}")
print(f"戌的数量: {zhi_list.count('戌')}")
print(f"丑的数量: {zhi_list.count('丑')}")

# 检查哪些柱是戌，哪些柱是丑
for k, v in bazi.items():
    if v['zhi'] == '戌':
        print(f"  {k}柱是戌")
    if v['zhi'] == '丑':
        print(f"  {k}柱是丑")
