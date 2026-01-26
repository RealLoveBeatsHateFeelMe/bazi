# Final Product - 12 Questions Call Chain Map

---

## 产品定义

我们的产品是一个 **chatbot**。用户像操作 GPT 一样开启聊天框，只不过开启聊天框后需要输入生日。然后用户可以自由问模型问题，模型根据用户的问题**裁剪出 Facts/Index 里的文案**，输入给 LLM，然后 LLM 再输出给用户。

### 产品哲学

> **给出每个人的天气预报，帮助每个人更了解自己的天赋和特长**

| 维度 | 口径 |
|------|------|
| **主要性格** | 作为地基。不是你一定是什么样的人，而是你**更可能有什么样的天赋、性格** |
| **年度/大运评级** | 这一年整体偏顺、偏平、偏变动、偏棘手（用**强度表达**，而不是恐吓式"必凶必祸"） |
| **可能的走势** | 用"更可能/较容易/需要留意"的口径，给出这一年更常见的主题走向，**尽量像"天气预报"一样提供参考，而不是下判决** |

### 我们刻意不做的

- ❌ **不断言具体事件**（不说"某月必发生某事"）
- ❌ **不提供玄学解决方案**（不教仪式、不卖护身符、不输出"神奇方法"）
- ❌ **不替你做决定**（只给趋势与理解框架，选择权永远在你手里）

---

## 核心原则

| 原则 | 说明 |
|------|------|
| **年度评级是根基** | 凶/有变动但能克服/好运/一般。hints 只是解释可能性 |
| **财富/名气 = 年度评级 + 大运评级** | 不看十神，只看评级 |
| **行业 = 用神五行** | 大运 turning_points 可能导致用神互换，则换行业 |
| **不引入 Payload** | 所有问题通过 Index + 新函数解决，Facts 裁剪喂给 LLM |

---

## 技术方案：Index + 新函数（无 Payload）

### 为什么不需要 Payload

| 场景 | 之前担心 | 实际解决方案 |
|------|----------|--------------|
| 感情问题逐年查 | LLM 一年一年查困难 | ✅ `index.relationship.{years_hit, last5_years_hit}` 已汇总命中年份 |
| 行业问题 | 需要结构化映射 | ✅ 新函数输出可读文本：用神行业 + turning_points 时期的变化行业 |
| 职业适配 | 需要结构化映射 | ✅ 同上，新函数直接输出文本 |

### 多语言支持（英文）

| 层 | 方案 |
|----|------|
| **Facts 层** | 保持中文输出（作为 LLM 输入） |
| **LLM 输出** | System prompt 指定输出语言："请用{用户语言}回答" |
| **防止漂移** | 在 system prompt 中明确：不要直译 Facts 中的术语，用自然语言解释 |

---

## 数据定位总表

| 数据项 | Facts 路径 | Index 路径 | 状态 |
|--------|-----------|------------|------|
| 年度评级 (Y%) | `facts.luck.groups[].liunian[].total_risk_percent` | `index.year_grade.last5[].Y` | ✅ |
| 开始/后来评级 | `facts.luck.groups[].liunian[].{start_good, later_good}` | `index.year_grade.last5[].{start, later}` | ✅ |
| 年度 hints | `facts.luck.groups[].liunian[].hints[]` | 无（直接读 facts） | ✅ |
| 大运评级 | `facts.luck.groups[].dayun.zhi_good` | `index.dayun.fortune_label` | ✅ |
| 用神互换 | `facts.luck.groups[].dayun.yongshen_swap_hint` | `index.dayun.yongshen_swap.windows[]` | ✅ |
| turning_points | `facts.turning_points[]` | `index.turning_points.{nearby, should_mention}` | ✅ |
| 主要性格 | `facts.natal.dominant_traits[]` | `index.personality.axis_summaries[]` | ✅ |
| 用神五行 | `facts.natal.yongshen_elements[]` | 无 | ✅ |
| 感情窗口 | `facts.indexes.relationship.years[]` | `index.relationship.{hit, years_hit, last5_years_hit}` | ✅ |
| 婚配倾向 | `facts.natal.marriage_hint` | 无 | ✅ |
| 下一个好运年 | 无 | `index.good_year_search.next_good_year` | ✅ |
| 下一个好大运 | 无 | 无 | ❌ TODO |

---

## Free Tier (Q1-Q4)

### Q1：最近 N 年怎么样

**用户问法**：最近怎么样 / 这几年运势 / 最近五年

| 项 | 说明 |
|----|------|
| **数据来源** | `index.year_grade.last5[]` + `index.turning_points.nearby[]` |
| **裁剪逻辑** | 1) 输出 last5 年度评级<br>2) 凶/明显变动年 drill-down 输出 hints<br>3) 如有 turning_points 则提及 |
| **当前状态** | ✅ year_grade.last5 已实现<br>⚠️ turning_points.nearby 窗口需改为 last5 |
| **TODO** | 月份规则（<=7月不含今年） |

---

### Q2：我这个人是什么样的

**用户问法**：我的性格 / 我是什么人 / 性格优势

| 项 | 说明 |
|----|------|
| **数据来源** | `facts.natal.dominant_traits[]` + `facts.natal.liuqin_zhuli` |
| **裁剪逻辑** | 直接输出性格文案（cli.py 已格式化） |
| **当前状态** | ✅ 完整实现 |

---

### Q3：某年运势（Year Detail）

**用户问法**：2025年怎么样 / 今年运势

| 项 | 说明 |
|----|------|
| **数据来源** | `facts.luck.groups[].liunian[year]` |
| **裁剪逻辑** | 输出该年评级 + 所有 hints |
| **当前状态** | ✅ 完整实现 (year_detail.py + cli.py) |

---

### Q4：过去/当前感情状况

**用户问法**：最近感情怎么样 / 以前恋爱顺不顺

| 项 | 说明 |
|----|------|
| **数据来源** | `index.relationship.last5_years_hit[]` → 定位年份<br>`facts.luck.groups[].liunian[year].hints[]` → 过滤感情 hints |
| **裁剪逻辑** | 1) Index 告诉我们哪些年命中<br>2) 只输出这些年的感情相关 hints |
| **当前状态** | ✅ Index 已汇总命中年份<br>⚠️ hints 需按关键词过滤 |
| **感情 hints 关键词** | "缘分"、"婚姻宫"、"夫妻宫"、"合冲同现"、"婚恋" |

---

## Paid Tier (Q5-Q12)

### Q5：未来某年运势

**用户问法**：明年怎么样 / 2027年运势

| 项 | 说明 |
|----|------|
| **数据来源** | 与 Q3 相同，但读 future 年份 |
| **口径** | 好 → "机会多好好把握"<br>差 → "三思而后行，小心谨慎" |
| **当前状态** | ✅ 完整实现 |

---

### Q6：适合什么行业

**用户问法**：适合做什么行业 / 做什么工作好

| 项 | 说明 |
|----|------|
| **数据来源** | `facts.natal.yongshen_elements[]` + `index.dayun.yongshen_swap.windows[]` |
| **裁剪逻辑** | **新函数** `build_industry_text()`：<br>1) 检查有无 yongshen_swap windows<br>2) 无 → 输出用神行业<br>3) 有 → 输出"平时适合 X 行业，但在 YYYY-YYYY 年间更适合 Y 行业" |
| **当前状态** | ⚠️ 需新建函数 + 行业映射表 |
| **不需要 Payload** | 函数直接输出可读文本 |

**新函数设计**：
```python
# bazi/industry_text.py

YONGSHEN_INDUSTRY = {
    "金": "金融、法律、IT、机械制造",
    "木": "教育、医疗、创意、出版",
    "水": "物流、旅游、传媒、咨询",
    "火": "餐饮、娱乐、能源、电子",
    "土": "房产、农业、建筑、人力资源",
}

def build_industry_text(yongshen_elements: list, yongshen_swap_windows: list) -> str:
    """输出行业建议文本，直接喂给 LLM。"""
    base_industry = "、".join(YONGSHEN_INDUSTRY.get(e, "") for e in yongshen_elements if e in YONGSHEN_INDUSTRY)

    if not yongshen_swap_windows:
        return f"用神五行：{'、'.join(yongshen_elements)}\n更适合的行业方向：{base_industry}"

    lines = [f"用神五行：{'、'.join(yongshen_elements)}"]
    lines.append(f"默认更适合的行业方向：{base_industry}")
    lines.append("")
    lines.append("注意：大运变化期间行业偏好可能调整：")
    for w in yongshen_swap_windows:
        start = w["year_range"]["start_year"]
        end = w["year_range"]["end_year"]
        to_elements = w["to_elements"]
        swap_industry = "、".join(YONGSHEN_INDUSTRY.get(e, "") for e in to_elements if e in YONGSHEN_INDUSTRY)
        lines.append(f"  - {start}-{end}年：更适合 {swap_industry}")

    return "\n".join(lines)
```

---

### Q7：我会不会有钱/出名

**用户问法**：我会不会有钱 / 什么时候起色 / 能不能出名

| 项 | 说明 |
|----|------|
| **数据来源** | `index.year_grade.future3[]` + `index.good_year_search.next_good_year` |
| **裁剪逻辑** | 1) 看 future3 评级<br>2) 都不好 → 找 next_good_year<br>3) 输出"X年会有起色" |
| **当前状态** | ✅ 基本实现<br>⚠️ TODO: next_good_dayun |

---

### Q8：什么时候遇到对的人

**用户问法**：什么时候脱单 / 什么时候遇到正缘

| 项 | 说明 |
|----|------|
| **数据来源** | `index.relationship.years_hit[]`（过滤 > base_year） |
| **裁剪逻辑** | 输出未来最近的命中年份 + 该年的缘分 hints |
| **当前状态** | ✅ Index 已有 years_hit<br>⚠️ TODO: 增加 next_hit_year 字段更清晰 |

---

### Q9：今年要不要做 X 决定

**用户问法**：今年适合跳槽吗 / 今年能买房吗 / 要不要投资

| 项 | 说明 |
|----|------|
| **数据来源** | 今年的 year_grade + hints |
| **裁剪逻辑** | 与 Q3/Q5 相同 |
| **口径** | 好 → "更可能成功"<br>差 → "风险较高，建议保守" |
| **当前状态** | ✅ 完整实现 |

---

### Q10：我适合当 X 职业吗

**用户问法**：我适合当 rapper 吗 / 适合当商人吗

| 项 | 说明 |
|----|------|
| **数据来源** | `facts.natal.yongshen_elements[]` + 职业→五行映射 |
| **裁剪逻辑** | **新函数** `check_career_fit()`：查职业五行 vs 用神五行，输出匹配度文本 |
| **当前状态** | ⚠️ 需新建函数 + 职业映射表 |
| **不需要 Payload** | 函数直接输出可读文本 |

**新函数设计**：
```python
# bazi/career_fit.py

CAREER_ELEMENT = {
    "rapper": ["火", "木"],      # 表达、创意
    "商人": ["金", "土"],        # 交易、资源
    "程序员": ["金", "水"],      # 逻辑、技术
    "老师": ["木", "火"],        # 教育、传播
    "医生": ["木", "水"],        # 医疗、研究
}

def check_career_fit(career: str, yongshen_elements: list) -> str:
    """输出职业适配度文本。"""
    career_elements = CAREER_ELEMENT.get(career, [])
    if not career_elements:
        return f"暂无 {career} 的五行映射数据"

    overlap = set(career_elements) & set(yongshen_elements)
    if len(overlap) >= 1:
        return f"你的用神五行（{'、'.join(yongshen_elements)}）与 {career} 需要的五行（{'、'.join(career_elements)}）有重合，更容易发挥优势。"
    else:
        return f"{career} 需要的五行（{'、'.join(career_elements)}）不在你的用神范围内，可能需要额外努力。"
```

---

### Q11：TA 爱不爱我

**用户问法**：他爱我吗 / 她对我有感觉吗

| 项 | 说明 |
|----|------|
| **数据来源** | 今年的感情 hints（合/冲/配偶星） |
| **裁剪逻辑** | 输出今年感情相关 hints |
| **口径** | 有合 + 配偶星 → "感情有推进机会"<br>有冲 → "关系可能有波动" |
| **当前状态** | ✅ 完整实现 |

---

### Q12：什么样的人会爱我

**用户问法**：什么样的人适合我 / 我的正缘是什么类型

| 项 | 说明 |
|----|------|
| **数据来源** | `facts.natal.marriage_hint` |
| **裁剪逻辑** | 直接输出 marriage_hint |
| **当前状态** | ✅ 完整实现 (enrich.py 已生成) |

---

## 技术方案总结

### 所有问题的解决方案

| 问题 | 方案 | 需要新建 |
|------|------|----------|
| Q1 | Index.year_grade.last5 + Index.turning_points | ⚠️ turning_points 窗口改为 last5 |
| Q2 | Facts.natal.dominant_traits | - |
| Q3 | Facts.liunian[year] | - |
| Q4 | Index.relationship.last5_years_hit → Facts hints | ⚠️ hints 过滤关键词 |
| Q5 | 同 Q3 | - |
| Q6 | Index.yongshen_swap + **新函数** | ✅ `build_industry_text()` |
| Q7 | Index.year_grade.future3 + Index.good_year_search | ⚠️ next_good_dayun |
| Q8 | Index.relationship.years_hit (future) | ⚠️ next_hit_year |
| Q9 | 同 Q3/Q5 | - |
| Q10 | 用神五行 + **新函数** | ✅ `check_career_fit()` |
| Q11 | Facts hints (今年感情) | - |
| Q12 | Facts.natal.marriage_hint | - |

### 不需要 Payload 的原因

1. **感情问题**：Index.relationship 已汇总命中年份，不需要逐年查
2. **行业/职业**：新函数直接输出可读文本，作为 Facts 的一部分喂给 LLM
3. **所有问题**：最终都转化为"文本块 → LLM → 输出"

---

## TODO 清单

| 优先级 | TODO | 落点 | 相关 Q |
|--------|------|------|--------|
| P0 | ✅ Year detail 打印层协议化 | `bazi/cli.py` | Q3/Q5 |
| P0 | Yun detail 打印层协议化 | `bazi/cli.py` | - |
| P0 | 原局 detail 打印层协议化 | `bazi/cli.py` | Q2 |
| P0 | last5 月份规则（<=7月不含今年） | `request_index.py:99` | Q1 |
| P0 | turning_points.nearby 改为 last5 窗口 | `request_index.py:322` | Q1 |
| P1 | 新建 `build_industry_text()` | `bazi/industry_text.py` | Q6 |
| P1 | 新建 `check_career_fit()` | `bazi/career_fit.py` | Q10 |
| P1 | Index 增加 next_good_dayun | `request_index.py` | Q7 |
| P1 | Index 增加 relationship.next_hit_year | `request_index.py` | Q8 |
| P2 | hints 增加 category 标签 | `enrich.py` | Q4 |

---

## 关键文件索引

| 文件 | 职责 |
|------|------|
| `bazi/request_index.py` | Index 生成（year_grade, turning_points, relationship, good_year_search） |
| `bazi/enrich.py` | hints 生成（缘分、婚恋、风险管理） |
| `bazi/cli.py` | 打印层（性格、流年、大运） |
| `bazi/year_detail.py` | Year detail 结构化 |
| `bazi/relationship_index.py` | 感情窗口检测 |
| `bazi/dayun_index.py` | 用神互换检测 |
| `bazi/industry_text.py` | **TODO** 行业建议文本 |
| `bazi/career_fit.py` | **TODO** 职业适配文本 |

---

---

## 当前进展

**打印层协议化**（2026-01-26）：
- ✅ Year detail 已完成协议化：`- HINTS -` / `- DEBUG -` / `@` 结束符
- ⏳ 下一步：Yun detail 和原局 detail 协议化
- ⏳ 需新增：用神行业函数 + 大运期间职业变化显示

---

*Last updated: 2026-01-26*
