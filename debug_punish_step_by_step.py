# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import ALL_PUNISH_PAIRS, SELF_PUNISH_PAIRS
from bazi.config import ZHI_CHONG

dt = datetime(1981, 9, 15, 10, 0)
basic = analyze_basic(dt)
bazi = basic["bazi"]
print(f"例A八字: {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 手动模拟检测逻辑，逐步打印
print("\n逐步模拟检测逻辑:")
pillars = ["year", "month", "day", "hour"]
self_punish_processed = set()
punishments = []

for i, pillar1 in enumerate(pillars):
    for pillar2 in pillars[i + 1 :]:
        zhi1 = bazi[pillar1]["zhi"]
        zhi2 = bazi[pillar2]["zhi"]
        print(f"\n检查: {pillar1}({zhi1}) - {pillar2}({zhi2})")
        print(f"  ('{zhi1}', '{zhi2}') in ALL_PUNISH_PAIRS: {((zhi1, zhi2) in ALL_PUNISH_PAIRS)}")
        
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
            print(f"  -> 添加到punishments列表")
        else:
            print(f"  -> 不在刑列表中")

print(f"\n最终结果: {len(punishments)}个刑事件")
for p in punishments:
    print(f"  {p['pillar1']}({p['zhi1']}) - {p['pillar2']}({p['zhi2']}), 自刑={p['is_self']}")
