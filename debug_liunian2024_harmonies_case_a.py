# -*- coding: utf-8 -*-
from datetime import datetime
from pprint import pprint
from bazi.lunar_engine import analyze_basic
from bazi.luck import analyze_luck

print('Debug 例A 2024 年六合')
dt = datetime(1981, 9, 15, 10, 0)
base = analyze_basic(dt)
res = analyze_luck(dt, is_male=True, yongshen_elements=base['yongshen_elements'])
for g in res['groups']:
    dy = g['dayun']
    for ln in g['liunian']:
        if ln['year'] == 2024:
            print('Dayun', dy['gan'], dy['zhi'], 'Liunian', ln['gan'], ln['zhi'])
            print('harmonies_natal:')
            pprint(ln.get('harmonies_natal', []), width=120)
PY