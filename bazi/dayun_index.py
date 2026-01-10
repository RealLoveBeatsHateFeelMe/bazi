# -*- coding: utf-8 -*-
"""
Dayun Index (Index-3) 生成：用神互换变动窗口信号。

注意：
- Index 只是 Router 的目录页（辅助决策），不是内容来源
- facts 是唯一真相源，Index 仅用于快速查询和筛选
- 严禁在 Index 中写"应该从事什么工作/行业"等建议性内容
- Index 只记录"变动事实"：发生在哪步大运、年份范围、从哪些用神五行侧重 → 到哪些五行侧重
"""

from typing import Any, Dict, List, Optional


def generate_dayun_index(
    luck_data: Dict[str, Any],
    natal_yongshen_elements: List[str],
) -> Dict[str, Any]:
    """生成 Dayun Index (Index-3)：用神互换变动窗口信号。
    
    注意：
    - Index 只是 Router 的目录页（辅助决策），不是内容来源
    - facts 是唯一真相源，Index 仅用于快速查询和筛选
    - 严禁在 Index 中写"应该从事什么工作/行业"等建议性内容
    - Index 只记录"变动事实"：发生在哪步大运、年份范围、从哪些用神五行侧重 → 到哪些五行侧重
    
    参数:
        luck_data: 大运/流年数据（包含 groups）
        natal_yongshen_elements: 原局用神五行列表
    
    返回:
        Dayun Index 字典，包含 yongshen_shift 信号
        {
            "yongshen_shift": {
                "hit": bool,                    # 是否存在用神互换窗口
                "windows": List[Dict],          # 用神互换窗口列表（排序稳定，按大运顺序）
            }
        }
    """
    groups = luck_data.get("groups", [])
    windows: List[Dict[str, Any]] = []
    
    # 遍历所有大运组（跳过 dayun 为 None 的组）
    for idx, group in enumerate(groups):
        dayun = group.get("dayun")
        if dayun is None:
            continue
        
        # 检查该大运是否触发用神互换
        yongshen_swap_hint = dayun.get("yongshen_swap_hint")
        if not yongshen_swap_hint:
            continue
        
        # 获取大运信息
        start_year = dayun.get("start_year")
        dayun_index = dayun.get("index")
        # dayun.index 字段已经正确设置（从0开始），直接使用
        dayun_seq = dayun_index if dayun_index is not None else idx
        
        # 计算窗口结束年份（下一个大运起始年份 - 1，或当前大运起始年份 + 9）
        end_year = start_year + 9  # 默认每个大运10年
        if idx + 1 < len(groups):
            next_group = groups[idx + 1]
            next_dayun = next_group.get("dayun")
            if next_dayun:
                next_start_year = next_dayun.get("start_year")
                if next_start_year:
                    end_year = next_start_year - 1
        
        # 提取用神互换信息（只记录可审计的最小信息）
        from_elements = sorted(natal_yongshen_elements)  # 互换前用神五行（原局用神）
        target_industry = yongshen_swap_hint.get("target_industry", "")
        # 将"金、水"或"木、火"转换为列表（只记录五行，不含建议）
        if "、" in target_industry:
            to_elements = sorted(target_industry.split("、"))
        else:
            to_elements = sorted([target_industry]) if target_industry else []
        
        # 创建窗口对象（只包含可审计的最小信息）
        window = {
            "dayun_seq": dayun_seq,
            "year_range": {
                "start_year": start_year,
                "end_year": end_year,
            },
            "from_elements": from_elements,  # 互换前用神五行集合（排序稳定）
            "to_elements": to_elements,      # 互换后用神五行集合（排序稳定，只记录五行，不含建议）
        }
        
        windows.append(window)
    
    # 合并连续触发的大运（年份连续且 from_elements/to_elements 相同）
    merged_windows: List[Dict[str, Any]] = []
    if windows:
        # 按 dayun_seq 排序（确保排序稳定）
        sorted_windows = sorted(windows, key=lambda w: w["dayun_seq"])
        
        current_window = None
        for window in sorted_windows:
            if current_window is None:
                current_window = window.copy()  # 复制窗口对象，避免直接引用
            else:
                # 检查是否可以合并（年份连续且 from_elements/to_elements 相同）
                current_end = current_window["year_range"]["end_year"]
                next_start = window["year_range"]["start_year"]
                current_from = tuple(current_window["from_elements"])
                current_to = tuple(current_window["to_elements"])
                next_from = tuple(window["from_elements"])
                next_to = tuple(window["to_elements"])
                
                if (next_start == current_end + 1 and 
                    current_from == next_from and 
                    current_to == next_to):
                    # 可以合并，更新结束年份
                    current_window["year_range"]["end_year"] = window["year_range"]["end_year"]
                else:
                    # 不能合并，保存当前窗口，开始新窗口
                    merged_windows.append(current_window)
                    current_window = window.copy()  # 复制窗口对象，避免直接引用
        
        # 添加最后一个窗口
        if current_window:
            merged_windows.append(current_window)
    
    return {
        "yongshen_shift": {
            "hit": len(merged_windows) > 0,
            "windows": merged_windows,  # 排序稳定，按 dayun_seq 排序
        }
    }

