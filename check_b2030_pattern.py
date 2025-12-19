# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2030:
            print(f"例B 2030年:")
            
            # 检查模式事件
            patterns_liunian = liunian.get("patterns_liunian", [])
            for pat in patterns_liunian:
                print(f"  模式事件:")
                print(f"    type: {pat.get('type')}")
                print(f"    kind: {pat.get('kind')}")
                print(f"    pattern_type: {pat.get('pattern_type')}")
                print(f"    risk_percent: {pat.get('risk_percent', 0.0)}")
                pos1 = pat.get("pos1", {})
                pos2 = pat.get("pos2", {})
                print(f"    pos1: {pos1.get('source')} {pos1.get('char')} ({pos1.get('shishen')})")
                print(f"    pos2: {pos2.get('source')} {pos2.get('char')} ({pos2.get('shishen')})")
            
            break
