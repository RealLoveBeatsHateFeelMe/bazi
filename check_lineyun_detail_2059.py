# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

# 查找2059年的流年
liunian_2059 = None
for group in luck.get('groups', []):
    for liunian in group.get('liunian', []):
        if liunian.get('year') == 2059:
            liunian_2059 = liunian
            break
    if liunian_2059:
        break

if liunian_2059:
    age = liunian_2059.get('age', 0)
    print(f"2059年年龄: {age}")
    
    # 检查active_pillar
    if age <= 16:
        active_pillar = "year"
    elif age <= 32:
        active_pillar = "month"
    elif age <= 48:
        active_pillar = "day"
    else:
        active_pillar = "hour"
    print(f"active_pillar: {active_pillar}")
    
    # 检查基础事件
    all_events = liunian_2059.get('all_events', [])
    base_events = [ev for ev in all_events if ev.get('role') == 'base']
    print(f"\n基础事件数量: {len(base_events)}")
    
    # 检查哪些事件命中active_pillar
    for ev in base_events:
        ev_type = ev.get('type')
        targets = ev.get('targets', [])
        hit_active = False
        for target in targets:
            if target.get('pillar') == active_pillar:
                hit_active = True
                break
        print(f"  事件: {ev_type}, risk={ev.get('risk_percent', 0.0)}, 命中active_pillar: {hit_active}")
        if hit_active:
            print(f"    targets: {[t.get('pillar') for t in targets]}")
