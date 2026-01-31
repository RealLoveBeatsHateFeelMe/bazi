# -*- coding: utf-8 -*-
"""
Request Index v0 生成：从 facts 派生请求级索引。

注意：
- Index 是请求级派生快照：随 base_year（服务器本地年）变化，尤其 last5/last3
- Index 只做抽取/汇总，不做解释，不扫 events 大段文本
- 字段缺失必须保守默认（空列表/false/空字符串），字段名稳定不改
- facts 是唯一真相源，Index 从 facts 派生，不做额外推理
"""

from typing import Any, Dict, List, Optional
from datetime import datetime


def _get_facts_max_year(facts: Dict[str, Any]) -> int:
    """获取 facts 支持的最大年份。
    
    从 luck.groups 中找到最后一个流年的年份。
    
    参数:
        facts: 完整的 facts 数据
    
    返回:
        facts 支持的最大年份
    """
    luck = facts.get("luck", {})
    groups = luck.get("groups", [])
    
    max_year = 0
    for group in groups:
        liunian_list = group.get("liunian", [])
        for ln in liunian_list:
            year = ln.get("year")
            if year is not None and year > max_year:
                max_year = year
    
    return max_year if max_year > 0 else 2100  # 保守默认


def _get_scan_horizon_end_year(base_year: int, facts_max_year: int) -> int:
    """获取扫描终点年份（用于找好运年）。
    
    参数:
        base_year: 基准年份
        facts_max_year: facts 支持的最大年份
    
    返回:
        扫描终点年份：min(base_year + 10, facts_max_year)
    """
    return min(base_year + 10, facts_max_year)


def generate_request_index(
    facts: Dict[str, Any],
    base_year: int,
    quota: Optional[Dict[str, Any]] = None,
    accesses_future: bool = False,
) -> Dict[str, Any]:
    """生成 Request Index v0。
    
    参数:
        facts: 完整的 facts 数据（来自 analyze_complete）
        base_year: 服务器本地年份（用于计算 last5/last3）
        quota: 配额信息（可选），包含：
            - tier: "free" | "paid"（默认为 "free"）
            - backend_allowed: bool（默认为 True）
            - future_allowed: bool（默认为 False，免费用户不允许未来）
            - token_budget: Dict（可选，token 预算信息）
        accesses_future: 本次请求是否访问未来数据（用于设置 blocked_reason）
            - True: 未来请求（future3/find_good_year）
            - False: 过去请求（overall_recent/named_year/replay_last5）
    
    返回:
        Request Index v0 字典
    """
    # 解析 quota 参数（默认值）
    if quota is None:
        quota = {
            "tier": "free",
            "backend_allowed": True,
            "future_allowed": False,
            "token_budget": {"remaining": None, "limit": None, "reset_at": None},
        }
    
    tier = quota.get("tier", "free")
    backend_allowed = quota.get("backend_allowed", True)
    future_allowed = quota.get("future_allowed", False) if tier == "free" else quota.get("future_allowed", True)
    token_budget = quota.get("token_budget", {"remaining": None, "limit": None, "reset_at": None})
    
    # 计算 facts_max_year
    facts_max_year = _get_facts_max_year(facts)
    
    # 1) index.meta（时间范围）
    scan_horizon_end_year = _get_scan_horizon_end_year(base_year, facts_max_year)
    meta = {
        "index_version": "0.1.0",
        "base_year": base_year,
        "last5_years": [base_year, base_year - 1, base_year - 2, base_year - 3, base_year - 4],  # 必须含当年
        "last3_years": [base_year, base_year - 1, base_year - 2],
        "future3_years": [base_year, base_year + 1, base_year + 2],  # 从今年开始的未来三年
        "scan_horizon_end_year": scan_horizon_end_year,  # 用于找好运年；min(base_year + 10, facts_max_year)
        "facts_max_year": facts_max_year,  # 新增：facts 支持的最大年份
    }
    
    # 确定 account_flags 和 request_blocked
    # account_flags: free 用户包含 "future_locked"，paid 用户为空数组
    account_flags: List[str] = []
    if tier == "free":
        account_flags.append("future_locked")
    
    # request_blocked: 只有当请求试图访问被锁能力或 backend hard stop 时才为 true
    # 对于 free 用户，如果 future_allowed=False 且 accesses_future=True，则请求被阻止
    # token 超限时，backend_allowed=False，请求也被阻止
    request_blocked = (not backend_allowed) or (not future_allowed and accesses_future)
    
    # blocked_reason: 本次请求阻断原因
    # 过去请求（overall_recent/named_year/replay_last5）：blocked_reason=""
    # 未来请求（future3/find_good_year）且 free："future_locked"
    # token 超限："token_limit"
    if not backend_allowed:
        blocked_reason = "token_limit"
    elif not future_allowed and accesses_future:
        blocked_reason = "future_locked"
    else:
        blocked_reason = ""
    
    # 2) index.dayun（确保"当前大运"永远抓对；免费用户裁剪未来信息）
    dayun_index = _build_dayun_index(facts, base_year, future_allowed)
    
    # 3) index.turning_points（临近才提；免费用户裁剪未来信息）
    turning_points_index = _build_turning_points_index(facts, base_year, future_allowed)
    
    # 4) index.year_grade（同时产出 last5 + future3；future3 受门控）
    year_grade_index = _build_year_grade_index(facts, meta["last5_years"], meta["future3_years"], backend_allowed, future_allowed)
    
    # 5) index.good_year_search（新增：从今年起找好运年/第几年好运；受门控）
    good_year_search_index = _build_good_year_search_index(facts, base_year, meta["future3_years"], meta["scan_horizon_end_year"], backend_allowed, future_allowed)
    
    # 6) index.relationship（只提示窗口，不展开；免费用户裁剪未来信息）
    relationship_index = _build_relationship_index(facts, meta["last5_years"], future_allowed, base_year)
    
    # 7) index.quota（新增：配额信息）
    quota_index = {
        "tier": tier,
        "backend_allowed": backend_allowed,
        "future_allowed": future_allowed,
        "allowed_year_max": base_year,  # 免费允许的最大年份=base_year（含当年）
        "token_budget": token_budget,
        "blocked_reason": blocked_reason,  # 本次请求阻断原因
        "account_flags": account_flags,  # 账户级标志（free 用户包含 "future_locked"）
        "request_blocked": request_blocked,  # 本次请求是否被阻止
    }
    
    # 8) index.personality（新增：性格轴索引）
    personality_index = _build_personality_index(facts)
    
    return {
        "meta": meta,
        "dayun": dayun_index,
        "turning_points": turning_points_index,
        "year_grade": year_grade_index,
        "good_year_search": good_year_search_index,
        "relationship": relationship_index,
        "quota": quota_index,
        "personality": personality_index,  # 新增：性格轴索引
    }


def _build_dayun_index(facts: Dict[str, Any], base_year: int, future_allowed: bool) -> Dict[str, Any]:
    """构建 dayun 索引。

    必须字段：
    - current_dayun_ref: 当前大运摘要（至少包含起止年 + 好运/一般/坏运标签）
    - future_dayuns: 未来两步大运（v1.1新增，受 future_allowed 门控）
    - yongshen_swap: 用神互换信息
    """
    luck = facts.get("luck", {})
    groups = luck.get("groups", [])
    
    # 找到当前年份所在的大运
    current_dayun_obj = None
    current_dayun_index = None
    current_dayun_end_year = None
    
    for idx, group in enumerate(groups):
        dayun = group.get("dayun")
        if dayun is None:
            continue
        
        start_year = dayun.get("start_year")
        if start_year is None:
            continue
        
        # 计算结束年份（下一个大运起始年份 - 1，或当前大运起始年份 + 9）
        end_year = start_year + 9
        if idx + 1 < len(groups):
            next_group = groups[idx + 1]
            next_dayun = next_group.get("dayun")
            if next_dayun:
                next_start_year = next_dayun.get("start_year")
                if next_start_year:
                    end_year = next_start_year - 1
        
        if start_year <= base_year <= end_year:
            current_dayun_obj = dayun
            current_dayun_index = dayun.get("index")
            current_dayun_end_year = end_year
            break
    
    # 构建 current_dayun_ref（确保"当前大运"永远抓对；不存大段文案，不存整本大运）
    if current_dayun_obj:
        # 确定 fortune_label：从 dayun_label 映射到 "好运" / "一般" / "坏运"
        dayun_label = current_dayun_obj.get("dayun_label", "一般")
        is_good = current_dayun_obj.get("is_good", False)
        is_very_good = current_dayun_obj.get("is_very_good", False)
        
        # 映射 fortune_label
        if is_very_good or (is_good and "好运" in dayun_label):
            fortune_label = "好运"
        elif "坏运" in dayun_label or "变动过大" in dayun_label:
            fortune_label = "坏运"
        else:
            fortune_label = "一般"
        
        # 构建简洁的 label（只包含干支）
        gan = current_dayun_obj.get("gan", "")
        zhi = current_dayun_obj.get("zhi", "")
        label = f"{gan}{zhi}" if gan and zhi else ""
        
        current_dayun_ref = {
            "label": label,  # 例如 "壬午"
            "start_year": current_dayun_obj.get("start_year"),
            "end_year": current_dayun_end_year if current_dayun_end_year is not None else (current_dayun_obj.get("start_year", 0) + 9),
            "fortune_label": fortune_label,  # "好运" / "一般" / "坏运"
        }
    else:
        # 保守默认：空对象
        current_dayun_ref = {
            "label": "",
            "start_year": None,
            "end_year": None,
            "fortune_label": "一般",
        }
    
    # 获取 fortune_label（用于顶层字段）
    fortune_label = current_dayun_ref.get("fortune_label", "一般")
    
    # 构建 yongshen_swap（从 facts 的 indexes.dayun.yongshen_shift 派生）
    yongshen_shift = facts.get("indexes", {}).get("dayun", {}).get("yongshen_shift", {})
    has_swap = yongshen_shift.get("hit", False)
    windows = yongshen_shift.get("windows", [])
    
    # 转换为 items 格式（只包含可审计的最小信息）
    # 免费用户：必须过滤，只保留与 <= base_year 有重叠的条目
    items: List[Dict[str, Any]] = []
    hint = ""
    
    if has_swap and windows:
        for window in windows:
            year_range = window.get("year_range", {})
            start_year = year_range.get("start_year", 0)
            end_year = year_range.get("end_year", 0)
            
            # 免费用户：只保留与 <= base_year 有重叠的条目
            if not future_allowed:
                # 如果整个区间都在未来，跳过
                if start_year > base_year:
                    continue
                # 如果区间与过去/当年有重叠，保留（但 end_year 可能需要裁剪）
                # 注意：这里我们保留完整的 year_range，但 hint 会被置空
            
            items.append({
                "dayun_seq": window.get("dayun_seq"),
                "year_range": year_range,
                "from_elements": window.get("from_elements", []),
                "to_elements": window.get("to_elements", []),
            })
        
        # 生成 hint（只做汇总，不展开）
        # 免费用户：hint 必须置空（因为文案很容易泄露未来区间）
        if future_allowed and len(items) > 0:
            if len(items) == 1:
                year_range = items[0].get("year_range", {})
                start_year = year_range.get("start_year", 0)
                end_year = year_range.get("end_year", 0)
                hint = f"存在用神侧重变化窗口（{start_year}-{end_year}年，仅提示变动，不展开原因；需要可继续追问）"
            else:
                hint = f"存在用神侧重变化窗口（共{len(items)}个窗口，仅提示变动，不展开原因；需要可继续追问）"
    
    # has_swap 按过滤后的 items 结果决定
    has_swap = len(items) > 0

    # ===== 新增：future_dayuns（未来两步大运）=====
    # 定义：不包括当前大运，从当前之后的两步
    # 门控：受 future_allowed 控制（Free用户 = []）
    future_dayuns: List[Dict[str, Any]] = []
    if future_allowed and current_dayun_index is not None:
        # 找到当前大运在 groups 中的位置
        current_group_idx = None
        for idx, group in enumerate(groups):
            dayun = group.get("dayun")
            if dayun and dayun.get("index") == current_dayun_index:
                current_group_idx = idx
                break

        if current_group_idx is not None:
            # 获取未来两步大运（当前大运之后的两个）
            for offset in [1, 2]:
                next_idx = current_group_idx + offset
                if next_idx < len(groups):
                    next_group = groups[next_idx]
                    next_dayun = next_group.get("dayun")
                    if next_dayun:
                        next_start_year = next_dayun.get("start_year")
                        if next_start_year is None:
                            continue

                        # 计算结束年份
                        next_end_year = next_start_year + 9
                        if next_idx + 1 < len(groups):
                            following_group = groups[next_idx + 1]
                            following_dayun = following_group.get("dayun")
                            if following_dayun:
                                following_start = following_dayun.get("start_year")
                                if following_start:
                                    next_end_year = following_start - 1

                        # 确定 fortune_label
                        next_dayun_label = next_dayun.get("dayun_label", "一般")
                        next_is_good = next_dayun.get("is_good", False)
                        next_is_very_good = next_dayun.get("is_very_good", False)

                        if next_is_very_good or (next_is_good and "好运" in next_dayun_label):
                            next_fortune_label = "好运"
                        elif "坏运" in next_dayun_label or "变动过大" in next_dayun_label:
                            next_fortune_label = "坏运"
                        else:
                            next_fortune_label = "一般"

                        next_gan = next_dayun.get("gan", "")
                        next_zhi = next_dayun.get("zhi", "")
                        next_label = f"{next_gan}{next_zhi}" if next_gan and next_zhi else ""

                        future_dayuns.append({
                            "label": next_label,
                            "start_year": next_start_year,
                            "end_year": next_end_year,
                            "fortune_label": next_fortune_label,
                        })

    return {
        "current_dayun_ref": current_dayun_ref,  # 改为 current_dayun_ref（简洁结构）
        "future_dayuns": future_dayuns,  # v1.1新增：未来两步大运（Free用户 = []）
        "fortune_label": fortune_label,  # 新增：顶层字段（与 current_dayun_ref.fortune_label 等值）
        "yongshen_swap": {
            "has_swap": has_swap,
            "items": items,  # 无互换则 []（免费用户已过滤未来条目）
            "hint": hint,    # 无互换则 ""（免费用户必须置空）
        },
    }


def _build_turning_points_index(facts: Dict[str, Any], base_year: int, future_allowed: bool) -> Dict[str, Any]:
    """构建 turning_points 索引。

    必须字段：
    - all: list（可空，但字段必须存在；免费用户只保留 year <= base_year 的条目）
    - nearby: list（all 裁剪到窗口；v1.1更新：过去5年+未来10年）
    - past5_turning_points: list（v1.1新增：过去5年内的转折点，用于Q1）
    - should_mention: bool（nearby 非空即 true）

    v1.1更新：
    - nearby 窗口调整为：过去5年 + 未来10年（[base_year-5, base_year+10]）
    - 新增 past5_turning_points：过去5年内的转折点

    参数:
        future_allowed: 是否允许未来相关计算（免费用户为 False）
    """
    turning_points = facts.get("turning_points", [])

    # 免费用户：all 只保留 year <= base_year 的条目
    if not future_allowed:
        turning_points = [tp for tp in turning_points if tp.get("year", 0) <= base_year]

    # v1.1更新：nearby 窗口调整为过去5年+未来10年
    # 免费用户：[base_year-5, base_year]
    # 付费用户：[base_year-5, base_year+10]
    nearby_window_start = base_year - 5
    nearby_window_end = base_year + 10 if future_allowed else base_year

    nearby_list: List[Dict[str, Any]] = []
    for tp in turning_points:
        year = tp.get("year")
        if year is not None and nearby_window_start <= year <= nearby_window_end:
            nearby_list.append(tp)

    # 按年份排序（升序）
    nearby_list.sort(key=lambda x: x.get("year", 0))

    # v1.1新增：past5_turning_points（过去5年内的转折点）
    # 窗口：[base_year-5, base_year]（含两端）
    past5_window_start = base_year - 5
    past5_window_end = base_year

    past5_turning_points: List[Dict[str, Any]] = []
    for tp in turning_points:
        year = tp.get("year")
        if year is not None and past5_window_start <= year <= past5_window_end:
            past5_turning_points.append(tp)

    # 按年份排序（升序）
    past5_turning_points.sort(key=lambda x: x.get("year", 0))

    return {
        "all": turning_points,  # 可空，但字段必须存在（免费用户已过滤未来条目）
        "nearby": nearby_list,   # all 裁剪到窗口（v1.1: 过去5年+未来10年）
        "past5_turning_points": past5_turning_points,  # v1.1新增：过去5年内的转折点
        "should_mention": len(nearby_list) > 0,  # nearby 非空即 true
    }


def _build_year_grade_index(
    facts: Dict[str, Any], 
    last5_years: List[int],
    future3_years: List[int],
    backend_allowed: bool,
    future_allowed: bool,
) -> Dict[str, Any]:
    """构建 year_grade 索引。
    
    必须字段：
    - last5: 长度=5，顺序严格按 last5_years 排序（year 从大到小）
    - future3: 长度=3，顺序严格按 future3_years 排序（year 从小到大）；⚠️若未来被锁/超限则填空结构或空列表，但字段必须存在）
    
    参数:
        backend_allowed: 是否允许后端计算（token 超限时为 False）
        future_allowed: 是否允许未来相关计算（免费用户为 False）
    """
    luck = facts.get("luck", {})
    groups = luck.get("groups", [])
    
    # 收集所有流年数据到字典中（year -> liunian_dict）
    liunian_map: Dict[int, Dict[str, Any]] = {}
    if backend_allowed:
        for group in groups:
            liunian_list = group.get("liunian", [])
            for ln in liunian_list:
                year = ln.get("year")
                if year is not None:
                    liunian_map[year] = ln
    
    # 构建 last5 列表（按 last5_years 顺序，year 从大到小）
    last5_list: List[Dict[str, Any]] = []
    for year in last5_years:  # 已经是 [base_year, base_year-1, ...] 顺序（从大到小）
        if backend_allowed:
            year_obj = _build_year_grade_item(year, liunian_map)
        else:
            # 后端超限，输出保守空值
            year_obj = {
                "year": year,
                "Y": 0.0,
                "year_label": "一般",
            }
        last5_list.append(year_obj)
    
    # 构建 future3 列表（按 future3_years 顺序，year 从小到大；⚠️若未来被锁/超限则填空结构或空列表，但字段必须存在）
    future3_list: List[Dict[str, Any]] = []
    if future_allowed and backend_allowed:
        # 未来允许且后端允许，正常计算
        for year in future3_years:  # [base_year, base_year+1, base_year+2]
            year_obj = _build_year_grade_item(year, liunian_map)
            future3_list.append(year_obj)
    else:
        # 未来被锁或后端超限，输出 locked=true + null（字段必须存在）
        for year in future3_years:
            future3_list.append({
                "year": year,
                "locked": True,
                "Y": None,
                "year_label": None,
                "half1": None,
                "half2": None,
            })
    
    return {
        "last5": last5_list,    # 长度=5，顺序严格按 last5_years 排序（year 从大到小）
        "future3": future3_list, # 长度=3，顺序严格按 future3_years 排序（year 从小到大）
    }


def _build_year_grade_item(year: int, liunian_map: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    """构建单个 YearGrade 项。

    v1.1新增：is_bad_year 和 is_change_year 字段
    - is_bad_year: total_risk_percent >= 40（凶年）
    - is_change_year: 25 <= total_risk_percent < 40（变动年）
    """
    if year not in liunian_map:
        # 该年份不存在流年数据，使用保守默认
        return {
            "year": year,
            "Y": 0.0,
            "year_label": "一般",
            "is_bad_year": False,      # v1.1新增
            "is_change_year": False,   # v1.1新增
        }

    ln = liunian_map[year]
    Y = ln.get("total_risk_percent", 0.0)

    # v1.1新增：计算 is_bad_year 和 is_change_year
    is_bad_year = Y >= 40.0
    is_change_year = 25.0 <= Y < 40.0

    # 计算 year_label（按用户最新口径）
    if Y >= 40.0:
        year_label = "全年 凶（棘手/意外）"
    elif Y >= 25.0:
        year_label = "全年 明显变动（可克服）"
    else:
        # Y < 25.0，必须输出开始/后来
        risk_from_gan = ln.get("risk_from_gan", 0.0)
        risk_from_zhi = ln.get("risk_from_zhi", 0.0)
        # 兼容映射：支持新字段 start_good/later_good 和旧字段 first_half_good/second_half_good
        is_gan_yongshen = ln.get("start_good", ln.get("first_half_good", False))
        is_zhi_yongshen = ln.get("later_good", ln.get("second_half_good", False))

        start_label = _calc_half_year_label(risk_from_gan, is_gan_yongshen)
        later_label = _calc_half_year_label(risk_from_zhi, is_zhi_yongshen)

        year_label = f"开始 {start_label}，后来 {later_label}"

    # 构建 year 对象
    year_obj: Dict[str, Any] = {
        "year": year,
        "Y": Y,
        "year_label": year_label,
        "is_bad_year": is_bad_year,        # v1.1新增
        "is_change_year": is_change_year,  # v1.1新增
    }

    # 当 Y < 25.0 时，必须额外输出 start/later（从流年数据中获取）
    if Y < 25.0:
        risk_from_gan = ln.get("risk_from_gan", 0.0)
        risk_from_zhi = ln.get("risk_from_zhi", 0.0)
        # 兼容映射
        is_gan_yongshen = ln.get("start_good", ln.get("first_half_good", False))
        is_zhi_yongshen = ln.get("later_good", ln.get("second_half_good", False))

        year_obj["start"] = {
            "H": risk_from_gan,
            "label": _calc_half_year_label(risk_from_gan, is_gan_yongshen),
        }
        year_obj["later"] = {
            "H": risk_from_zhi,
            "label": _calc_half_year_label(risk_from_zhi, is_zhi_yongshen),
        }

    return year_obj


def _calc_half_year_label(H: float, is_yongshen: bool) -> str:
    """计算半年判词。
    
    规则（必须按用户最新口径）：
    - H <= 10.0：用神 → "好运"；非用神 → "一般"
    - 10.0 < H < 20.0："有轻微变动"
    - H >= 20.0："凶（棘手/意外）"
    """
    if H <= 10.0:
        return "好运" if is_yongshen else "一般"
    elif H < 20.0:
        return "有轻微变动"
    else:  # H >= 20.0
        return "凶（棘手/意外）"


def _build_good_year_search_index(
    facts: Dict[str, Any],
    base_year: int,
    future3_years: List[int],
    scan_horizon_end_year: int,
    backend_allowed: bool,
    future_allowed: bool,
) -> Dict[str, Any]:
    """构建 good_year_search 索引。
    
    必有字段（永远存在，找不到就空/Null）：
    - rule: "half1_or_half2_label_is_好运"
    - future3_good_years: [year...]
    - has_good_in_future3: bool
    - next_good_year: int | null（未来三年都没好运时，从 base_year 往后继续找最近好运年）
    - next_good_year_offset: int | null（next_good_year - base_year）
    - checked_years: [year...]（审计：到底扫了哪些年）
    
    好运年判定规则（写死）：
    只要该年 half1.half_label == "好运" 或 half2.half_label == "好运" 即认为该年是"好运年"
    
    ⚠️门控规则：
    若 future_allowed=false 或 backend_allowed=false：
    good_year_search 字段仍存在，但应输出"保守空结果"：
    - future3_good_years=[]
    - has_good_in_future3=false
    - next_good_year=null
    - next_good_year_offset=null
    - checked_years=[]
    不得扫描未来年份、不得进行任何未来计算
    """
    # ⚠️门控：若未来被锁或后端超限，输出保守空结果
    if not future_allowed or not backend_allowed:
        return {
            "rule": "half1_or_half2_label_is_好运",
            "future3_good_years": [],
            "has_good_in_future3": False,
            "next_good_year": None,
            "next_good_year_offset": None,
            "checked_years": [],
        }
    
    luck = facts.get("luck", {})
    groups = luck.get("groups", [])
    
    # 收集所有流年数据到字典中（year -> liunian_dict）
    liunian_map: Dict[int, Dict[str, Any]] = {}
    for group in groups:
        liunian_list = group.get("liunian", [])
        for ln in liunian_list:
            year = ln.get("year")
            if year is not None:
                liunian_map[year] = ln
    
    # 1. 检查 future3_years 中的好运年
    future3_good_years: List[int] = []
    checked_years: List[int] = list(future3_years)  # 先记录检查的年份
    
    for year in future3_years:
        if year not in liunian_map:
            continue
        
        ln = liunian_map[year]
        Y = ln.get("total_risk_percent", 0.0)

        # 只有当 Y < 25.0 时，才有 start/later
        if Y < 25.0:
            risk_from_gan = ln.get("risk_from_gan", 0.0)
            risk_from_zhi = ln.get("risk_from_zhi", 0.0)
            # 兼容映射
            is_gan_yongshen = ln.get("start_good", ln.get("first_half_good", False))
            is_zhi_yongshen = ln.get("later_good", ln.get("second_half_good", False))

            start_label = _calc_half_year_label(risk_from_gan, is_gan_yongshen)
            later_label = _calc_half_year_label(risk_from_zhi, is_zhi_yongshen)

            # 好运年判定：start 或 later 的 label == "好运"
            if start_label == "好运" or later_label == "好运":
                future3_good_years.append(year)

    has_good_in_future3 = len(future3_good_years) > 0

    # 2. 如果未来三年没有好运，从 base_year 往后继续找（最多到 base_year+10）
    next_good_year: Optional[int] = None
    next_good_year_offset: Optional[int] = None

    if not has_good_in_future3:
        # 从 future3_years 的最后一年 + 1 开始，直到 min(scan_horizon_end_year, base_year+10)
        start_search_year = max(future3_years) + 1 if future3_years else base_year + 3
        end_search_year = min(scan_horizon_end_year, base_year + 10)

        for year in range(start_search_year, end_search_year + 1):
            checked_years.append(year)  # 记录检查的年份

            if year not in liunian_map:
                continue

            ln = liunian_map[year]
            Y = ln.get("total_risk_percent", 0.0)

            # 只有当 Y < 25.0 时，才有 start/later
            if Y < 25.0:
                risk_from_gan = ln.get("risk_from_gan", 0.0)
                risk_from_zhi = ln.get("risk_from_zhi", 0.0)
                # 兼容映射
                is_gan_yongshen = ln.get("start_good", ln.get("first_half_good", False))
                is_zhi_yongshen = ln.get("later_good", ln.get("second_half_good", False))

                start_label = _calc_half_year_label(risk_from_gan, is_gan_yongshen)
                later_label = _calc_half_year_label(risk_from_zhi, is_zhi_yongshen)

                # 好运年判定：start 或 later 的 label == "好运"
                if start_label == "好运" or later_label == "好运":
                    next_good_year = year
                    next_good_year_offset = year - base_year
                    break

    return {
        "rule": "start_or_later_label_is_好运",
        "future3_good_years": future3_good_years,
        "has_good_in_future3": has_good_in_future3,
        "next_good_year": next_good_year,          # int | null
        "next_good_year_offset": next_good_year_offset,  # int | null
        "checked_years": checked_years,            # 审计：到底扫了哪些年
    }


def _build_relationship_index(facts: Dict[str, Any], last5_years: List[int], future_allowed: bool, base_year: int) -> Dict[str, Any]:
    """构建 relationship 索引。
    
    必须字段：
    - hit: bool
    - years_hit: list[int]（命中列表；免费用户必须过滤为 <= base_year 的年份）
    - last5_years_hit: list[int]（years_hit 与 last5_years 的交集，保持排序与 last5_years 一致）
    
    参数:
        future_allowed: 是否允许未来相关计算（免费用户为 False）
        base_year: 基准年份
    """
    relationship = facts.get("indexes", {}).get("relationship", {})
    years_hit = relationship.get("years", [])
    hit = relationship.get("hit", False)
    
    # 免费用户：years_hit 必须过滤为 <= base_year 的年份列表
    if not future_allowed:
        years_hit = [y for y in years_hit if y <= base_year]
        hit = len(years_hit) > 0
    
    # last5_years_hit：years_hit 与 last5_years 的交集，保持排序与 last5_years 一致
    last5_years_hit = [y for y in last5_years if y in years_hit]
    
    return {
        "hit": hit,
        "years_hit": years_hit,        # 命中列表（免费用户已过滤未来年份）
        "last5_years_hit": last5_years_hit,  # years_hit 与 last5_years 的交集，保持排序与 last5_years 一致
    }


def _build_personality_index(facts: Dict[str, Any]) -> Dict[str, Any]:
    """构建 personality 索引（性格轴摘要）。
    
    从 facts.natal.dominant_traits 派生，包含每个轴的关键字段：
    - group: 大类名称（印 / 财 / 官杀 / 食伤 / 比劫）
    - total_percent: 该大类的总占比
    - dominant_ten_god: 主导十神（split 时为 None）
    - xiongshen_status: 凶神状态（4态枚举：pure_xiongshen / xiongshen_majority / split / none）
    """
    natal = facts.get("natal", {})
    dominant_traits = natal.get("dominant_traits", [])
    
    # 转换为 axis_summaries 列表
    axis_summaries: List[Dict[str, Any]] = []
    for trait in dominant_traits:
        group = trait.get("group")
        total_percent = trait.get("total_percent", 0.0)
        
        # 如果该轴力量为 0，跳过（不存在的轴不展示）
        if total_percent == 0.0:
            continue
        
        axis_summary = {
            "group": group,
            "total_percent": total_percent,
            "dominant_ten_god": trait.get("dominant_ten_god"),
            "xiongshen_status": trait.get("xiongshen_status", "none"),
            "mix_label": trait.get("mix_label"),  # 保留兼容字段
            "sub_label": trait.get("sub_label"),  # 保留兼容字段
        }
        axis_summaries.append(axis_summary)
    
    return {
        "axis_summaries": axis_summaries,  # 性格轴摘要列表（按 total_percent 降序）
    }

