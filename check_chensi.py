# -*- coding: utf-8 -*-
from bazi.punishment import ALL_PUNISH_PAIRS

# 检查辰巳是否在刑列表中
print(f"('辰', '巳') in ALL_PUNISH_PAIRS: {('辰', '巳') in ALL_PUNISH_PAIRS}")
print(f"('巳', '辰') in ALL_PUNISH_PAIRS: {('巳', '辰') in ALL_PUNISH_PAIRS}")

# 列出所有包含辰或巳的刑组合
pairs = [p for p in ALL_PUNISH_PAIRS if '辰' in p or '巳' in p]
print(f"\n包含辰或巳的刑组合:")
for p in sorted(pairs):
    print(f"  {p}")
