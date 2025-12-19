# -*- coding: utf-8 -*-
"""调试原局刑检测逻辑"""
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import ALL_PUNISH_PAIRS, SELF_PUNISH_PAIRS
from bazi.config import ZHI_CHONG

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]

print("例A八字:")
for pillar in ("year", "month", "day", "hour"):
    print(f"  {pillar}: {bazi[pillar]['zhi']}")

# 手动模拟检测逻辑
print("\n手动模拟检测逻辑:")
pillars = ["year", "month", "day", "hour"]
self_punish_processed = set()
punishments = []

for i, pillar1 in enumerate(pillars):
    for pillar2 in pillars[i + 1 :]:
        zhi1 = bazi[pillar1]["zhi"]
        zhi2 = bazi[pillar2]["zhi"]
        print(f"\n检查: {pillar1}({zhi1}) - {pillar2}({zhi2})")
        
        if (zhi1, zhi2) in ALL_PUNISH_PAIRS:
            print(f"  -> 在刑列表中")
            clash_target = ZHI_CHONG.get(zhi1)
            if clash_target == zhi2:
                print(f"  -> 既冲又刑，跳过")
                continue
            
            is_self = (zhi1, zhi2) in SELF_PUNISH_PAIRS
            print(f"  -> 是自刑: {is_self}")
            
            if is_self:
                if zhi1 in self_punish_processed:
                    print(f"  -> 跳过（{zhi1}已处理，当前集合: {self_punish_processed}）")
                    continue
                self_punish_processed.add(zhi1)
                self_punish_processed.add(zhi2)
                print(f"  -> 添加，标记: {zhi1}, {zhi2}, 当前集合: {self_punish_processed}")
            
            punishments.append({
                "pillar1": pillar1,
                "pillar2": pillar2,
                "zhi1": zhi1,
                "zhi2": zhi2,
                "is_self": is_self,
            })
            print(f"  -> 添加到punishments: {zhi1} {zhi2}, target_pillar={pillar2}")
        else:
            print(f"  -> 不在刑列表中")

print(f"\n手动检测结果: {len(punishments)}个")
for p in punishments:
    print(f"  {p['pillar1']}({p['zhi1']}) - {p['pillar2']}({p['zhi2']}), 自刑={p['is_self']}")

# 使用函数检测
from bazi.punishment import detect_natal_clashes_and_punishments
conflicts = detect_natal_clashes_and_punishments(bazi)
detected_punishments = conflicts.get("punishments", [])
print(f"\n函数检测结果: {len(detected_punishments)}个")
for i, p in enumerate(detected_punishments):
    flow = p.get("flow_branch")
    target = p.get("target_branch")
    risk = p.get("risk_percent", 0.0)
    targets = p.get("targets", [])
    print(f"  {i+1}. {flow} {target} risk={risk}% targets={[t.get('pillar') for t in targets]}")
