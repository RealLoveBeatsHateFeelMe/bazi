# -*- coding: utf-8 -*-
"""
Chat API：用户随便问一句 → 后端返回统一返回壳（answer/index/trace）。

关键边界：
- facts（用户建档生成的全量事实）仍是唯一真相源，不要把推理散落到打印层
- Index 是请求级派生快照：随 base_year（服务器本地年）变化，尤其 last5/last3
- Router 做决策只读 index，不要扫 facts 全书
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .request_index import generate_request_index
from .router import route
from .modules import get_module_inputs_trace


def chat_api(
    query: str,
    facts: Dict[str, Any],
    base_year: Optional[int] = None,
) -> Dict[str, Any]:
    """Chat API 主函数。
    
    参数:
        query: 用户查询
        facts: 完整的 facts 数据（来自 analyze_complete）
        base_year: 服务器本地年份（默认使用当前年份）
    
    返回:
        统一返回壳：
        {
            "answer": "string",
            "index": { /* Request Index v0 */ },
            "trace": { /* 全审计 */ },
            "error": null
        }
    """
    # 确定 base_year（默认使用当前年份）
    if base_year is None:
        base_year = datetime.now().year
    
    # 1. 生成 Request Index v0
    index = generate_request_index(facts, base_year)
    
    # 2. Router 决策（只读 index）
    intent, modules, years_used, reasons = route(query, index)
    
    # 3. 获取 modules 输入数据来源追踪（用于 trace）
    module_inputs_trace = get_module_inputs_trace(modules, index)
    
    # 4. 构建 trace（必须"全部都显示"）
    trace = {
        "router": {
            "intent": intent,
            "base_year": base_year,
            "years_used": years_used,
            "reasons": reasons,
        },
        "modules": [{"name": m} for m in modules],
        "module_inputs": module_inputs_trace,
        "backend_called": True,  # MVP 先固定 true
        "token_usage": {  # MVP 可以 null 占位，但字段必须存在
            "prompt": None,
            "completion": None,
            "total": None,
        },
    }
    
    # 5. 生成 answer（MVP 简化版：只做模板填充，不做真实 LLM 调用）
    answer = _generate_answer(query, intent, index, modules, years_used)
    
    # 6. 组装统一返回壳
    return {
        "answer": answer,
        "index": index,
        "trace": trace,
        "error": None,  # MVP 先固定为 null
    }


def _generate_answer(
    query: str,
    intent: str,
    index: Dict[str, Any],
    modules: List[str],
    years_used: List[int],
) -> str:
    """生成 answer（MVP 简化版：只做模板填充，不做真实 LLM 调用）。
    
    注意：这是 MVP 简化实现，真实场景应该调用 LLM。
    """
    parts: List[str] = []
    
    # 3.2 叙述口径（必须贯彻）："大运是气候、流年是天气"
    
    # 1. 大运气候（DAYUN_OVERVIEW）
    if "DAYUN_OVERVIEW" in modules:
        dayun = index.get("dayun", {})
        current_dayun_ref = dayun.get("current_dayun_ref", {})
        
        if current_dayun_ref.get("start_year") is not None:
            label = current_dayun_ref.get("label", "")
            start_year = current_dayun_ref.get("start_year")
            end_year = current_dayun_ref.get("end_year")
            fortune_label = current_dayun_ref.get("fortune_label", "一般")
            
            parts.append(f"【大运气候】当前大运：{label}（{start_year}-{end_year}年），整体：{fortune_label}。")
            
            # 用神互换提示
            yongshen_swap = dayun.get("yongshen_swap", {})
            if yongshen_swap.get("has_swap", False):
                hint = yongshen_swap.get("hint", "")
                if hint:
                    parts.append(hint)
            
            # 临近转折点
            turning_points = index.get("turning_points", {})
            if turning_points.get("should_mention", False):
                nearby = turning_points.get("nearby", [])
                if nearby:
                    parts.append(f"【临近转折】未来几年内有大运转折点。")
    
    # 2. 流年天气（LAST5_YEAR_GRADE）
    if "LAST5_YEAR_GRADE" in modules:
        year_grade = index.get("year_grade", {})
        last5 = year_grade.get("last5", [])
        
        if last5:
            parts.append(f"\n【近{len(years_used)}年天气回放】")
            for year_data in last5:
                if year_data.get("year") in years_used:  # 只显示 years_used 中的年份
                    year = year_data.get("year", 0)
                    Y = year_data.get("Y", 0.0)
                    year_label = year_data.get("year_label", "")
                    parts.append(f"{year}年：{year_label}（Y={Y:.1f}%）")
                    
                    # 如果 Y < 25，显示上下半年详情
                    if Y < 25.0:
                        half1 = year_data.get("half1", {})
                        half2 = year_data.get("half2", {})
                        if half1 and half2:
                            parts.append(f"  上半年：{half1.get('half_label', '')}（H={half1.get('H', 0.0):.1f}%），下半年：{half2.get('half_label', '')}（H={half2.get('H', 0.0):.1f}%）")
    
    # 3. 未来三年天气（FUTURE3_YEAR_GRADE）
    if "FUTURE3_YEAR_GRADE" in modules:
        year_grade = index.get("year_grade", {})
        future3 = year_grade.get("future3", [])
        
        if future3:
            parts.append(f"\n【未来三年天气】")
            for year_data in future3:
                year = year_data.get("year", 0)
                Y = year_data.get("Y", 0.0)
                year_label = year_data.get("year_label", "")
                parts.append(f"{year}年：{year_label}（Y={Y:.1f}%）")
                
                # 如果 Y < 25，显示上下半年详情
                if Y < 25.0:
                    half1 = year_data.get("half1", {})
                    half2 = year_data.get("half2", {})
                    if half1 and half2:
                        parts.append(f"  上半年：{half1.get('half_label', '')}（H={half1.get('H', 0.0):.1f}%），下半年：{half2.get('half_label', '')}（H={half2.get('H', 0.0):.1f}%）")
    
    # 4. 好运年份搜索（GOOD_YEAR_SEARCH）
    if "GOOD_YEAR_SEARCH" in modules:
        good_year_search = index.get("good_year_search", {})
        has_good_in_future3 = good_year_search.get("has_good_in_future3", False)
        future3_good_years = good_year_search.get("future3_good_years", [])
        next_good_year = good_year_search.get("next_good_year")
        next_good_year_offset = good_year_search.get("next_good_year_offset")
        
        if has_good_in_future3 and future3_good_years:
            parts.append(f"\n【好运年份】未来三年内有好运年份：{future3_good_years}")
        elif next_good_year is not None:
            parts.append(f"\n【好运年份】未来三年内无好运年份。从今年起第 {next_good_year_offset} 年（{next_good_year}年）是好运年份。")
        else:
            parts.append(f"\n【好运年份】在可计算范围内（到 {index.get('meta', {}).get('scan_horizon_end_year', 2100)}年）未找到好运年份。")
    
    # 3. 感情变动窗口（RELATIONSHIP_WINDOW）
    if "RELATIONSHIP_WINDOW" in modules:
        relationship = index.get("relationship", {})
        if relationship.get("hit", False):
            last5_years_hit = relationship.get("last5_years_hit", [])
            if last5_years_hit:
                parts.append(f"\n【感情变动窗口】近5年命中年份：{last5_years_hit}（有变动窗口，不展开原因；需要可继续追问）")
            else:
                years_hit = relationship.get("years_hit", [])
                parts.append(f"\n【感情变动窗口】全期命中年份：{years_hit}（有变动窗口，不展开原因；需要可继续追问）")
    
    # 如果没有内容，返回默认提示
    if not parts:
        return "暂无相关信息。"
    
    return "\n".join(parts)

