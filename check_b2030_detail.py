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
            print(f"  total_risk: {liunian.get('total_risk_percent', 0.0)}")
            print(f"  risk_from_gan: {liunian.get('risk_from_gan', 0.0)}")
            print(f"  risk_from_zhi: {liunian.get('risk_from_zhi', 0.0)}")
            
            # 检查所有事件
            all_events = liunian.get("all_events", [])
            punishment_risk = sum(ev.get("risk_percent", 0.0) for ev in all_events if ev.get("type") == "punishment")
            pattern_risk = sum(ev.get("risk_percent", 0.0) for ev in all_events if ev.get("type") == "pattern")
            static_clash_risk = sum(ev.get("risk_percent", 0.0) for ev in all_events if ev.get("type") == "static_clash_activation")
            static_punish_risk = sum(ev.get("risk_percent", 0.0) for ev in all_events if ev.get("type") == "static_punish_activation")
            
            clashes_dayun = liunian.get("clashes_dayun", [])
            dayun_liunian_clash_risk = sum(ev.get("risk_percent", 0.0) for ev in clashes_dayun)
            
            print(f"  刑风险: {punishment_risk}")
            print(f"  模式风险: {pattern_risk}")
            print(f"  静态冲风险: {static_clash_risk}")
            print(f"  静态刑风险: {static_punish_risk}")
            print(f"  运年相冲风险: {dayun_liunian_clash_risk}")
            break
