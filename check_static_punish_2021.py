# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2007, 1, 28, 12, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

# 检查2021年
for group in luck.get('groups', []):
    dayun = group.get('dayun', {})
    if dayun.get('start_year', 0) <= 2021:
        print(f"大运: {dayun.get('zhi')}, 静态刑数量: {len(dayun.get('punishments_natal', []))}")
        for punish_ev in dayun.get('punishments_natal', []):
            print(f"  静态刑: {punish_ev.get('flow_branch')} vs {punish_ev.get('target_branch')}, risk={punish_ev.get('risk_percent', 0.0)}")
        
        for liunian in group.get('liunian', []):
            if liunian.get('year') == 2021:
                print(f"\n2021年流年: {liunian.get('zhi')}")
                print(f"流年与命局相刑: {len(liunian.get('punishments_natal', []))}")
                for punish_ev in liunian.get('punishments_natal', []):
                    print(f"  流年刑: {punish_ev.get('flow_branch')} vs {punish_ev.get('target_branch')}, risk={punish_ev.get('risk_percent', 0.0)}")
                
                # 检查静态刑激活事件
                all_events = liunian.get('all_events', [])
                for ev in all_events:
                    if ev.get('type') == 'static_punish_activation':
                        print(f"  静态刑激活: risk={ev.get('risk_percent', 0.0)}")
                break
