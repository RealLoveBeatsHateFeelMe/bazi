# -*- coding: utf-8 -*-
"""facts 唯一真相源入口。

规则：
- facts = compute_facts(...) 的返回必须等同于打印层展示的结构化输出（同一次运行结果）
- Router/API/LLM 只能从这个 facts 取事实内容
"""

from datetime import datetime
from typing import Any, Dict

from .lunar_engine import analyze_complete


def compute_facts(birth_dt: datetime, is_male: bool, max_dayun: int = 15) -> Dict[str, Any]:
    """生成 facts（唯一真相源）。"""
    facts = analyze_complete(birth_dt, is_male, max_dayun=max_dayun)
    return facts


