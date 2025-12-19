# -*- coding: utf-8 -*-
"""验证例A的八字，确保不会搞混"""
from datetime import datetime
from bazi.lunar_engine import analyze_basic

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]

print("例A八字验证:")
print(f"年柱: {bazi['year']['gan']}{bazi['year']['zhi']}")
print(f"月柱: {bazi['month']['gan']}{bazi['month']['zhi']}")
print(f"日柱: {bazi['day']['gan']}{bazi['day']['zhi']}")
print(f"时柱: {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 明确验证
assert bazi['year']['zhi'] == "酉", f"年柱地支应该是酉，但得到{bazi['year']['zhi']}"
assert bazi['month']['zhi'] == "酉", f"月柱地支应该是酉，但得到{bazi['month']['zhi']}"
assert bazi['day']['zhi'] == "未", f"日柱地支应该是未，但得到{bazi['day']['zhi']}"
assert bazi['hour']['zhi'] == "巳", f"时柱地支应该是巳，但得到{bazi['hour']['zhi']}"

print("\n✓ 例A八字验证通过：年柱酉、月柱酉、日柱未、时柱巳")
