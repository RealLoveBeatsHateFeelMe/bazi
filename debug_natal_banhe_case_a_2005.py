# -*- coding: utf-8 -*-
from datetime import datetime
from pprint import pprint
from bazi.lunar_engine import analyze_basic

print("Debug 2005-09-20 10:00 natal banhe")
dt = datetime(2005, 9, 20, 10, 0)
info = analyze_basic(dt)
print("bazi:", info["bazi"])
print("natal_harmonies:")
for ev in info.get("natal_harmonies", []):
    if ev.get("subtype") == "banhe":
        pprint(ev, width=120)
