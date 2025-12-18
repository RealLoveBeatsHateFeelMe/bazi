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
    print(f"lineyun_bonus: {liunian_2059.get('lineyun_bonus', 0.0)}")
    
    # 检查线运事件
    all_events = liunian_2059.get('all_events', [])
    for ev in all_events:
        if ev.get('type') == 'lineyun_bonus':
            print(f"线运事件: {ev}")
            print(f"  active_pillar: {ev.get('active_pillar')}")
            print(f"  lineyun_bonus_gan: {ev.get('lineyun_bonus_gan', 0.0)}")
            print(f"  lineyun_bonus_zhi: {ev.get('lineyun_bonus_zhi', 0.0)}")
            print(f"  trigger_events_gan: {len(ev.get('trigger_events_gan', []))}")
            print(f"  trigger_events_zhi: {len(ev.get('trigger_events_zhi', []))}")
