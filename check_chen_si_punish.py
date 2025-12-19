# -*- coding: utf-8 -*-
"""检查辰巳是否在刑列表中"""
from bazi.punishment import ALL_PUNISH_PAIRS, NORMAL_PUNISH_PAIRS, GRAVE_PUNISH_PAIRS, SELF_PUNISH_PAIRS

print("检查辰巳是否在刑列表中:")
print(f"  ('辰', '巳') in ALL_PUNISH_PAIRS: {('辰', '巳') in ALL_PUNISH_PAIRS}")
print(f"  ('巳', '辰') in ALL_PUNISH_PAIRS: {('巳', '辰') in ALL_PUNISH_PAIRS}")

print("\n所有包含辰的刑组合:")
chen_pairs = [p for p in ALL_PUNISH_PAIRS if '辰' in p]
for p in sorted(chen_pairs):
    print(f"  {p}")

print("\n所有包含巳的刑组合:")
si_pairs = [p for p in ALL_PUNISH_PAIRS if '巳' in p]
for p in sorted(si_pairs):
    print(f"  {p}")

print("\n普通刑列表:")
for p in sorted(NORMAL_PUNISH_PAIRS):
    print(f"  {p}")

print("\n墓库刑列表:")
for p in sorted(GRAVE_PUNISH_PAIRS):
    print(f"  {p}")

print("\n自刑列表:")
for p in sorted(SELF_PUNISH_PAIRS):
    print(f"  {p}")
