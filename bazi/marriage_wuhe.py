# -*- coding: utf-8 -*-
"""天干五合争合/双合婚恋提醒检测。"""

from typing import Dict, List, Optional, Tuple, Any, Set
from .config import GAN_WUXING, GAN_WUHE
from .shishen import get_shishen


def get_spouse_star_and_competitor(
    day_gan: str, is_male: bool
) -> Optional[Tuple[str, str, str]]:
    """根据日主和性别，获取配偶星X、争合字Y和五合名称。
    
    参数:
        day_gan: 日主天干
        is_male: 是否为男性
    
    返回:
        (X, Y, wuhe_name) 或 None
        X: 配偶星天干
        Y: 争合字天干（同五行一端）
        wuhe_name: 五合名称（如"乙庚合"）
    """
    day_wuxing = GAN_WUXING.get(day_gan)
    if not day_wuxing:
        return None
    
    # 定义映射表（五合名称使用简化版，如"乙庚合"而非"乙庚合金"）
    if not is_male:
        # 女命：X = 官杀（克日主），Y = 同五行一端
        mapping = {
            "木": ("庚", "乙", "乙庚合"),  # 日主木（甲/乙）：X=庚，Y=乙（乙庚合）
            "火": ("壬", "丁", "丁壬合"),  # 日主火（丙/丁）：X=壬，Y=丁（丁壬合）
            "土": ("甲", "己", "甲己合"),  # 日主土（戊/己）：X=甲，Y=己（甲己合）
            "金": ("丙", "辛", "丙辛合"),  # 日主金（庚/辛）：X=丙，Y=辛（丙辛合）
            "水": ("戊", "癸", "戊癸合"),  # 日主水（壬/癸）：X=戊，Y=癸（戊癸合）
        }
    else:
        # 男命：X = 财（被日主克），Y = 同五行一端
        mapping = {
            "木": ("己", "甲", "甲己合"),  # 日主木（甲/乙）：X=己，Y=甲（甲己合）
            "火": ("辛", "丙", "丙辛合"),  # 日主火（丙/丁）：X=辛，Y=丙（丙辛合）
            "土": ("癸", "戊", "戊癸合"),  # 日主土（戊/己）：X=癸，Y=戊（戊癸合）
            "金": ("乙", "庚", "乙庚合"),  # 日主金（庚/辛）：X=乙，Y=庚（乙庚合）
            "水": ("丁", "壬", "丁壬合"),  # 日主水（壬/癸）：X=丁，Y=壬（丁壬合）
        }
    
    result = mapping.get(day_wuxing)
    if not result:
        return None
    
    X, Y, wuhe_name = result
    return (X, Y, wuhe_name)


def detect_marriage_wuhe_hints(
    gan_list: List[str],
    day_gan: str,
    is_male: bool,
    trigger_gans: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """检测天干五合争合/双合婚恋提醒。
    
    参数:
        gan_list: 该层所有天干列表（可能包含重复，需要包含日干）
        day_gan: 日主天干
        is_male: 是否为男性
        trigger_gans: 引动天干列表（大运/流年天干）。如果提供，则必须至少有一个引动天干是X或Y才触发。
                      如果为None，则只检查原局层（不需要引动）。
    
    返回:
        提醒事件列表，每个事件包含：
        - type: "他人争合" 或 "命主双合"
        - wuhe_name: 五合名称（如"乙庚合"）
        - hint_text: 提醒文案
    """
    hints = []
    
    # 获取配偶星X和争合字Y
    mapping = get_spouse_star_and_competitor(day_gan, is_male)
    if not mapping:
        return hints
    
    X, Y, wuhe_name = mapping
    
    # 如果提供了引动天干，检查是否有引动
    if trigger_gans is not None:
        # 必须至少有一个引动天干是X或Y
        has_trigger = any(gan in (X, Y) for gan in trigger_gans)
        if not has_trigger:
            return hints  # 没有引动，不触发
    
    # 统计天干出现次数（包括日干）
    gan_count: Dict[str, int] = {}
    for gan in gan_list:
        gan_count[gan] = gan_count.get(gan, 0) + 1
    
    # 检查X和Y是否都在集合中
    has_X = X in gan_count
    has_Y = Y in gan_count
    
    if not (has_X and has_Y):
        return hints
    
    X_count = gan_count[X]
    Y_count = gan_count[Y]
    
    # A) 他人争合：X和Y都出现，且参与这次五合的X与Y都不是"日干那一颗"
    # 如果Y恰好等于日干字，则必须有"另一颗Y"参与（即Y的实例不是日干那柱的Y）
    Y_is_day_gan = (Y == day_gan)
    
    if Y_is_day_gan:
        # Y是日干，需要至少2个Y（一个日干+至少一个非日干的Y）
        # 且X必须出现（X不可能是日干，因为X是配偶星）
        if Y_count >= 2 and X_count >= 1:
            hint_text = (
                f"天干{'官杀星' if not is_male else '财星'}被争合，{wuhe_name}合走{'官杀星' if not is_male else '财星'}，注意，防止感情竞争/第三者介入"
            )
            hints.append({
                "type": "他人争合",
                "wuhe_name": wuhe_name,
                "hint_text": hint_text,
            })
    else:
        # Y不是日干，只要X和Y都出现就满足（因为日干不可能是X，X是配偶星）
        # 但需要确保参与五合的X和Y都不是日干
        # 由于Y != day_gan，且X是配偶星（不可能是日干），所以只要X和Y都出现就满足
        if X_count >= 1 and Y_count >= 1:
            hint_text = (
                f"天干{'官杀星' if not is_male else '财星'}被争合，{wuhe_name}合走{'官杀星' if not is_male else '财星'}，注意，防止感情竞争/第三者介入"
            )
            hints.append({
                "type": "他人争合",
                "wuhe_name": wuhe_name,
                "hint_text": hint_text,
            })
    
    # B) 命主双合：日干=Y，且出现两个X
    if Y == day_gan and X_count >= 2:
        hint_text = (
            f"命主合两个{'官杀星' if not is_male else '财星'}，{wuhe_name}，注意，防止陷入三角恋"
        )
        hints.append({
            "type": "命主双合",
            "wuhe_name": wuhe_name,
            "hint_text": hint_text,
        })
    
    # B2) 命主三角恋（分支B2）：日干=Y，出现X，同时还存在另一个配偶星Z
    # 条件：日干=Y，且X出现，且存在另一个同类配偶星Z（不是X）
    if Y == day_gan and has_X:
        # 找到所有同类配偶星（排除X）
        other_spouse_stars: Set[str] = set()
        for gan in gan_list:
            if gan == day_gan or gan == X:
                continue  # 跳过日干和X
            shishen = get_shishen(day_gan, gan)
            if not shishen:
                continue
            
            # 女命：找官杀（正官/七杀）
            if not is_male:
                if shishen in ("正官", "七杀"):
                    other_spouse_stars.add(gan)
            else:
                # 男命：找财星（正财/偏财）
                if shishen in ("正财", "偏财"):
                    other_spouse_stars.add(gan)
        
        # 如果存在另一个配偶星Z（不是X），则触发
        if other_spouse_stars:
            hint_text = (
                f"命主合两个{'官杀星' if not is_male else '财星'}，{wuhe_name}，注意，防止陷入三角恋"
            )
            hints.append({
                "type": "命主三角恋B2",
                "wuhe_name": wuhe_name,
                "hint_text": hint_text,
            })
    
    return hints

