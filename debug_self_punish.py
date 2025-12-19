# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import SELF_PUNISH_PAIRS, ALL_PUNISH_PAIRS

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"例A八字: {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 手动检查所有柱对
print("\n检查所有柱对:")
pillars = ["year", "month", "day", "hour"]
self_punish_processed = set()
for i, pillar1 in enumerate(pillars):
    for pillar2 in pillars[i + 1 :]:
        zhi1 = bazi[pillar1]["zhi"]
        zhi2 = bazi[pillar2]["zhi"]
        if (zhi1, zhi2) in ALL_PUNISH_PAIRS:
            is_self = (zhi1, zhi2) in SELF_PUNISH_PAIRS
            print(f"  {pillar1}({zhi1}) - {pillar2}({zhi2}): 是刑, 自刑={is_self}")
            if is_self:
                if zhi1 in self_punish_processed:
                    print(f"    跳过（{zhi1}已处理）")
                    continue
                self_punish_processed.add(zhi1)
                self_punish_processed.add(zhi2)
                print(f"    添加，标记: {zhi1}, {zhi2}, 当前集合: {self_punish_processed}")
