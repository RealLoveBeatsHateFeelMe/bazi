# -*- coding: utf-8 -*-
"""Findings Collector：收集 facts、hints 和 links（因果链接）。

最小改动实现：在 chat_api 层从 facts 中提取并生成 findings。
"""

from typing import Any, Dict, List, Optional, Set
import hashlib


class FindingsCollector:
    """Findings 收集器：用于收集 facts、hints 和 links。"""
    
    def __init__(self):
        self.facts: List[Dict[str, Any]] = []
        self.hints: List[Dict[str, Any]] = []
        self.links: List[Dict[str, Any]] = []
        
        # 用于去重和查找：fact_key -> fact_id
        self._fact_key_to_id: Dict[str, str] = {}
        # hint_key -> hint_id
        self._hint_key_to_id: Dict[str, str] = {}
    
    def add_fact(
        self,
        fact_type: str,
        scope: str,  # "natal" | "dayun_{year}" | "liunian_{year}"
        kind: str,  # "clash" | "pattern" | "harmony" | "punishment" | "marriage_wuhe" | etc.
        label: str,
        key_fields: Dict[str, Any],  # 用于生成稳定的 fact_id
    ) -> str:
        """添加一个 fact，返回 fact_id（如果已存在则返回已有的 fact_id）。
        
        参数:
            fact_type: fact 类型（如 "branch_clash", "pattern"）
            scope: 作用域（"natal" 或 "dayun_2020" 或 "liunian_2021"）
            kind: kind 类别（如 "clash", "pattern"）
            label: 简短标签（如 "辰戌冲", "枭神夺食"）
            key_fields: 关键字段字典，用于生成稳定的 fact_id
        
        返回:
            fact_id（字符串）
        """
        # 生成 fact_key：用于去重
        key_parts = [fact_type, scope, kind]
        # 将 key_fields 排序后加入
        key_items = sorted(key_fields.items())
        key_parts.extend([f"{k}:{v}" for k, v in key_items])
        fact_key = "|".join(key_parts)
        
        # 如果已存在，返回已有的 fact_id
        if fact_key in self._fact_key_to_id:
            return self._fact_key_to_id[fact_key]
        
        # 生成稳定的 fact_id：使用 type + scope + key_fields 的确定性拼接
        id_parts = [fact_type, scope, kind]
        id_parts.extend([str(v) for k, v in sorted(key_fields.items())])
        id_str = "|".join(id_parts)
        fact_id = hashlib.md5(id_str.encode('utf-8')).hexdigest()[:12]  # 12位十六进制
        
        # 创建 fact 对象
        fact = {
            "fact_id": fact_id,
            "type": fact_type,
            "kind": kind,
            "scope": scope,
            "label": label,
            **key_fields,  # 展开 key_fields 到 fact 对象中
        }
        
        self.facts.append(fact)
        self._fact_key_to_id[fact_key] = fact_id
        return fact_id
    
    def add_hint(
        self,
        domain: str,  # "relationship" | "career" | "health" | "wealth" | "general"
        level: str,  # "light" | "moderate" | "serious"
        label: str,
        key_fields: Optional[Dict[str, Any]] = None,
    ) -> str:
        """添加一个 hint，返回 hint_id。
        
        参数:
            domain: 领域（如 "relationship", "career"）
            level: 级别（"light", "moderate", "serious"）
            label: 提示文本（如 "感情波动", "婚姻宫被冲"）
            key_fields: 关键字段字典，用于生成稳定的 hint_id（可选）
        
        返回:
            hint_id（字符串）
        """
        key_fields = key_fields or {}
        
        # 生成 hint_key：用于去重
        key_parts = [domain, level, label]
        key_items = sorted(key_fields.items())
        key_parts.extend([f"{k}:{v}" for k, v in key_items])
        hint_key = "|".join(key_parts)
        
        # 如果已存在，返回已有的 hint_id
        if hint_key in self._hint_key_to_id:
            return self._hint_key_to_id[hint_key]
        
        # 生成稳定的 hint_id
        id_parts = [domain, level, label]
        id_parts.extend([str(v) for k, v in sorted(key_fields.items())])
        id_str = "|".join(id_parts)
        hint_id = hashlib.md5(id_str.encode('utf-8')).hexdigest()[:12]
        
        # 创建 hint 对象
        hint = {
            "hint_id": hint_id,
            "domain": domain,
            "level": level,
            "label": label,
        }
        if key_fields:
            hint.update(key_fields)
        
        self.hints.append(hint)
        self._hint_key_to_id[hint_key] = hint_id
        return hint_id
    
    def link(
        self,
        hint_id: str,
        fact_ids: List[str],
        rule_id: Optional[str] = None,
    ) -> None:
        """建立 hint 到 facts 的链接。
        
        参数:
            hint_id: hint 的 ID
            fact_ids: fact ID 列表
            rule_id: 规则 ID（可选，用于 trace）
        """
        link = {
            "hint_id": hint_id,
            "fact_ids": fact_ids,
        }
        if rule_id:
            link["rule_id"] = rule_id
        
        self.links.append(link)
    
    def get_findings(self) -> Dict[str, Any]:
        """获取所有 findings。
        
        返回:
            {
                "facts": [...],
                "hints": [...],
                "links": [...]
            }
        """
        return {
            "facts": self.facts,
            "hints": self.hints,
            "links": self.links,
        }

