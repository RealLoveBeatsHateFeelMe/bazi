# -*- coding: utf-8 -*-
from bazi.punishment import ALL_PUNISH_PAIRS, NORMAL_PUNISH_PAIRS, GRAVE_PUNISH_PAIRS, SELF_PUNISH_PAIRS

print("所有刑的组合:")
for pair in sorted(ALL_PUNISH_PAIRS):
    print(f"  {pair[0]} {pair[1]}")

print("\n普通刑:")
for pair in sorted(NORMAL_PUNISH_PAIRS):
    print(f"  {pair[0]} {pair[1]}")

print("\n墓库刑:")
for pair in sorted(GRAVE_PUNISH_PAIRS):
    print(f"  {pair[0]} {pair[1]}")

print("\n自刑:")
for pair in sorted(SELF_PUNISH_PAIRS):
    print(f"  {pair[0]} {pair[1]}")

# 检查巳和未是否在刑列表中
print("\n检查巳和未:")
if ("巳", "未") in ALL_PUNISH_PAIRS:
    print("  (巳, 未) 在刑列表中 - 错误！")
else:
    print("  (巳, 未) 不在刑列表中 - 正确")
if ("未", "巳") in ALL_PUNISH_PAIRS:
    print("  (未, 巳) 在刑列表中 - 错误！")
else:
    print("  (未, 巳) 不在刑列表中 - 正确")

