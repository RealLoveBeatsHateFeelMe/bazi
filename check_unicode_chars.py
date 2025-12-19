# -*- coding: utf-8 -*-
"""检查Unicode字符问题"""
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import ALL_PUNISH_PAIRS

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]

day_zhi = bazi['day']['zhi']
hour_zhi = bazi['hour']['zhi']

print("例A日柱和时柱的Unicode:")
print(f"  日柱地支: {day_zhi} (Unicode: U+{ord(day_zhi):04X})")
print(f"  时柱地支: {hour_zhi} (Unicode: U+{ord(hour_zhi):04X})")

# 标准地支字符
standard_zhi = {
    '子': 0x5B50, '丑': 0x4E11, '寅': 0x5BC5, '卯': 0x536F,
    '辰': 0x8FB0, '巳': 0x5DF3, '午': 0x5348, '未': 0x672A,
    '申': 0x7533, '酉': 0x9149, '戌': 0x620C, '亥': 0x4EA5
}

print(f"\n标准地支Unicode:")
for zhi, code in standard_zhi.items():
    print(f"  {zhi}: U+{code:04X}")

print(f"\n日柱地支是否是标准'辰' (U+8FB0): {ord(day_zhi) == 0x8FB0}")
print(f"时柱地支是否是标准'巳' (U+5DF3): {ord(hour_zhi) == 0x5DF3}")

# 检查刑列表中的字符
print(f"\n刑列表中包含'辰'的组合（检查Unicode）:")
for p in ALL_PUNISH_PAIRS:
    if '辰' in p or any(ord(c) == 0x8FB0 for c in p[0] + p[1]):
        zhi1_code = ord(p[0])
        zhi2_code = ord(p[1])
        print(f"  {p} -> U+{zhi1_code:04X}, U+{zhi2_code:04X}")

print(f"\n刑列表中包含'巳'的组合（检查Unicode）:")
for p in ALL_PUNISH_PAIRS:
    if '巳' in p or any(ord(c) == 0x5DF3 for c in p[0] + p[1]):
        zhi1_code = ord(p[0])
        zhi2_code = ord(p[1])
        print(f"  {p} -> U+{zhi1_code:04X}, U+{zhi2_code:04X}")

# 检查日柱时柱组合
pair = (day_zhi, hour_zhi)
print(f"\n检查 ({day_zhi}, {hour_zhi}) 是否在刑列表中:")
print(f"  日柱Unicode: U+{ord(day_zhi):04X}")
print(f"  时柱Unicode: U+{ord(hour_zhi):04X}")
print(f"  pair in ALL_PUNISH_PAIRS: {pair in ALL_PUNISH_PAIRS}")

# 检查是否有Unicode匹配的
print(f"\n检查是否有Unicode匹配的刑组合:")
for p in ALL_PUNISH_PAIRS:
    if ord(p[0]) == ord(day_zhi) and ord(p[1]) == ord(hour_zhi):
        print(f"  找到匹配: {p} (U+{ord(p[0]):04X}, U+{ord(p[1]):04X})")
