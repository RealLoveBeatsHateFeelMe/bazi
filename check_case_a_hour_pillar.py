# -*- coding: utf-8 -*-
"""检查例A的时柱到底是什么，以及为什么会有2个刑"""
from datetime import datetime
from bazi.lunar_engine import analyze_basic

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]

print("例A八字（使用repr显示准确字符）:")
print(f"  年柱: {repr(bazi['year']['zhi'])}")
print(f"  月柱: {repr(bazi['month']['zhi'])}")
print(f"  日柱: {repr(bazi['day']['zhi'])}")
print(f"  时柱: {repr(bazi['hour']['zhi'])}")

# 检查时柱是否是"未"
hour_zhi = bazi['hour']['zhi']
print(f"\n时柱地支: {hour_zhi}")
print(f"时柱是否是'未': {hour_zhi == '未'}")
print(f"时柱是否是'巳': {hour_zhi == '巳'}")

# 检查日柱和时柱的组合
day_zhi = bazi['day']['zhi']
print(f"\n日柱地支: {day_zhi}")
print(f"日柱时柱组合: {day_zhi}{hour_zhi}")

# 如果时柱是"未"，检查辰未是否在刑列表中
if hour_zhi == '未':
    from bazi.punishment import ALL_PUNISH_PAIRS
    print(f"\n如果时柱是'未':")
    print(f"  ('辰', '未') in ALL_PUNISH_PAIRS: {('辰', '未') in ALL_PUNISH_PAIRS}")
    print(f"  ('未', '辰') in ALL_PUNISH_PAIRS: {('未', '辰') in ALL_PUNISH_PAIRS}")
