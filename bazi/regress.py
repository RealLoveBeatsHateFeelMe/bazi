# -*- coding: utf-8 -*-
"""回归测试：确保关键业务规则不被破坏。"""

import sys
from datetime import datetime

from .punishment import ALL_PUNISH_PAIRS, GRAVE_PUNISH_PAIRS, detect_branch_punishments
from .lunar_engine import analyze_basic
from .luck import analyze_luck


def test_chenwei_not_punishment():
    """断言：辰未不刑（防止误加回去）。"""
    assert ("辰", "未") not in ALL_PUNISH_PAIRS, "辰未不应该在 ALL_PUNISH_PAIRS 中"
    assert ("未", "辰") not in ALL_PUNISH_PAIRS, "未辰不应该在 ALL_PUNISH_PAIRS 中"
    assert ("辰", "未") not in GRAVE_PUNISH_PAIRS, "辰未不应该在 GRAVE_PUNISH_PAIRS 中"
    assert ("未", "辰") not in GRAVE_PUNISH_PAIRS, "未辰不应该在 GRAVE_PUNISH_PAIRS 中"
    print("[PASS] 辰未不刑断言通过")


def test_chen_no_wei_target():
    """断言：任意盘对 flow_branch='辰' 的 detect_branch_punishments 不应出现 target_branch='未'。"""
    # 构造一个包含未的测试八字
    test_bazi = {
        "year": {"gan": "甲", "zhi": "未"},
        "month": {"gan": "乙", "zhi": "寅"},
        "day": {"gan": "丙", "zhi": "子"},
        "hour": {"gan": "丁", "zhi": "卯"},
    }
    
    # 检测 flow_branch="辰" 的刑
    events = detect_branch_punishments(
        bazi=test_bazi,
        flow_branch="辰",
        flow_type="test",
    )
    
    # 验证没有任何事件的 target_branch 是 "未"
    for ev in events:
        assert ev.get("target_branch") != "未", f"flow_branch='辰' 不应检测到 target_branch='未'，但得到事件: {ev}"
    
    print("[PASS] 辰不刑未的运行时断言通过")


def _assert_close(actual: float, expected: float, tol: float = 0.5) -> None:
    """浮点比较辅助函数，默认允许 0.5% 误差。"""
    assert abs(actual - expected) <= tol, f"expected {expected}, got {actual}"


def _get_dominant_traits(year: int, month: int, day: int, hour: int, minute: int):
    """便于 traits 回归直接取出 dominant_traits。"""
    dt = datetime(year, month, day, hour, minute)
    basic = analyze_basic(dt)
    traits = basic.get("dominant_traits") or []
    return traits


def test_traits_T1():
    """Traits 回归 T-1：2005-09-20 10:00 男 M。"""
    traits = _get_dominant_traits(2005, 9, 20, 10, 0)

    # 辅助：按 group / name 索引
    def find_group(traits_list, group_name):
        for t in traits_list:
            if t.get("group") == group_name:
                return t
        return {}

    def detail_map(trait):
        return {d.get("name"): d for d in (trait.get("detail") or [])}

    yin = find_group(traits, "印")
    cai = find_group(traits, "财")

    # 印：total_percent = 30；偏印=30，正印=0；mix_label = “纯偏印”；偏印 stems_visible_count = 3
    _assert_close(yin.get("total_percent", 0.0), 30.0, tol=0.1)
    assert yin.get("mix_label") == "纯偏印"
    yin_dm = detail_map(yin)
    _assert_close(yin_dm["偏印"]["percent"], 30.0, tol=0.1)
    _assert_close(yin_dm["正印"]["percent"], 0.0, tol=0.1)
    assert yin_dm["偏印"]["stems_visible_count"] == 3

    # 财：total_percent = 45；偏财=45，正财=0；mix_label = “纯偏财”
    _assert_close(cai.get("total_percent", 0.0), 45.0, tol=0.1)
    assert cai.get("mix_label") == "纯偏财"
    cai_dm = detail_map(cai)
    _assert_close(cai_dm["偏财"]["percent"], 45.0, tol=0.1)
    _assert_close(cai_dm["正财"]["percent"], 0.0, tol=0.1)

    print("[PASS] traits T-1 用例通过")


def test_traits_T2():
    """Traits 回归 T-2：2007-01-28 12:00 男 M。"""
    traits = _get_dominant_traits(2007, 1, 28, 12, 0)

    def find_group(traits_list, group_name):
        for t in traits_list:
            if t.get("group") == group_name:
                return t
        return {}

    def detail_map(trait):
        return {d.get("name"): d for d in (trait.get("detail") or [])}

    cai = find_group(traits, "财")
    guansha = find_group(traits, "官杀")

    # 财：total_percent = 35；偏财=20（干），正财=15（支）；mix_label = “正偏财混杂”；偏财 stems_visible_count = 2
    _assert_close(cai.get("total_percent", 0.0), 35.0, tol=0.1)
    assert cai.get("mix_label") == "正偏财混杂"
    cai_dm = detail_map(cai)
    _assert_close(cai_dm["偏财"]["percent"], 20.0, tol=0.1)
    _assert_close(cai_dm["正财"]["percent"], 15.0, tol=0.1)
    assert cai_dm["偏财"]["stems_visible_count"] == 2

    # 官杀：正官=35、七杀=20、total=55；mix_label = “官杀混杂”
    _assert_close(guansha.get("total_percent", 0.0), 55.0, tol=0.1)
    assert guansha.get("mix_label") == "官杀混杂"
    gs_dm = detail_map(guansha)
    _assert_close(gs_dm["正官"]["percent"], 35.0, tol=0.1)
    _assert_close(gs_dm["七杀"]["percent"], 20.0, tol=0.1)

    print("[PASS] traits T-2 用例通过")


def test_yongshen_special_rule_wood():
    """用神补木回归：2007-01-28 12:00 锁死 base/final 差异 + explain 走 final。"""
    dt = datetime(2007, 1, 28, 12, 0)
    basic = analyze_basic(dt)

    yongshen_elements = basic.get("yongshen_elements", [])
    yongshen_detail = basic.get("yongshen_detail", {})
    base_yongshen = yongshen_detail.get("base_yongshen_elements", [])
    final_yongshen = yongshen_detail.get("final_yongshen_elements", [])

    # 断言：顶层 == detail.final 永远一致
    assert yongshen_elements == final_yongshen, f"顶层用神 {yongshen_elements} != detail.final {final_yongshen}"

    # 断言：base 不含"木"，final 含"木"（因为 special rule）
    assert "木" not in base_yongshen, f"base 用神不应含'木'，但得到 {base_yongshen}"
    assert "木" in final_yongshen, f"final 用神应含'木'，但得到 {final_yongshen}"

    # 断言：explain 按 final 计算（至少有一条"木"的 shishen 或 tokens）
    yongshen_shishen = basic.get("yongshen_shishen", [])
    yongshen_tokens = basic.get("yongshen_tokens", [])

    # 找到"木"的 explain
    mu_shishen = None
    for entry in yongshen_shishen:
        if entry.get("element") == "木":
            mu_shishen = entry
            break

    assert mu_shishen is not None, "yongshen_shishen 中应包含'木'的条目"
    # 即使原局没有木，也应该有理论十神（因为 explain 支持不在原局的五行）
    assert len(mu_shishen.get("shishens", [])) > 0 or len(mu_shishen.get("categories", [])) > 0, \
        "用神'木'的 explain 应包含十神或类别（即使原局没有落点）"

    print("[PASS] 用神补木回归通过")


def test_yongshen_special_rule_fire():
    """用神补火回归：2005-08-08 08:00 断言 final 用神 == ["水","木","火"]。"""
    dt = datetime(2005, 8, 8, 8, 0)
    basic = analyze_basic(dt)

    yongshen_elements = basic.get("yongshen_elements", [])
    yongshen_detail = basic.get("yongshen_detail", {})
    base_yongshen = yongshen_detail.get("base_yongshen_elements", [])
    final_yongshen = yongshen_detail.get("final_yongshen_elements", [])
    special_rules = basic.get("special_rules", [])

    # 断言：顶层 == detail.final 永远一致
    assert yongshen_elements == final_yongshen, f"顶层用神 {yongshen_elements} != detail.final {final_yongshen}"

    # 断言：final 用神包含 ["水","木","火"]（顺序可不同，但必须都包含）
    final_set = set(final_yongshen)
    assert "水" in final_set, f"final 用神应含'水'，但得到 {final_yongshen}"
    assert "木" in final_set, f"final 用神应含'木'，但得到 {final_yongshen}"
    assert "火" in final_set, f"final 用神应含'火'，但得到 {final_yongshen}"

    # 断言：base 用神应为水木（补火前）
    base_set = set(base_yongshen)
    assert base_set == {"水", "木"} or base_set == {"木", "水"}, \
        f"base 用神应为水木，但得到 {base_yongshen}"

    # 断言：special_rules 包含补火规则
    assert "weak_wood_heavy_metal_add_fire" in special_rules, \
        f"special_rules 应包含 'weak_wood_heavy_metal_add_fire'，但得到 {special_rules}"

    # 断言：explain 按 final 计算（"火"的 explain 应存在）
    yongshen_shishen = basic.get("yongshen_shishen", [])
    fire_shishen = None
    for entry in yongshen_shishen:
        if entry.get("element") == "火":
            fire_shishen = entry
            break

    assert fire_shishen is not None, "yongshen_shishen 中应包含'火'的条目"
    # 即使原局没有火，也应该有理论十神
    assert len(fire_shishen.get("shishens", [])) > 0 or len(fire_shishen.get("categories", [])) > 0, \
        "用神'火'的 explain 应包含十神或类别（即使原局没有落点）"

    print("[PASS] 用神补火回归通过")


def test_lineyun_case_a():
    """线运回归 case A：命中 active_pillar 的 base 事件 risk=9.9 → 不触发（lineyun_bonus=0）。"""
    # 构造一个事件列表，risk_percent=9.9，命中 active_pillar
    from .luck import _compute_lineyun_bonus
    
    # 年龄 20（active_pillar = "month"）
    age = 20
    base_events = [{
        "type": "branch_clash",
        "role": "base",
        "risk_percent": 9.9,
        "targets": [{
            "pillar": "month",
            "position_weight": 0.35,
        }],
    }]
    
    lineyun_event = _compute_lineyun_bonus(age, base_events)
    assert lineyun_event is None, f"risk=9.9 不应触发线运，但得到 {lineyun_event}"
    
    print("[PASS] 线运 case A 回归通过")


def test_lineyun_case_b():
    """线运回归 case B：命中 active_pillar 的 base 事件 risk=10.0 → 触发（lineyun_bonus=6）。"""
    from .luck import _compute_lineyun_bonus
    
    # 年龄 20（active_pillar = "month"）
    age = 20
    base_events = [{
        "type": "branch_clash",
        "role": "base",
        "risk_percent": 10.0,
        "targets": [{
            "pillar": "month",
            "position_weight": 0.35,
        }],
    }]
    
    lineyun_event = _compute_lineyun_bonus(age, base_events)
    assert lineyun_event is not None, "risk=10.0 应触发线运"
    assert lineyun_event.get("risk_percent") == 6.0, f"线运加成应为 6.0，但得到 {lineyun_event.get('risk_percent')}"
    assert lineyun_event.get("active_pillar") == "month", f"active_pillar 应为 'month'，但得到 {lineyun_event.get('active_pillar')}"
    
    print("[PASS] 线运 case B 回归通过")


def test_harmonies_2005_09_20():
    """合类事件回归：2005-09-20 10:00 男，检查 2024/2025/2026 的合类事件。"""
    dt = datetime(2005, 9, 20, 10, 0)
    basic = analyze_basic(dt)
    yongshen_elements = basic.get("yongshen_elements", [])
    
    luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)
    
    # 查找 2024/2025/2026 的流年
    found_2024 = False
    found_2025 = False
    found_2026 = False
    
    for group in luck.get("groups", []):
        for liunian in group.get("liunian", []):
            year = liunian.get("year")
            if year == 2024:
                found_2024 = True
                harmonies = liunian.get("harmonies_natal", [])
                # 2024：辰酉合（liuhe），命中 年柱=根基宫、月柱=婚姻宫
                chen_you_liuhe = None
                for h in harmonies:
                    if h.get("subtype") == "liuhe" and "辰" in h.get("matched_branches", []) and "酉" in h.get("matched_branches", []):
                        chen_you_liuhe = h
                        break
                assert chen_you_liuhe is not None, "2024 年应检测到辰酉六合"
                assert chen_you_liuhe.get("risk_percent") == 0.0, "合类事件 risk_percent 应为 0"
                targets = chen_you_liuhe.get("targets", [])
                pillars = {t.get("pillar") for t in targets}
                assert "year" in pillars or "month" in pillars, "辰酉合应命中年柱或月柱"
            elif year == 2025:
                found_2025 = True
                harmonies = liunian.get("harmonies_natal", [])
                # 2025：巳酉半合（banhe，金局/巳酉丑），命中 年柱=根基宫、月柱=婚姻宫
                si_you_banhe = None
                for h in harmonies:
                    if h.get("subtype") == "banhe" and "巳" in h.get("matched_branches", []) and "酉" in h.get("matched_branches", []):
                        si_you_banhe = h
                        break
                assert si_you_banhe is not None, "2025 年应检测到巳酉半合"
                assert si_you_banhe.get("risk_percent") == 0.0, "合类事件 risk_percent 应为 0"
            elif year == 2026:
                found_2026 = True
                harmonies = liunian.get("harmonies_natal", [])
                # 2026：巳午未三会（sanhui），以及 午未六合（liuhe）
                sanhui_found = False
                liuhe_found = False
                for h in harmonies:
                    if h.get("subtype") == "sanhui" and set(h.get("matched_branches", [])) == {"巳", "午", "未"}:
                        sanhui_found = True
                        assert h.get("risk_percent") == 0.0, "合类事件 risk_percent 应为 0"
                    elif h.get("subtype") == "liuhe" and "午" in h.get("matched_branches", []) and "未" in h.get("matched_branches", []):
                        liuhe_found = True
                        assert h.get("risk_percent") == 0.0, "合类事件 risk_percent 应为 0"
                assert sanhui_found or liuhe_found, "2026 年应检测到三会或六合"
    
    assert found_2024 and found_2025 and found_2026, "应找到 2024/2025/2026 的流年数据"
    
    print("[PASS] 合类事件 2005-09-20 回归通过")


def test_harmonies_2007_01_28():
    """合类事件回归：2007-01-28 12:00 男，检查 2022/2020 的合类事件。"""
    dt = datetime(2007, 1, 28, 12, 0)
    basic = analyze_basic(dt)
    yongshen_elements = basic.get("yongshen_elements", [])
    
    luck = analyze_luck(dt, is_male=True, yongshen_elements=yongshen_elements)
    
    # 查找 2022/2020 的流年
    found_2022 = False
    found_2020 = False
    
    for group in luck.get("groups", []):
        for liunian in group.get("liunian", []):
            year = liunian.get("year")
            if year == 2022:
                found_2022 = True
                harmonies = liunian.get("harmonies_natal", [])
                # 2022：寅午戌三合（sanhe，火局）
                yin_wu_xu_sanhe = None
                for h in harmonies:
                    if h.get("subtype") == "sanhe" and set(h.get("matched_branches", [])) == {"寅", "午", "戌"}:
                        yin_wu_xu_sanhe = h
                        break
                assert yin_wu_xu_sanhe is not None, "2022 年应检测到寅午戌三合"
                assert yin_wu_xu_sanhe.get("risk_percent") == 0.0, "合类事件 risk_percent 应为 0"
            elif year == 2020:
                found_2020 = True
                harmonies = liunian.get("harmonies_natal", [])
                # 2020：子丑合（liuhe）
                zi_chou_liuhe = None
                for h in harmonies:
                    if h.get("subtype") == "liuhe" and "子" in h.get("matched_branches", []) and "丑" in h.get("matched_branches", []):
                        zi_chou_liuhe = h
                        break
                assert zi_chou_liuhe is not None, "2020 年应检测到子丑六合"
                assert zi_chou_liuhe.get("risk_percent") == 0.0, "合类事件 risk_percent 应为 0"
    
    assert found_2022 and found_2020, "应找到 2022/2020 的流年数据"
    
    print("[PASS] 合类事件 2007-01-28 回归通过")


def main():
    try:
        test_chenwei_not_punishment()
        test_chen_no_wei_target()
        test_traits_T1()
        test_traits_T2()
        test_yongshen_special_rule_wood()
        test_yongshen_special_rule_fire()
        test_lineyun_case_a()
        test_lineyun_case_b()
        test_harmonies_2005_09_20()
        test_harmonies_2007_01_28()
        print("ALL REGRESSION TESTS PASS")
    except AssertionError as e:
        print(f"REGRESSION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"REGRESSION ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

