# -*- coding: utf-8 -*-
"""导出 traits 相关的 AnalyzeBasic 样例 JSON，供 partner / 前端使用。"""

from __future__ import annotations

import json
import os
from datetime import datetime

from .lunar_engine import analyze_basic


FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")


def _ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def export_fixtures() -> None:
    _ensure_dir(FIXTURES_DIR)

    cases = [
        ("traits_T1_2005.json", datetime(2005, 9, 20, 10, 0)),
        ("traits_T2_2007.json", datetime(2007, 1, 28, 12, 0)),
    ]

    for filename, dt in cases:
        basic = analyze_basic(dt)
        path = os.path.join(FIXTURES_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(basic, f, ensure_ascii=False, indent=2)


def main() -> None:
    export_fixtures()


if __name__ == "__main__":
    main()


