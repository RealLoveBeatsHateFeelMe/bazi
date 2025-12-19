# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]

print("例A实际八字:")
print(f"年柱: {bazi['year']['gan']}{bazi['year']['zhi']}")
print(f"月柱: {bazi['month']['gan']}{bazi['month']['zhi']}")
print(f"日柱: {bazi['day']['gan']}{bazi['day']['zhi']}")
print(f"时柱: {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 打印所有柱的地支
print("\n所有柱的地支:")
for pillar in ("year", "month", "day", "hour"):
    print(f"  {pillar}: {bazi[pillar]['zhi']}")
