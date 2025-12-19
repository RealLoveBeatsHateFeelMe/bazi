# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

dt = datetime(2005, 9, 20, 10, 0)
basic = analyze_basic(dt)
yongshen = basic.get('yongshen_elements', [])
luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen)

for group in luck.get("groups", []):
    for liunian in group.get("liunian", []):
        if liunian.get("year") == 2059:
            print(f"2059年:")
            print(f"  total_risk: {liunian.get('total_risk_percent', 0.0)}")
            print(f"  risk_from_gan: {liunian.get('risk_from_gan', 0.0)}")
            print(f"  risk_from_zhi: {liunian.get('risk_from_zhi', 0.0)}")
            
            # 检查流年冲
            clashes_natal = liunian.get("clashes_natal", [])
            for clash in clashes_natal:
                if clash:
                    print(f"  流年冲 tkdc_bonus: {clash.get('tkdc_bonus_percent', 0.0)}")
                    print(f"  流年冲 tkdc_targets: {[t.get('pillar') for t in clash.get('tkdc_targets', [])]}")
            
            # 检查运年相冲
            clashes_dayun = liunian.get("clashes_dayun", [])
            for clash in clashes_dayun:
                print(f"  运年相冲 tkdc_bonus: {clash.get('tkdc_bonus_percent', 0.0)}")
            
            # 检查所有事件
            all_events = liunian.get("all_events", [])
            for ev in all_events:
                if ev.get("type") == "static_clash_activation":
                    print(f"  静态冲激活: {ev.get('risk_percent', 0.0)}")
            
            break
