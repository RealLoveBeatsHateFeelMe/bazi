# -*- coding: utf-8 -*-
"""天干五合：识别与打印（不影响风险计算）。"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .config import GAN_WUHE
from .shishen import get_shishen


@dataclass
class GanPosition:
    """天干位置对象"""
    source: str  # "natal" | "dayun" | "liunian"
    label: str   # "年干"/"月干"/"日干"/"时干"/"大运天干"/"流年天干"
    gan: str     # 天干字
    shishen: str  # 十神


def detect_gan_wuhe(positions: List[GanPosition]) -> List[Dict[str, Any]]:
    """检测天干五合事件（包括争合）。
    
    参数:
        positions: 天干位置列表
        
    返回:
        五合事件列表，每个事件包含：
        - gan_pair: frozenset({gan1, gan2})
        - wuhe_name: 五合名称（如"乙庚合金"）
        - pos_a: A侧位置列表
        - pos_b: B侧位置列表
        - is_zhenghe: 是否争合
        - shishen_a: A侧十神（如果多的一侧）
        - shishen_b: B侧十神（如果少的一侧）
    """
    events = []
    
    # 按天干分组
    gan_to_positions: Dict[str, List[GanPosition]] = {}
    for pos in positions:
        if pos.gan not in gan_to_positions:
            gan_to_positions[pos.gan] = []
        gan_to_positions[pos.gan].append(pos)
    
    # 检查所有可能的五合对
    checked_pairs = set()
    for gan_a in gan_to_positions:
        for gan_b in gan_to_positions:
            if gan_a == gan_b:
                continue
            
            # 用frozenset作为key，避免重复检查
            pair_key = frozenset({gan_a, gan_b})
            if pair_key in checked_pairs:
                continue
            
            # 检查是否是五合
            if pair_key in GAN_WUHE:
                checked_pairs.add(pair_key)
                wuhe_name = GAN_WUHE[pair_key]
                
                pos_a = gan_to_positions[gan_a]
                pos_b = gan_to_positions[gan_b]
                
                # 判断是否争合
                is_zhenghe = len(pos_a) > 1 or len(pos_b) > 1
                
                # 确定多的一侧和少的一侧
                if len(pos_a) > len(pos_b):
                    many_side = pos_a
                    few_side = pos_b
                    many_gan = gan_a
                    few_gan = gan_b
                elif len(pos_b) > len(pos_a):
                    many_side = pos_b
                    few_side = pos_a
                    many_gan = gan_b
                    few_gan = gan_a
                else:
                    # 相等，都>1时是互争合，否则是普通1对1
                    many_side = pos_a
                    few_side = pos_b
                    many_gan = gan_a
                    few_gan = gan_b
                
                # 获取十神（取第一个位置的十神作为代表）
                shishen_a = many_side[0].shishen if many_side else ""
                shishen_b = few_side[0].shishen if few_side else ""
                
                events.append({
                    "gan_pair": pair_key,
                    "wuhe_name": wuhe_name,
                    "pos_a": pos_a,
                    "pos_b": pos_b,
                    "many_side": many_side,
                    "few_side": few_side,
                    "many_gan": many_gan,
                    "few_gan": few_gan,
                    "is_zhenghe": is_zhenghe,
                    "shishen_a": shishen_a,
                    "shishen_b": shishen_b,
                })
    
    return events


def format_gan_wuhe_event(
    event: Dict[str, Any],
    incoming_shishen: Optional[str] = None,
    prefix: str = ""
) -> str:
    """格式化五合事件为打印字符串。
    
    格式：
    （前缀）多的一侧柱位列表 + 字 "争合" 少的一侧柱位列表 + 字 五合名称 十神描述 （合进十神）合进
    
    参数:
        event: 五合事件字典
        incoming_shishen: 合进十神（大运/流年入口时提供）
        prefix: 前缀（如"大运6"、"2050年"）
    """
    many_side = event["many_side"]
    few_side = event["few_side"]
    many_gan = event["many_gan"]
    few_gan = event["few_gan"]
    wuhe_name = event["wuhe_name"]
    is_zhenghe = event["is_zhenghe"]
    shishen_a = event["shishen_a"]
    shishen_b = event["shishen_b"]
    
    # 构建柱位列表字符串（用逗号分隔）
    many_labels = "，".join([pos.label for pos in many_side])
    few_labels = "，".join([pos.label for pos in few_side])
    
    parts = []
    if prefix:
        parts.append(prefix)
    
    if is_zhenghe:
        # 争合格式：多的一侧柱位列表 + 字 "争合" 少的一侧柱位列表 + 字 五合名称 十神描述
        parts.append(f"{many_labels} {many_gan}")
        parts.append("争合")
        parts.append(f"{few_labels} {few_gan}")
        parts.append(wuhe_name)
        parts.append(f"{shishen_a}争合{shishen_b}")
    else:
        # 普通1对1格式：柱位列表 + 字 "与" 柱位列表 + 字 五合名称 十神描述
        parts.append(f"{many_labels} {many_gan}")
        parts.append("与")
        parts.append(f"{few_labels} {few_gan}")
        parts.append(wuhe_name)
        parts.append(f"{shishen_a}合{shishen_b}")
    
    # 合进标注（只在大运/流年入口时添加）
    if incoming_shishen:
        parts.append(f"{incoming_shishen}合进")
    
    return " ".join(parts)

