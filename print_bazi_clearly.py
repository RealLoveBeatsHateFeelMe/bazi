# -*- coding: utf-8 -*-
"""清晰打印八字，避免混淆"""
from datetime import datetime
from bazi.lunar_engine import analyze_basic

def print_bazi_clearly(bazi, label=""):
    """清晰打印八字，每个天干和地支都单独打印"""
    if label:
        print(f"\n{'='*60}")
        print(f"{label}")
        print(f"{'='*60}")
    
    print("八字详细:")
    print(f"  年柱: 天干={bazi['year']['gan']}, 地支={bazi['year']['zhi']}")
    print(f"  月柱: 天干={bazi['month']['gan']}, 地支={bazi['month']['zhi']}")
    print(f"  日柱: 天干={bazi['day']['gan']}, 地支={bazi['day']['zhi']}")
    print(f"  时柱: 天干={bazi['hour']['gan']}, 地支={bazi['hour']['zhi']}")
    
    print("\n所有地支列表:")
    for pillar in ("year", "month", "day", "hour"):
        print(f"  {pillar}_zhi = '{bazi[pillar]['zhi']}'")
    
    print("\n八字简写:")
    print(f"  {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 例A
dt_a = datetime(1981, 9, 15, 10, 0)
basic_a = analyze_basic(dt_a)
bazi_a = basic_a["bazi"]
print_bazi_clearly(bazi_a, "例A：1981-09-15 10:00")

# 例B
dt_b = datetime(2007, 1, 28, 12, 0)
basic_b = analyze_basic(dt_b)
bazi_b = basic_b["bazi"]
print_bazi_clearly(bazi_b, "例B：2007-01-28 12:00")
