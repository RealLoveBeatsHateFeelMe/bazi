# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
yongshen_elements = basic.get("yongshen_elements", [])

luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)

print("检查所有大运:")
for i, group in enumerate(luck["groups"]):
    dy = group["dayun"]
    print(f"Group {i}: index={dy['index']}, 干支={dy['gan']}{dy['zhi']}, 起始年={dy['start_year']}")
    if dy['index'] == 3:  # 大运4（index从0开始，所以index=3是大运4）
        print(f"  -> 这是大运4！")
        # 检查2026年
        for ln in group["liunian"]:
            if ln["year"] == 2026:
                print(f"  2026年: {ln['gan']}{ln['zhi']}")
                break
