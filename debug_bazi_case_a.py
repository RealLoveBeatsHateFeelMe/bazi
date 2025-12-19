# -*- coding: utf-8 -*-
from datetime import datetime
from bazi.lunar_engine import analyze_basic

dt = datetime(1981, 9, 15, 10, 0)
info = analyze_basic(dt)
print('bazi:', info['bazi'])
from bazi.harmony import detect_natal_harmonies
print('natal harmonies:')
from pprint import pprint
pprint(info['natal_humnies'] if 'natal_humnies' in info else info.get('natal_harmonies'))
