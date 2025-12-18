# -*- coding: utf-8 -*-
"""黄金回归用例：例A和例B"""

import sys
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck


def _assert_close(actual: float, expected: float, tol: float = 0.5) -> None:
    """浮点比较辅助函数，默认允许 0.5% 误差。"""
    assert abs(actual - expected) <= tol, f"expected {expected}, got {actual}"


def test_case_A_2021():
    """例A：2005-09-20 10:00 男，2021年"""
    dt = datetime(2005, 9, 20, 10, 0)
    basic = analyze_basic(dt)
    yongshen_elements = basic.get("yongshen_elements", [])
    
    luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)
    
    # 查找2021年的流年
    liunian_2021 = None
    for group in luck.get("groups", []):
        for liunian in group.get("liunian", []):
            if liunian.get("year") == 2021:
                liunian_2021 = liunian
                break
        if liunian_2021:
            break
    
    assert liunian_2021 is not None, "应找到2021年的流年数据"
    
    # 期望：core_total=40（丑未冲25=10+5+10；运年相冲15=10+5；墓库加成必须出现两次）
    # 注意：这里需要确认 core_total 是什么字段，可能是 total_risk_percent
    total_risk = liunian_2021.get("total_risk_percent", 0.0)
    print(f"[DEBUG] 例A 2021年 total_risk_percent = {total_risk}")
    print(f"[DEBUG] 期望 core_total = 40")
    
    # 检查事件详情
    all_events = liunian_2021.get("all_events", [])
    print(f"[DEBUG] 事件数量: {len(all_events)}")
    for ev in all_events:
        ev_type = ev.get('type')
        risk = ev.get('risk_percent', 0.0)
        print(f"[DEBUG] 事件: {ev_type}, risk={risk}")
        if ev_type == "branch_clash":
            print(f"  - base_power: {ev.get('base_power_percent', 0.0)}, grave_bonus: {ev.get('grave_bonus_percent', 0.0)}, tkdc: {ev.get('tkdc_bonus_percent', 0.0)}")
        elif ev_type == "dayun_liunian_branch_clash":
            print(f"  - base_risk: {ev.get('base_risk_percent', 0.0)}, grave_bonus: {ev.get('grave_bonus_percent', 0.0)}, tkdc: {ev.get('tkdc_bonus_percent', 0.0)}")
    
    # 检查运年相冲
    clashes_dayun = liunian_2021.get("clashes_dayun", [])
    print(f"[DEBUG] 运年相冲数量: {len(clashes_dayun)}")
    for ev in clashes_dayun:
        print(f"[DEBUG] 运年相冲: {ev.get('dayun_branch')} vs {ev.get('liunian_branch')}, risk={ev.get('risk_percent', 0.0)}")
    
    # 检查静态激活
    static_activation = liunian_2021.get("patterns_static_activation", [])
    print(f"[DEBUG] 静态激活数量: {len(static_activation)}")
    for ev in static_activation:
        print(f"[DEBUG] 静态激活: {ev.get('pattern_type')}, risk={ev.get('risk_percent', 0.0)}, gan={ev.get('risk_from_gan', 0.0)}, zhi={ev.get('risk_from_zhi', 0.0)}")
    
    # 暂时不断言，先看输出
    # _assert_close(total_risk, 40.0, tol=1.0)


def test_case_A_2033():
    """例A：2005-09-20 10:00 男，2033年"""
    dt = datetime(2005, 9, 20, 10, 0)
    basic = analyze_basic(dt)
    yongshen_elements = basic.get("yongshen_elements", [])
    
    luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)
    
    # 查找2033年的流年
    liunian_2033 = None
    for group in luck.get("groups", []):
        for liunian in group.get("liunian", []):
            if liunian.get("year") == 2033:
                liunian_2033 = liunian
                break
        if liunian_2033:
            break
    
    assert liunian_2033 is not None, "应找到2033年的流年数据"
    
    # 期望：core_total=25（墓库冲15=10+5；TKDC+10）
    total_risk = liunian_2033.get("total_risk_percent", 0.0)
    print(f"[DEBUG] 例A 2033年 total_risk_percent = {total_risk}")
    print(f"[DEBUG] 期望 core_total = 25")


def test_case_A_2059():
    """例A：2005-09-20 10:00 男，2059年"""
    dt = datetime(2005, 9, 20, 10, 0)
    basic = analyze_basic(dt)
    yongshen_elements = basic.get("yongshen_elements", [])
    
    luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)
    
    # 查找2059年的流年
    liunian_2059 = None
    dayun_dict_2059 = None
    for group in luck.get("groups", []):
        dayun_dict = group.get("dayun", {})
        for liunian in group.get("liunian", []):
            if liunian.get("year") == 2059:
                liunian_2059 = liunian
                dayun_dict_2059 = dayun_dict
                break
        if liunian_2059:
            break
    
    assert liunian_2059 is not None, "应找到2059年的流年数据"
    
    # 期望：core_total=203.5（不含线运）加上线运6% = 209.5
    total_risk = liunian_2059.get("total_risk_percent", 0.0)
    lineyun_bonus = liunian_2059.get("lineyun_bonus", 0.0)
    
    print(f"[DEBUG] 例A 2059年 total_risk_percent = {total_risk}")
    print(f"[DEBUG] 例A 2059年 lineyun_bonus = {lineyun_bonus}")
    print(f"[DEBUG] 期望 core_total = 203.5（不含线运），加上线运6% = 209.5")
    
    # 检查详细事件
    all_events = liunian_2059.get("all_events", [])
    print(f"[DEBUG] 事件数量: {len(all_events)}")
    for ev in all_events:
        ev_type = ev.get('type')
        risk = ev.get('risk_percent', 0.0)
        print(f"[DEBUG] 事件: {ev_type}, risk={risk}")
        if ev_type == "branch_clash":
            print(f"  - base_power: {ev.get('base_power_percent', 0.0)}, grave_bonus: {ev.get('grave_bonus_percent', 0.0)}, tkdc: {ev.get('tkdc_bonus_percent', 0.0)}")
        elif ev_type == "pattern":
            print(f"  - pattern_type: {ev.get('pattern_type')}, kind: {ev.get('kind')}")
    
    # 检查静态激活
    static_activation = liunian_2059.get("patterns_static_activation", [])
    print(f"[DEBUG] 静态激活数量: {len(static_activation)}")
    for ev in static_activation:
        print(f"[DEBUG] 静态激活: {ev.get('pattern_type')}, risk={ev.get('risk_percent', 0.0)}, gan={ev.get('risk_from_gan', 0.0)}, zhi={ev.get('risk_from_zhi', 0.0)}")
    
    # 检查大运的静态冲（dayun_dict中的clashes_natal）
    if dayun_dict_2059:
        dayun_clashes = dayun_dict_2059.get("clashes_natal", [])
        print(f"[DEBUG] 大运静态冲数量: {len(dayun_clashes)}")
        for ev in dayun_clashes:
            print(f"[DEBUG] 大运静态冲: {ev.get('flow_branch')} vs {ev.get('target_branch')}, risk={ev.get('risk_percent', 0.0)}")
            print(f"  - base_power: {ev.get('base_power_percent', 0.0)}, grave_bonus: {ev.get('grave_bonus_percent', 0.0)}, tkdc: {ev.get('tkdc_bonus_percent', 0.0)}")
    
    # 检查运年相冲
    clashes_dayun_2059 = liunian_2059.get("clashes_dayun", [])
    print(f"[DEBUG] 运年相冲数量: {len(clashes_dayun_2059)}")
    for ev in clashes_dayun_2059:
        print(f"[DEBUG] 运年相冲: {ev.get('dayun_branch')} vs {ev.get('liunian_branch')}, risk={ev.get('risk_percent', 0.0)}")
    
    # 检查静态冲/刑激活事件
    for ev in all_events:
        if ev.get('type') in ('static_clash_activation', 'static_punish_activation'):
            print(f"[DEBUG] 静态冲/刑激活: {ev.get('type')}, risk={ev.get('risk_percent', 0.0)}")


def test_case_B_2021():
    """例B：2007-01-28 12:00 男，2021年"""
    dt = datetime(2007, 1, 28, 12, 0)
    basic = analyze_basic(dt)
    yongshen_elements = basic.get("yongshen_elements", [])
    
    luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)
    
    # 查找2021年的流年
    liunian_2021 = None
    for group in luck.get("groups", []):
        for liunian in group.get("liunian", []):
            if liunian.get("year") == 2021:
                liunian_2021 = liunian
                break
        if liunian_2021:
            break
    
    assert liunian_2021 is not None, "应找到2021年的流年数据"
    
    # 期望：core_total=43（伤官见官15+静态10=25；丑戌刑两次12+静态刑6=18）不算线运因为单柱的影响不超过10%
    total_risk = liunian_2021.get("total_risk_percent", 0.0)
    lineyun_bonus = liunian_2021.get("lineyun_bonus", 0.0)
    print(f"[DEBUG] 例B 2021年 total_risk_percent = {total_risk}")
    print(f"[DEBUG] 例B 2021年 lineyun_bonus = {lineyun_bonus}")
    print(f"[DEBUG] 期望 core_total = 43，不算线运（单柱影响不超过10%）")
    
    # 检查详细事件
    all_events = liunian_2021.get("all_events", [])
    print(f"[DEBUG] 事件数量: {len(all_events)}")
    for ev in all_events:
        ev_type = ev.get('type')
        risk = ev.get('risk_percent', 0.0)
        print(f"[DEBUG] 事件: {ev_type}, risk={risk}")
        if ev_type == "pattern":
            print(f"  - pattern_type: {ev.get('pattern_type')}, kind: {ev.get('kind')}")
        elif ev_type == "punishment":
            print(f"  - target_branch: {ev.get('target_branch')}")
    
    # 检查静态激活
    static_activation = liunian_2021.get("patterns_static_activation", [])
    print(f"[DEBUG] 静态激活数量: {len(static_activation)}")
    for ev in static_activation:
        print(f"[DEBUG] 静态激活: {ev.get('pattern_type')}, risk={ev.get('risk_percent', 0.0)}, gan={ev.get('risk_from_gan', 0.0)}, zhi={ev.get('risk_from_zhi', 0.0)}")
    
    # 检查刑事件
    punishments = liunian_2021.get("punishments_natal", [])
    print(f"[DEBUG] 刑事件数量: {len(punishments)}")
    for ev in punishments:
        print(f"[DEBUG] 刑: target={ev.get('target_branch')}, risk={ev.get('risk_percent', 0.0)}")


def test_case_B_2030():
    """例B：2007-01-28 12:00 男，2030年"""
    dt = datetime(2007, 1, 28, 12, 0)
    basic = analyze_basic(dt)
    yongshen_elements = basic.get("yongshen_elements", [])
    
    luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)
    
    # 查找2030年的流年
    liunian_2030 = None
    dayun_dict_2030 = None
    for group in luck.get("groups", []):
        dayun_dict = group.get("dayun", {})
        for liunian in group.get("liunian", []):
            if liunian.get("year") == 2030:
                liunian_2030 = liunian
                dayun_dict_2030 = dayun_dict
                break
        if liunian_2030:
            break
    
    assert liunian_2030 is not None, "应找到2030年的流年数据"
    
    # 期望：core_total=73%（丑戌刑6+静态刑6=12；辰戌冲15+静态冲15+TKDC10=40，运年天克地冲再加10% = 50%）算线运6%，因为加上静态的丑戌刑，辛丑柱超过10%
    total_risk = liunian_2030.get("total_risk_percent", 0.0)
    lineyun_bonus = liunian_2030.get("lineyun_bonus", 0.0)
    print(f"[DEBUG] 例B 2030年 total_risk_percent = {total_risk}")
    print(f"[DEBUG] 例B 2030年 lineyun_bonus = {lineyun_bonus}")
    print(f"[DEBUG] 期望 core_total = 73%（12+50+线运6%），算线运6%（单柱影响超过10%）")
    
    # 检查详细事件
    all_events = liunian_2030.get("all_events", [])
    print(f"[DEBUG] 事件数量: {len(all_events)}")
    for ev in all_events:
        ev_type = ev.get('type')
        risk = ev.get('risk_percent', 0.0)
        print(f"[DEBUG] 事件: {ev_type}, risk={risk}")
        if ev_type == "branch_clash":
            print(f"  - base_power: {ev.get('base_power_percent', 0.0)}, grave_bonus: {ev.get('grave_bonus_percent', 0.0)}, tkdc: {ev.get('tkdc_bonus_percent', 0.0)}")
        elif ev_type == "dayun_liunian_branch_clash":
            print(f"  - base_risk: {ev.get('base_risk_percent', 0.0)}, grave_bonus: {ev.get('grave_bonus_percent', 0.0)}, tkdc: {ev.get('tkdc_bonus_percent', 0.0)}")
        elif ev_type == "punishment":
            print(f"  - target_branch: {ev.get('target_branch')}")
    
    # 检查运年相冲
    clashes_dayun = liunian_2030.get("clashes_dayun", [])
    print(f"[DEBUG] 运年相冲数量: {len(clashes_dayun)}")
    for ev in clashes_dayun:
        print(f"[DEBUG] 运年相冲: {ev.get('dayun_branch')} vs {ev.get('liunian_branch')}, risk={ev.get('risk_percent', 0.0)}, tkdc={ev.get('tkdc_bonus_percent', 0.0)}")
    
    # 检查大运的静态冲（dayun_dict中的clashes_natal）
    if dayun_dict_2030:
        dayun_clashes = dayun_dict_2030.get("clashes_natal", [])
        print(f"[DEBUG] 大运静态冲数量: {len(dayun_clashes)}")
        for ev in dayun_clashes:
            print(f"[DEBUG] 大运静态冲: {ev.get('flow_branch')} vs {ev.get('target_branch')}, risk={ev.get('risk_percent', 0.0)}")
            print(f"  - base_power: {ev.get('base_power_percent', 0.0)}, grave_bonus: {ev.get('grave_bonus_percent', 0.0)}, tkdc: {ev.get('tkdc_bonus_percent', 0.0)}")
    
    # 检查静态激活
    static_activation = liunian_2030.get("patterns_static_activation", [])
    print(f"[DEBUG] 静态激活数量: {len(static_activation)}")
    for ev in static_activation:
        print(f"[DEBUG] 静态激活: {ev.get('pattern_type')}, risk={ev.get('risk_percent', 0.0)}, gan={ev.get('risk_from_gan', 0.0)}, zhi={ev.get('risk_from_zhi', 0.0)}")
    
    # 检查静态冲/刑激活事件
    all_events = liunian_2030.get("all_events", [])
    for ev in all_events:
        if ev.get('type') in ('static_clash_activation', 'static_punish_activation'):
            print(f"[DEBUG] 静态冲/刑激活: {ev.get('type')}, risk={ev.get('risk_percent', 0.0)}")


def main():
    print("=" * 60)
    print("开始运行黄金回归用例")
    print("=" * 60)
    
    try:
        print("\n--- 例A：2005-09-20 10:00 男 ---")
        test_case_A_2021()
        test_case_A_2033()
        test_case_A_2059()
        
        print("\n--- 例B：2007-01-28 12:00 男 ---")
        test_case_B_2021()
        test_case_B_2030()
        
        print("\n" + "=" * 60)
        print("所有用例运行完成（暂未断言，仅输出调试信息）")
        print("=" * 60)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
