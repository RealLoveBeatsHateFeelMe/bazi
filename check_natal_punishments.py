# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import detect_natal_clashes_and_punishments

# 例A
print("=" * 50)
print("例A：1981-09-15 10:00")
dt_a = datetime(1981, 9, 15, 10, 0)
basic_a = analyze_basic(dt_a)
bazi_a = basic_a["bazi"]
print(f"八字: {bazi_a['year']['gan']}{bazi_a['year']['zhi']} {bazi_a['month']['gan']}{bazi_a['month']['zhi']} {bazi_a['day']['gan']}{bazi_a['day']['zhi']} {bazi_a['hour']['gan']}{bazi_a['hour']['zhi']}")

conflicts_a = detect_natal_clashes_and_punishments(bazi_a)
punishments_a = conflicts_a.get("punishments", [])
print(f"\n原局刑: {len(punishments_a)}个")
total_risk_a = 0.0
for p in punishments_a:
    risk = p.get("risk_percent", 0.0)
    total_risk_a += risk
    print(f"  {p.get('flow_branch')} {p.get('target_branch')} risk={risk}%")
print(f"总风险: {total_risk_a}%")
print(f"期望: 1个酉酉自刑，5%")

# 例B
print("\n" + "=" * 50)
print("例B：2007-01-28 12:00")
dt_b = datetime(2007, 1, 28, 12, 0)
basic_b = analyze_basic(dt_b)
bazi_b = basic_b["bazi"]
print(f"八字: {bazi_b['year']['gan']}{bazi_b['year']['zhi']} {bazi_b['month']['gan']}{bazi_b['month']['zhi']} {bazi_b['day']['gan']}{bazi_b['day']['zhi']} {bazi_b['hour']['gan']}{bazi_b['hour']['zhi']}")

conflicts_b = detect_natal_clashes_and_punishments(bazi_b)
punishments_b = conflicts_b.get("punishments", [])
print(f"\n原局刑: {len(punishments_b)}个")
total_risk_b = 0.0
for p in punishments_b:
    risk = p.get("risk_percent", 0.0)
    total_risk_b += risk
    print(f"  {p.get('flow_branch')} {p.get('target_branch')} risk={risk}%")
print(f"总风险: {total_risk_b}%")
print(f"期望: 2个丑戌刑，各6%，共12%")
