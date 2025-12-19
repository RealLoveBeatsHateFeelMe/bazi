# -*- coding: utf-8 -*-
"""测试例A原局刑：应该只有1个酉酉自刑（年-月），5%"""
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import detect_natal_clashes_and_punishments

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]

print("例A八字:")
print(f"年柱: {bazi['year']['gan']}{bazi['year']['zhi']}")
print(f"月柱: {bazi['month']['gan']}{bazi['month']['zhi']}")
print(f"日柱: {bazi['day']['gan']}{bazi['day']['zhi']}")
print(f"时柱: {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 验证八字
assert bazi['year']['zhi'] == "酉", f"年柱地支应该是酉，但得到{bazi['year']['zhi']}"
assert bazi['month']['zhi'] == "酉", f"月柱地支应该是酉，但得到{bazi['month']['zhi']}"

conflicts = detect_natal_clashes_and_punishments(bazi)
punishments = conflicts.get("punishments", [])
print(f"\n检测到的原局刑: {len(punishments)}个")

youyou_count = 0
total_risk = 0.0
for i, p in enumerate(punishments):
    flow = p.get("flow_branch")
    target = p.get("target_branch")
    risk = p.get("risk_percent", 0.0)
    targets = p.get("targets", [])
    total_risk += risk
    print(f"  {i+1}. {flow} {target} risk={risk}% targets={[t.get('pillar') for t in targets]}")
    if flow == "酉" and target == "酉":
        youyou_count += 1

print(f"\n酉酉自刑数量: {youyou_count}")
print(f"总风险: {total_risk}%")
print(f"期望: 1个酉酉自刑，5%")

assert youyou_count == 1, f"应检测到1个酉酉自刑，但得到{youyou_count}个"
assert total_risk == 5.0, f"总风险应为5.0%，但得到{total_risk}%"

print("\n✓ 例A原局刑检测正确！")
