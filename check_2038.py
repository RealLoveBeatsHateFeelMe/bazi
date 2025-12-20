# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
yongshen_elements = basic.get("yongshen_elements", [])

luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)

# 查找大运4（index=3）
for group in luck["groups"]:
    dy = group["dayun"]
    if dy["index"] == 3:
        print(f"大运4: {dy['gan']}{dy['zhi']}, index={dy['index']}")
        print(f"大运4的流年列表:")
        for ln in group["liunian"]:
            print(f"  {ln['year']}年 {ln['gan']}{ln['zhi']}")
            if ln["year"] == 2038:
                print(f"    找到2038年！")
                print(f"    sanhui_complete数量: {len(ln.get('sanhui_complete', []))}")
                if ln.get("sanhui_complete"):
                    import json
                    print(f"    三会局: {json.dumps(ln['sanhui_complete'], ensure_ascii=False, indent=4)}")
        break
