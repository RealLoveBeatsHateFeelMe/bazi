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
    zhi_ln = liunian_2059.get('zhi')
    print(f"\n2059年年龄: {age}, 流年地支: {zhi_ln}")
    print(f"active_pillar: hour (age > 48)")
    
    # 检查流年地支冲什么
    from bazi.config import ZHI_CHONG
    clash_target = ZHI_CHONG.get(zhi_ln)
    print(f"流年地支 {zhi_ln} 冲 {clash_target}")
    
    # 检查命局中哪些柱是clash_target
    for pillar in ['year', 'month', 'day', 'hour']:
        if bazi[pillar]['zhi'] == clash_target:
            print(f"  命局 {pillar} 柱是 {clash_target} (被冲)")
    
    # 检查所有基础事件
    all_events = liunian_2059.get('all_events', [])
    base_events = [ev for ev in all_events if ev.get('role') == 'base']
    print(f"\n基础事件数量: {len(base_events)}")
    
    total_risk_zhi = 0.0
    for ev in base_events:
        ev_type = ev.get('type')
        targets = ev.get('targets', [])
        target_pillars = [t.get('pillar') for t in targets]
        hit_hour = 'hour' in target_pillars
        risk = ev.get('risk_percent', 0.0)
        
        # 判断是地支侧事件
        is_zhi_side = False
        if ev_type == "pattern":
            kind = ev.get('kind')
            if kind == "zhi":
                is_zhi_side = True
        elif ev_type in ("branch_clash", "punishment", "dayun_liunian_branch_clash"):
            is_zhi_side = True
        
        if is_zhi_side and hit_hour:
            total_risk_zhi += risk
            print(f"  事件: {ev_type}, risk={risk}, 命中hour柱, 累加后total_risk_zhi={total_risk_zhi}")
        else:
            print(f"  事件: {ev_type}, risk={risk}, 命中hour柱: {hit_hour}, 是地支侧: {is_zhi_side}")
    
    print(f"\n命中hour柱的地支侧风险总和: {total_risk_zhi}")
    print(f"是否触发线运: {total_risk_zhi >= 10.0}")
