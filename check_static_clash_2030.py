# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

# 检查2030年
for group in luck.get('groups', []):
    dayun = group.get('dayun', {})
    if dayun.get('start_year', 0) <= 2030:
        print(f"大运: {dayun.get('zhi')}, 静态冲数量: {len(dayun.get('clashes_natal', []))}")
        for clash_ev in dayun.get('clashes_natal', []):
            print(f"  大运静态冲: {clash_ev.get('flow_branch')} vs {clash_ev.get('target_branch')}, risk={clash_ev.get('risk_percent', 0.0)}")
            print(f"    - base_power: {clash_ev.get('base_power_percent', 0.0)}, grave_bonus: {clash_ev.get('grave_bonus_percent', 0.0)}, tkdc: {clash_ev.get('tkdc_bonus_percent', 0.0)}")
            print(f"    - targets数量: {len(clash_ev.get('targets', []))}")
            for target in clash_ev.get('targets', []):
                print(f"      target: {target.get('pillar')}, weight: {target.get('position_weight', 0.0)}")
        
        for liunian in group.get('liunian', []):
            if liunian.get('year') == 2030:
                print(f"\n2030年流年: {liunian.get('zhi')}")
                print(f"运年相冲: {len(liunian.get('clashes_dayun', []))}")
                for clash_ev in liunian.get('clashes_dayun', []):
                    print(f"  运年相冲: {clash_ev.get('dayun_branch')} vs {clash_ev.get('liunian_branch')}, risk={clash_ev.get('risk_percent', 0.0)}")
                    print(f"    - base_risk: {clash_ev.get('base_risk_percent', 0.0)}, grave_bonus: {clash_ev.get('grave_bonus_percent', 0.0)}, tkdc: {clash_ev.get('tkdc_bonus_percent', 0.0)}")
                
                # 检查静态冲激活事件
                all_events = liunian.get('all_events', [])
                for ev in all_events:
                    if ev.get('type') == 'static_clash_activation':
                        print(f"  静态冲激活: risk={ev.get('risk_percent', 0.0)}")
                break
