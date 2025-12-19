# -*- coding: utf-8 -*-
"""验证例A 2005-09-20的八字"""
from datetime import datetime
from bazi.lunar_engine import analyze_basic

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]

print("例A 2005-09-20 10:00 八字:")
print(f"年柱: {bazi['year']['gan']}{bazi['year']['zhi']}")
print(f"月柱: {bazi['month']['gan']}{bazi['month']['zhi']}")
print(f"日柱: {bazi['day']['gan']}{bazi['day']['zhi']}")
print(f"时柱: {bazi['hour']['gan']}{bazi['hour']['zhi']}")

expected = "乙酉乙酉丁未乙巳"
actual = f"{bazi['year']['gan']}{bazi['year']['zhi']}{bazi['month']['gan']}{bazi['month']['zhi']}{bazi['day']['gan']}{bazi['day']['zhi']}{bazi['hour']['gan']}{bazi['hour']['zhi']}"

print(f"\n期望: {expected}")
print(f"实际: {actual}")
print(f"匹配: {expected == actual}")

assert expected == actual, f"八字不匹配！期望{expected}，实际{actual}"
