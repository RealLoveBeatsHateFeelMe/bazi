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
    print(f"例A 2059年 total_risk_percent = {liunian_2059.get('total_risk_percent', 0.0)}")
    print(f"例A 2059年 risk_from_gan = {liunian_2059.get('risk_from_gan', 0.0)}")
    print(f"例A 2059年 risk_from_zhi = {liunian_2059.get('risk_from_zhi', 0.0)}")
    print(f"例A 2059年 lineyun_bonus = {liunian_2059.get('lineyun_bonus', 0.0)}")
    
    # 详细计算
    all_events = liunian_2059.get('all_events', [])
    clash_risk = sum(ev.get('risk_percent', 0.0) for ev in all_events if ev.get('type') == 'branch_clash')
    pattern_risk = sum(ev.get('risk_percent', 0.0) for ev in all_events if ev.get('type') == 'pattern')
    pattern_static_risk = sum(ev.get('risk_percent', 0.0) for ev in all_events if ev.get('type') == 'pattern_static_activation')
    static_clash_risk = sum(ev.get('risk_percent', 0.0) for ev in all_events if ev.get('type') == 'static_clash_activation')
    
    print(f"\n详细计算:")
    print(f"  冲风险: {clash_risk}")
    print(f"  模式风险: {pattern_risk}")
    print(f"  静态模式风险: {pattern_static_risk}")
    print(f"  静态冲风险: {static_clash_risk}")
    
    # 检查冲的详细构成
    for ev in all_events:
        if ev.get('type') == 'branch_clash':
            print(f"\n冲事件详情:")
            print(f"  base_power: {ev.get('base_power_percent', 0.0)}")
            print(f"  grave_bonus: {ev.get('grave_bonus_percent', 0.0)}")
            print(f"  tkdc_bonus: {ev.get('tkdc_bonus_percent', 0.0)}")
            print(f"  risk_percent: {ev.get('risk_percent', 0.0)}")
    
    # 检查静态冲激活的详细构成
    for ev in all_events:
        if ev.get('type') == 'static_clash_activation':
            print(f"\n静态冲激活详情:")
            print(f"  risk_percent: {ev.get('risk_percent', 0.0)}")
    
    # 检查静态模式激活的详细构成
    for ev in all_events:
        if ev.get('type') == 'pattern_static_activation':
            print(f"\n静态模式激活详情:")
            print(f"  risk_percent: {ev.get('risk_percent', 0.0)}")
            print(f"  risk_from_gan: {ev.get('risk_from_gan', 0.0)}")
            print(f"  risk_from_zhi: {ev.get('risk_from_zhi', 0.0)}")
