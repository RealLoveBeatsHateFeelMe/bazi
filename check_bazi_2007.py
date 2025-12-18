# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
bazi = basic['bazi']

print("命局地支:", [bazi[k]['zhi'] for k in ['year', 'month', 'day', 'hour']])
print("戌的数量:", [bazi[k]['zhi'] for k in ['year', 'month', 'day', 'hour']].count('戌'))
print("丑的数量:", [bazi[k]['zhi'] for k in ['year', 'month', 'day', 'hour']].count('丑'))
