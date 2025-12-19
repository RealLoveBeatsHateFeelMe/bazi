# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import detect_natal_clashes_and_punishments

# 检查例A：酉酉自刑
print("=" * 60)
print("检查例A：1981-09-15 10:00 - 酉酉自刑")
print("=" * 60)
dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"八字: {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")
print(f"年柱地支: {bazi['year']['zhi']}")
print(f"月柱地支: {bazi['month']['zhi']}")
print(f"日柱地支: {bazi['day']['zhi']}")
print(f"时柱地支: {bazi['hour']['zhi']}")

conflicts = detect_natal_clashes_and_punishments(bazi)
punishments = conflicts.get("punishments", [])
print(f"\n检测到的原局刑: {len(punishments)}个")
total = 0.0
for p in punishments:
    risk = p.get("risk_percent", 0.0)
    total += risk
    print(f"  {p.get('flow_branch')} {p.get('target_branch')} risk={risk}%")
print(f"总风险: {total}%")
print(f"期望: 5%（只有年柱和月柱是酉，应该只有1个酉酉自刑）")
if total == 5.0:
    print("✓ 例A修复成功")
else:
    print(f"✗ 例A修复失败，实际总风险是{total}%")

