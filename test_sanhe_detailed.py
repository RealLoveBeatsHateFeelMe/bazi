# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.harmony import detect_sanhe_complete
from bazi.lunar_engine import analyze_basic
import json

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]

print("测试2022年（流年寅，大运应该是其他）:")
sanhe_2022 = detect_sanhe_complete(
    bazi=bazi,
    dayun_branch="卯",  # 假设大运是癸卯
    dayun_label="癸卯",
    dayun_index=2,
    liunian_branch="寅",
    liunian_year=2022,
    liunian_label="壬寅",
)
print(f"检测结果: {len(sanhe_2022)}个三合局")
if sanhe_2022:
    for ev in sanhe_2022:
        print(f"  {ev.get('matched_branches')} {ev.get('group')}")
        print(f"  来源: {json.dumps(ev.get('sources'), ensure_ascii=False, indent=4)}")

print("\n测试2010年（流年寅，大运寅）:")
sanhe_2010 = detect_sanhe_complete(
    bazi=bazi,
    dayun_branch="寅",
    dayun_label="壬寅",
    dayun_index=1,
    liunian_branch="寅",
    liunian_year=2010,
    liunian_label="庚寅",
)
print(f"检测结果: {len(sanhe_2010)}个三合局")
if sanhe_2010:
    for ev in sanhe_2010:
        print(f"  {ev.get('matched_branches')} {ev.get('group')}")
        print(f"  来源: {json.dumps(ev.get('sources'), ensure_ascii=False, indent=4)}")
else:
    print("未检测到三合局，检查原因...")
    # 检查原局是否有午和戌
    print(f"原局: 年={bazi['year']['zhi']}, 月={bazi['month']['zhi']}, 日={bazi['day']['zhi']}, 时={bazi['hour']['zhi']}")
