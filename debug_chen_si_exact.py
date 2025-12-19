# -*- coding: utf-8 -*-
"""精确检查辰巳字符和刑列表"""
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import ALL_PUNISH_PAIRS

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]

day_zhi = bazi['day']['zhi']
hour_zhi = bazi['hour']['zhi']

print("例A日柱和时柱:")
print(f"  日柱地支: {repr(day_zhi)} (字符码: {[ord(c) for c in day_zhi]})")
print(f"  时柱地支: {repr(hour_zhi)} (字符码: {[ord(c) for c in hour_zhi]})")

# 检查是否是辰和巳
print(f"\n日柱是否是'辰': {day_zhi == '辰'}")
print(f"时柱是否是'巳': {hour_zhi == '巳'}")

# 检查刑列表
pair = (day_zhi, hour_zhi)
print(f"\n检查 ({repr(day_zhi)}, {repr(hour_zhi)}) 是否在刑列表中:")
print(f"  pair in ALL_PUNISH_PAIRS: {pair in ALL_PUNISH_PAIRS}")

# 列出所有刑组合，看看是否有类似的
print(f"\n所有刑组合（前10个）:")
for i, p in enumerate(sorted(ALL_PUNISH_PAIRS)):
    if i < 10:
        print(f"  {p} (字符码: {[ord(c) for c in p[0]], [ord(c) for c in p[1]]})")

# 检查是否有包含日柱或时柱的刑组合
print(f"\n包含日柱地支的刑组合:")
for p in ALL_PUNISH_PAIRS:
    if day_zhi in p:
        print(f"  {p}")

print(f"\n包含时柱地支的刑组合:")
for p in ALL_PUNISH_PAIRS:
    if hour_zhi in p:
        print(f"  {p}")
