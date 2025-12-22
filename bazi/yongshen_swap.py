# -*- coding: utf-8 -*-
"""用神互换提示：在特定条件下提示可从事的行业（只打印，不影响计算）。"""

from typing import List, Optional, Dict, Any


def should_print_yongshen_swap_hint(
    day_gan: str,
    strength_percent: float,
    support_percent: float,
    yongshen_elements: List[str],
    dayun_zhi: str,
) -> Optional[Dict[str, Any]]:
    """判断是否应该打印用神互换提示。
    
    参数:
        day_gan: 日主天干
        strength_percent: 综合强弱百分比（用于判断身强/身弱）
        support_percent: 生扶力量占比
        yongshen_elements: 原局用神五行列表
        dayun_zhi: 大运地支
        
    返回:
        如果应该打印，返回包含提示信息的字典；否则返回None
    """
    # 只对丙、丁、壬、癸日主生效
    if day_gan not in ("丙", "丁", "壬", "癸"):
        return None
    
    # 判断身强/身弱
    is_strong = strength_percent >= 50.0
    is_weak = strength_percent < 50.0
    
    # 判断大运地支类型
    fire_yun = dayun_zhi in ("巳", "午")  # 火运
    water_yun = dayun_zhi in ("子", "亥")  # 水运
    
    if not (fire_yun or water_yun):
        return None
    
    # 检查用神是否包含指定五行
    yong_set = set(yongshen_elements)
    has_mu_huo = "木" in yong_set and "火" in yong_set
    has_jin_shui = "金" in yong_set and "水" in yong_set
    
    # 判断目标行业
    target_industry = None
    
    if day_gan in ("丙", "丁"):  # 火日主
        if is_weak and support_percent >= 30.0 and has_mu_huo and fire_yun:
            # 身弱 + 生扶≥30% + 用神包含木火 + 火运 → 可从事金、水行业
            target_industry = "金、水"
        elif is_strong and support_percent <= 75.0 and has_jin_shui and water_yun:
            # 身强 + 生扶≤75% + 用神包含金水 + 水运 → 可从事木、火行业
            target_industry = "木、火"
    elif day_gan in ("壬", "癸"):  # 水日主
        if is_weak and support_percent >= 30.0 and has_jin_shui and water_yun:
            # 身弱 + 生扶≥30% + 用神包含金水 + 水运 → 可从事木、火行业
            target_industry = "木、火"
        elif is_strong and support_percent <= 75.0 and has_mu_huo and fire_yun:
            # 身强 + 生扶≤75% + 用神包含木火 + 火运 → 可从事金、水行业
            target_industry = "金、水"
    
    if not target_industry:
        return None
    
    # 确定身强/身弱标签
    shen_status = "身强" if is_strong else "身弱"
    
    # 确定运支类型
    yun_type = "火" if fire_yun else "水"
    
    return {
        "yongshen_list": "、".join(sorted(yongshen_elements)),
        "shen_status": shen_status,
        "support_percent": support_percent,
        "dayun_zhi": dayun_zhi,
        "yun_type": yun_type,
        "target_industry": target_industry,
    }


def format_yongshen_swap_hint(hint_info: Dict[str, Any]) -> str:
    """格式化用神互换提示字符串。
    
    格式：
    【用神互换提示】原局用神：{原局全部用神五行}；{身弱/身强}；生扶力量={xx%}；运支={地支}(火/水) → 可从事：{目标五行}行业。注意转行，工作变动。
    """
    return (
        f"【用神互换提示】原局用神：{hint_info['yongshen_list']}；"
        f"{hint_info['shen_status']}；"
        f"生扶力量={hint_info['support_percent']:.0f}%；"
        f"运支={hint_info['dayun_zhi']}({hint_info['yun_type']}) → "
        f"可从事：{hint_info['target_industry']}行业。注意转行，工作变动。"
    )

