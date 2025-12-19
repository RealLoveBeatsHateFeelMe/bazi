# -*- coding: utf-8 -*-
from bazi.punishment import ALL_PUNISH_PAIRS, NORMAL_PUNISH_PAIRS, GRAVE_PUNISH_PAIRS, SELF_PUNISH_PAIRS

print("检查未巳是否在刑列表中:")
print(f"  ('未', '巳') in ALL_PUNISH_PAIRS: {('未', '巳') in ALL_PUNISH_PAIRS}")
print(f"  ('巳', '未') in ALL_PUNISH_PAIRS: {('巳', '未') in ALL_PUNISH_PAIRS}")
print(f"  ('未', '巳') in NORMAL_PUNISH_PAIRS: {('未', '巳') in NORMAL_PUNISH_PAIRS}")
print(f"  ('巳', '未') in NORMAL_PUNISH_PAIRS: {('巳', '未') in NORMAL_PUNISH_PAIRS}")
print(f"  ('未', '巳') in GRAVE_PUNISH_PAIRS: {('未', '巳') in GRAVE_PUNISH_PAIRS}")
print(f"  ('巳', '未') in GRAVE_PUNISH_PAIRS: {('巳', '未') in GRAVE_PUNISH_PAIRS}")

print("\n所有刑的组合:")
for pair in sorted(ALL_PUNISH_PAIRS):
    print(f"  {pair}")
