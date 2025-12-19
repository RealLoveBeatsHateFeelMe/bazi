# -*- coding: utf-8 -*-
"""详细分析刑的逻辑，准确打印八字"""
from datetime import datetime
from bazi.lunar_engine import analyze_basic
from bazi.punishment import (
    ALL_PUNISH_PAIRS, NORMAL_PUNISH_PAIRS, GRAVE_PUNISH_PAIRS, SELF_PUNISH_PAIRS,
    detect_natal_clashes_and_punishments
)
from bazi.config import ZHI_CHONG

def print_bazi_with_unicode(bazi, label=""):
    """用Unicode编码清晰打印八字"""
    if label:
        print(f"\n{'='*60}")
        print(f"{label}")
        print(f"{'='*60}")
    
    # 使用repr来显示准确的字符
    print("八字（使用repr显示准确字符）:")
    print(f"  年柱: gan={repr(bazi['year']['gan'])}, zhi={repr(bazi['year']['zhi'])}")
    print(f"  月柱: gan={repr(bazi['month']['gan'])}, zhi={repr(bazi['month']['zhi'])}")
    print(f"  日柱: gan={repr(bazi['day']['gan'])}, zhi={repr(bazi['day']['zhi'])}")
    print(f"  时柱: gan={repr(bazi['hour']['gan'])}, zhi={repr(bazi['hour']['zhi'])}")
    
    # 也打印正常显示
    print("\n八字正常显示:")
    print(f"  {bazi['year']['gan']}{bazi['year']['zhi']} {bazi['month']['gan']}{bazi['month']['zhi']} {bazi['day']['gan']}{bazi['day']['zhi']} {bazi['hour']['gan']}{bazi['hour']['zhi']}")

# 例A
dt_a = datetime(1981, 9, 15, 10, 0)
basic_a = analyze_basic(dt_a)
bazi_a = basic_a["bazi"]
print_bazi_with_unicode(bazi_a, "例A：1981-09-15 10:00")

# 手动模拟原局刑检测逻辑
print("\n" + "="*60)
print("手动模拟原局刑检测逻辑")
print("="*60)

pillars = ["year", "month", "day", "hour"]
self_punish_processed = set()
detected_punishments = []

print("\n所有柱对检查:")
for i, pillar1 in enumerate(pillars):
    for pillar2 in pillars[i + 1 :]:
        zhi1 = bazi_a[pillar1]["zhi"]
        zhi2 = bazi_a[pillar2]["zhi"]
        
        print(f"\n检查: {pillar1}({repr(zhi1)}) - {pillar2}({repr(zhi2)})")
        print(f"  zhi1={zhi1}, zhi2={zhi2}")
        
        # 检查是否在刑列表中
        pair = (zhi1, zhi2)
        in_all_pairs = pair in ALL_PUNISH_PAIRS
        print(f"  ({repr(zhi1)}, {repr(zhi2)}) in ALL_PUNISH_PAIRS: {in_all_pairs}")
        
        if in_all_pairs:
            # 检查是否既冲又刑
            clash_target = ZHI_CHONG.get(zhi1)
            is_clash = clash_target == zhi2
            print(f"  既冲又刑: {is_clash} (clash_target={repr(clash_target)})")
            
            if is_clash:
                print(f"  -> 跳过（既冲又刑，只算冲）")
                continue
            
            # 判断刑的类型
            is_grave = pair in GRAVE_PUNISH_PAIRS
            is_self = pair in SELF_PUNISH_PAIRS
            is_normal = pair in NORMAL_PUNISH_PAIRS
            
            print(f"  刑类型: 墓库刑={is_grave}, 自刑={is_self}, 普通刑={is_normal}")
            
            # 对于自刑，检查是否已处理
            if is_self:
                if zhi1 in self_punish_processed:
                    print(f"  -> 跳过（{repr(zhi1)}已处理，当前集合: {self_punish_processed}）")
                    continue
                self_punish_processed.add(zhi1)
                self_punish_processed.add(zhi2)
                print(f"  -> 添加自刑，标记: {repr(zhi1)}, {repr(zhi2)}, 当前集合: {self_punish_processed}")
            
            detected_punishments.append({
                "pillar1": pillar1,
                "pillar2": pillar2,
                "zhi1": zhi1,
                "zhi2": zhi2,
                "is_grave": is_grave,
                "is_self": is_self,
            })
            print(f"  -> 添加到检测结果")
        else:
            print(f"  -> 不在刑列表中")

print(f"\n手动检测结果: {len(detected_punishments)}个")
for p in detected_punishments:
    print(f"  {p['pillar1']}({repr(p['zhi1'])}) - {p['pillar2']}({repr(p['zhi2'])}), 墓库刑={p['is_grave']}, 自刑={p['is_self']}")

# 使用函数检测
print("\n" + "="*60)
print("函数检测结果")
print("="*60)
conflicts = detect_natal_clashes_and_punishments(bazi_a)
punishments = conflicts.get("punishments", [])
print(f"\n函数检测到: {len(punishments)}个刑事件")
for i, p in enumerate(punishments):
    flow = p.get("flow_branch")
    target = p.get("target_branch")
    risk = p.get("risk_percent", 0.0)
    targets = p.get("targets", [])
    print(f"  {i+1}. flow_branch={repr(flow)}, target_branch={repr(target)}, risk={risk}%, targets={[t.get('pillar') for t in targets]}")
