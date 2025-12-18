# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
bazi = basic['bazi']
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

print("命局:", {k: v['zhi'] for k, v in bazi.items()})

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
    print(f"\n2059年年龄: {age}")
    print(f"active_pillar: hour (age > 48)")
    
    # 检查所有基础事件
    all_events = liunian_2059.get('all_events', [])
    base_events = [ev for ev in all_events if ev.get('role') == 'base']
    print(f"\n基础事件数量: {len(base_events)}")
    
    for ev in base_events:
        ev_type = ev.get('type')
        targets = ev.get('targets', [])
        print(f"\n事件: {ev_type}, risk={ev.get('risk_percent', 0.0)}")
        print(f"  targets: {[t.get('pillar') for t in targets]}")
        if 'hour' in [t.get('pillar') for t in targets]:
            print(f"  ✓ 命中hour柱")
        else:
            print(f"  ✗ 未命中hour柱")
