# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck
from bazi.punishment import detect_natal_clashes_and_punishments, detect_branch_punishments

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"例A八字: {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 检查原局刑
conflicts = detect_natal_clashes_and_punishments(bazi)
natal_punishments = conflicts.get("punishments", [])
print(f"\n原局刑: {len(natal_punishments)}个")
for p in natal_punishments:
    print(f"  {p.get('flow_branch')} {p.get('target_branch')} risk={p.get('risk_percent', 0.0)}%")

# 检查2017年流年刑
print("\n2017年流年刑:")
punishments_ln = detect_branch_punishments(bazi, "酉", "liunian", 2017, "丁酉")
print(f"  数量: {len(punishments_ln)}个")
for ev in punishments_ln:
    targets = ev.get("targets", [])
    print(f"  {ev.get('flow_branch')} {ev.get('target_branch')} risk={ev.get('risk_percent', 0.0)}% targets={[t.get('pillar') for t in targets]}")

# 检查静态刑激活逻辑
print("\n检查静态刑激活:")
zhi_ln = "酉"
ln_punish_pairs = {(ev.get("flow_branch"), ev.get("target_branch")) for ev in punishments_ln}
print(f"  流年刑组合: {ln_punish_pairs}")

activated_punish_evs = []
for natal_punish_ev in natal_punishments:
    natal_flow = natal_punish_ev.get("flow_branch")
    natal_target = natal_punish_ev.get("target_branch")
    print(f"  原局刑: {natal_flow} {natal_target}")
    
    # 检查是否与流年刑相同
    condition1 = zhi_ln == natal_flow and natal_target in {ev.get("target_branch") for ev in punishments_ln}
    condition2 = zhi_ln == natal_target and natal_flow in {ev.get("target_branch") for ev in punishments_ln}
    print(f"    condition1: {condition1} (zhi_ln={zhi_ln} == natal_flow={natal_flow} and natal_target={natal_target} in {[ev.get('target_branch') for ev in punishments_ln]})")
    print(f"    condition2: {condition2} (zhi_ln={zhi_ln} == natal_target={natal_target} and natal_flow={natal_flow} in {[ev.get('target_branch') for ev in punishments_ln]})")
    
    if condition1 or condition2:
        print(f"    -> 激活！")
        activated_punish_evs.append(natal_punish_ev)
    else:
        print(f"    -> 不激活")

# 计算静态刑激活风险
static_punish_activation_risk = 0.0
for punish_ev in activated_punish_evs:
    static_punish_risk_per_event = punish_ev.get("risk_percent", 0.0) * 0.5
    print(f"\n  激活的静态刑: {punish_ev.get('flow_branch')} {punish_ev.get('target_branch')} risk={punish_ev.get('risk_percent', 0.0)}% -> 激活风险={static_punish_risk_per_event}%")
    static_punish_activation_risk += static_punish_risk_per_event

print(f"\n静态刑激活总风险: {static_punish_activation_risk}%")
print(f"期望: 静态刑应该是5%（原局酉酉自刑只算一次）")
