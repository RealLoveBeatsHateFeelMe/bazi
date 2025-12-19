# -*- coding: utf-8 -*-
from bazi.punishment import ALL_PUNISH_PAIRS

# 检查包含未或巳的刑组合
pairs = [p for p in ALL_PUNISH_PAIRS if '未' in p or '巳' in p]
print('包含未或巳的刑组合:')
for p in sorted(pairs):
    print(f'  {p}')

# 特别检查未巳
print(f"\n('未', '巳') in ALL_PUNISH_PAIRS: {('未', '巳') in ALL_PUNISH_PAIRS}")
print(f"('巳', '未') in ALL_PUNISH_PAIRS: {('巳', '未') in ALL_PUNISH_PAIRS}")
