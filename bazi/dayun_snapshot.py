# -*- coding: utf-8 -*-
"""大运快照生成模块。

生成大运整体走势的快速概览，包含：
- 运势好坏（基于地支是否用神）
- 职业五行（原局用神或互换后的五行）
- 用神互换提示

设计原则：
- 打印层用 #PAID_START# / #PAID_END# 标记付费内容
- 后期统一裁剪，方便 debug 时看到完整输出
"""

from typing import Any, Dict, List, Optional


def build_dayun_snapshot(facts: Dict[str, Any], base_year: int) -> str:
    """生成大运快照文本。

    参数:
        facts: compute_facts() 返回的完整 facts
        base_year: 基准年份（用于判断当前大运）

    返回:
        完整文本，付费内容用 #PAID_START# / #PAID_END# 标记
    """
    lines = ["—— 大运快照 ——", ""]

    # 收集有效大运
    dayuns = [g['dayun'] for g in facts['luck']['groups'] if g.get('dayun')]

    if not dayuns:
        lines.append("大运尚未开始")
        return "\n".join(lines)

    # 找当前大运索引
    current_idx = _find_current_dayun_idx(dayuns, base_year)

    # 计算免费区和付费区范围
    free_start, free_end, paid_start, paid_end = _calculate_ranges(
        dayuns, current_idx
    )

    # 生成免费区（所有用户都能看到）
    lines.append("[过去与当前]")
    for i in range(free_start, free_end):
        lines.append(_format_dayun_line(dayuns[i], facts, i == current_idx))

    # 付费区：用标记包裹
    if paid_start < paid_end:
        lines.append("#PAID_START#")
        lines.append("")
        lines.append("[未来大运]")
        for i in range(paid_start, paid_end):
            lines.append(_format_dayun_line(dayuns[i], facts, False))
        lines.append("#PAID_END#")

    return "\n".join(lines)


def _find_current_dayun_idx(dayuns: List[Dict], base_year: int) -> Optional[int]:
    """找到当前大运的索引。"""
    for i, dy in enumerate(dayuns):
        start = dy['start_year']
        end = start + 9
        if start <= base_year <= end:
            return i
    return None


def _calculate_ranges(
    dayuns: List[Dict], current_idx: Optional[int]
) -> tuple:
    """计算免费区和付费区的范围。

    免费区：当前大运 + 之前2个
    付费区：当前大运之后的2个
    """
    n = len(dayuns)

    if current_idx is None:
        # 没有找到当前大运（可能 base_year 太早或太晚）
        # 默认显示前3个作为免费区
        free_start = 0
        free_end = min(3, n)
        paid_start = free_end
        paid_end = min(paid_start + 2, n)
    else:
        # 免费区：当前 + 之前2个
        free_start = max(0, current_idx - 2)
        free_end = current_idx + 1

        # 付费区：当前之后2个
        paid_start = free_end
        paid_end = min(paid_start + 2, n)

    return free_start, free_end, paid_start, paid_end


def _format_dayun_line(
    dayun: Dict[str, Any], facts: Dict[str, Any], is_current: bool
) -> str:
    """格式化单行大运。

    格式：大运N | {干支} | {起始年}-{结束年} | {好运/一般} | 职业五行：{五行}
    """
    idx = dayun['index']
    ganzhi = dayun['gan'] + dayun['zhi']
    year_range = f"{dayun['start_year']}-{dayun['start_year'] + 9}"
    luck = "好运" if dayun['zhi_good'] else "一般"

    # 职业五行
    swap = dayun.get('yongshen_swap_hint')
    if swap:
        wuxing = swap['target_industry']
        wuxing_str = f"职业五行：{wuxing}（用神互换，可能出现转行、工作变动）"
    else:
        elements = facts['natal']['yongshen_elements']
        wuxing = "、".join(elements)
        wuxing_str = f"职业五行：{wuxing}"

    line = f"大运{idx} | {ganzhi} | {year_range} | {luck} | {wuxing_str}"

    if is_current:
        line += " ← 当前"

    return line


# 付费内容裁剪由 router.py 统一处理
# 此模块只负责生成带标记的完整文本
