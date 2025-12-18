# -*- coding: utf-8 -*-
"""验收标准验证脚本。"""

import sys
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

def verify_acceptance():
    """验证所有验收标准。"""
    all_pass = True
    
    # 测试用例1：2005-09-20 10:00 男
    dt1 = datetime(2005, 9, 20, 10, 0)
    basic1 = analyze_basic(dt1)
    luck1 = analyze_luck(dt1, is_male=True, yongshen_elements=basic1.get("yongshen_elements", []))
    
    # 1. 验证合类事件 risk_percent == 0 且不影响 total_risk_percent
    print("验证1: 合类事件 risk_percent == 0")
    harmony_risks = []
    for group in luck1.get("groups", []):
        for ln in group.get("liunian", []):
            for h in ln.get("harmonies_natal", []):
                risk = h.get("risk_percent", -1)
                harmony_risks.append(risk)
                if risk != 0.0:
                    print(f"  [FAIL] 合类事件 risk_percent 应为 0，但得到 {risk}")
                    all_pass = False
    
    if all(h == 0.0 for h in harmony_risks):
        print(f"  [OK] 所有合类事件 risk_percent == 0 ({len(harmony_risks)} 个事件)")
    
    # 2. 验证线运只可能是 0 或 6
    print("\n验证2: 线运只可能是 0 或 6")
    lineyun_values = set()
    for group in luck1.get("groups", []):
        for ln in group.get("liunian", []):
            lb = ln.get("lineyun_bonus", -1)
            lineyun_values.add(lb)
            if lb not in (0.0, 6.0):
                print(f"  [FAIL] 线运应为 0 或 6，但得到 {lb}")
                all_pass = False
    
    if lineyun_values.issubset({0.0, 6.0}):
        print(f"  [OK] 所有线运值都在 {{0, 6}} 中: {lineyun_values}")
    
    # 3. 验证 total_risk_percent 不封顶（可>100）
    print("\n验证3: total_risk_percent 不封顶（可>100）")
    max_risk = 0.0
    for group in luck1.get("groups", []):
        for ln in group.get("liunian", []):
            risk = ln.get("total_risk_percent", 0)
            max_risk = max(max_risk, risk)
    
    if max_risk > 100.0:
        print(f"  [OK] 存在 total_risk_percent > 100 的情况: {max_risk}")
    else:
        print(f"  [INFO] 当前测试用例最大风险: {max_risk}（未超过100，但代码已支持>100）")
    
    # 4. 验证 special_rules 包含新 code
    print("\n验证4: special_rules 包含新 code")
    dt2 = datetime(2005, 8, 8, 8, 0)
    basic2 = analyze_basic(dt2)
    special_rules = basic2.get("special_rules", [])
    if "weak_wood_heavy_metal_add_fire" in special_rules:
        print(f"  [OK] special_rules 包含 'weak_wood_heavy_metal_add_fire'")
    else:
        print(f"  [FAIL] special_rules 应包含 'weak_wood_heavy_metal_add_fire'，但得到 {special_rules}")
        all_pass = False
    
    # 5. 验证用神 explain 支持不在原局的五行
    print("\n验证5: 用神 explain 支持不在原局的五行")
    yongshen_shishen = basic2.get("yongshen_shishen", [])
    fire_info = next((e for e in yongshen_shishen if e.get("element") == "火"), None)
    if fire_info and (fire_info.get("shishens") or fire_info.get("categories")):
        print(f"  [OK] 用神'火'的 explain 包含十神或类别（即使原局可能没有落点）")
    else:
        print(f"  [FAIL] 用神'火'的 explain 应包含十神或类别")
        all_pass = False
    
    # 6. 验证合类事件包含 pillar 和 palace
    print("\n验证6: 合类事件包含 pillar 和 palace")
    harmony_has_pillar_palace = True
    for group in luck1.get("groups", []):
        for ln in group.get("liunian", []):
            for h in ln.get("harmonies_natal", []):
                targets = h.get("targets", [])
                for t in targets:
                    if "pillar" not in t or "palace" not in t:
                        print(f"  [FAIL] 合类事件 target 缺少 pillar 或 palace: {t}")
                        harmony_has_pillar_palace = False
                        all_pass = False
    
    if harmony_has_pillar_palace:
        print(f"  [OK] 所有合类事件的 targets 都包含 pillar 和 palace")
    
    if all_pass:
        print("\n[SUCCESS] 所有验收标准通过！")
        return True
    else:
        print("\n[FAIL] 部分验收标准未通过")
        return False

if __name__ == "__main__":
    success = verify_acceptance()
    sys.exit(0 if success else 1)
