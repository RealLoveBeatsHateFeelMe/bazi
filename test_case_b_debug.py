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
        print(f"大运: {dayun.get('zhi')}, 静态冲: {len(dayun.get('clashes_natal', []))}, 静态刑: {len(dayun.get('punishments_natal', []))}")
        for liunian in group.get('liunian', []):
            if liunian.get('year') == 2030:
                print(f"\n2030年流年: {liunian.get('zhi')}")
                print(f"大运地支: {dayun.get('zhi')}")
                print(f"流年与命局相冲: {len(liunian.get('clashes_natal', []))}")
                print(f"流年与命局相刑: {len(liunian.get('punishments_natal', []))}")
                print(f"运年相冲: {len(liunian.get('clashes_dayun', []))}")
                
                # 检查大运静态冲
                dayun_clashes = dayun.get('clashes_natal', [])
                for ev in dayun_clashes:
                    print(f"大运静态冲: {ev.get('flow_branch')} vs {ev.get('target_branch')}, risk={ev.get('risk_percent', 0.0)}")
                
                # 检查流年与命局相冲
                ln_clashes = liunian.get('clashes_natal', [])
                for ev in ln_clashes:
                    print(f"流年与命局相冲: {ev.get('flow_branch')} vs {ev.get('target_branch')}, risk={ev.get('risk_percent', 0.0)}")
                
                # 检查运年相冲
                dy_ln_clashes = liunian.get('clashes_dayun', [])
                for ev in dy_ln_clashes:
                    print(f"运年相冲: {ev.get('dayun_branch')} vs {ev.get('liunian_branch')}, risk={ev.get('risk_percent', 0.0)}, tkdc={ev.get('tkdc_bonus_percent', 0.0)}")
                break
