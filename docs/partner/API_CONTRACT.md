# API Contract Version 1.0.0

## Analyze 基础接口约定（API_CONTRACT）

本文件描述前端 / partner 需要消费的核心字段结构，来源于：

- `bazi.lunar_engine.analyze_basic(birth_dt)` → `basic`
- `bazi.luck.analyze_luck(birth_dt, is_male, yongshen_elements)` → `luck`

所有示例仅展示结构，真实数值以实际返回为准。

---

## 0. 统一响应壳（API Response Wrapper）

所有 API 响应必须遵循统一的外层响应壳结构，便于前端统一处理成功/失败。

### 0.1 成功响应（Success）

```python
{
  "ok": true,
  "data": {
    "basic": <analyze_basic>,  # analyze_basic 返回的完整结构
    "luck": <analyze_luck>?    # analyze_luck 返回的完整结构（可选）
  },
  "error": null
}
```

### 0.2 失败响应（Failure）

```python
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INVALID_INPUT" | "INTERNAL_ERROR" | "VALIDATION_ERROR" | ...,
    "message": "错误描述信息（用户友好）",
    "details": { ... }  # 可选，调试用详细信息
  }
}
```

### 0.3 说明

- `ok: boolean`：明确标识请求是否成功
- `data: object | null`：成功时包含业务数据，失败时为 `null`
  - `data.basic`：基础分析结果（analyze_basic 的完整返回）
  - `data.luck`：运势分析结果（analyze_luck 的完整返回，可选）
- `error: object | null`：失败时包含错误信息，成功时为 `null`
  - `error.code`：错误代码（字符串枚举）
  - `error.message`：用户友好的错误描述
  - `error.details`：可选的调试信息（对象，结构不固定）

**注意**：当前实现中，`analyze_basic` 和 `analyze_luck` 直接返回业务数据。实际 HTTP API 层需要在外层包装此响应壳。

---

## 1. analyze_basic 返回结构（basic）

```python
basic = {
  "bazi": {
    "year": {"gan": "甲", "zhi": "子"},
    "month": {"gan": "乙", "zhi": "丑"},
    "day": {"gan": "丙", "zhi": "寅"},
    "hour": {"gan": "丁", "zhi": "卯"},
  },
  "day_master_element": "火",
  "strength_percent": 72.5,
  "strength_score_raw": 0.45,
  "support_percent": 30.0,
  "drain_percent": 70.0,
  "global_element_percentages": {...},
  "yongshen_elements": ["木", "火"],
  "yongshen_detail": {...},
  "yongshen_shishen": [...],
  "yongshen_tokens": [...],
  "shishen_category_percentages": {...},
  "stem_pattern_summary": [...],
  "dominant_traits": [...],
  "natal_patterns": [...],
  "natal_conflicts": {...},
  "special_rules": [...],
}
```

### 1.1 用神相关字段

- `yongshen_elements: List[str]`
  - **最终用神五行列表**（包含规则补充后的），如 `["木","火"]`。
  - 等同于 `yongshen_detail.final_yongshen_elements`，保证永远一致。
- `yongshen_detail: Dict`
  - 用神计算的详细结构，包含基础用神与最终用神：
  - 结构：
    ```python
    {
      "day_gan": "壬",
      "day_element": "水",
      "strength_percent": 10.0,
      "global_distribution": {...},
      "base_yongshen_elements": ["金", "水"],      # 原始计算出的基础用神
      "final_yongshen_elements": ["金", "水", "木"], # 最终用神（包含规则补充，与顶层一致）
      "water_percent": 12.5
    }
    ```
  - **字段说明**：
    - `base_yongshen_elements`：根据日主强弱和全局五行占比，按规则计算出的基础用神
    - `final_yongshen_elements`：基础用神 + special_rules 补充后的最终用神，**与顶层 `yongshen_elements` 永远一致**
- `special_rules: List[str]`：特殊规则代码列表，可能的值：
  - `"weak_water_heavy_guansha_add_wood"`：弱水 + 官杀重 → 补木
  - `"weak_wood_heavy_metal_add_fire"`：弱木 + 强金（官杀%≥40%）+ 基础用神为水木 → 补火
- `yongshen_shishen: List[Dict]`
  - 用神五行在十神上的解释：
  - 结构：
    ```python
    {
      "element": "木",
      "categories": ["印星"],        # 五大类中的类别集合
      "shishens": ["正印", "偏印"],  # 具体十神集合
    }
    ```
- `yongshen_tokens: List[Dict]`
  - 用神在盘中的“落点字”清单（不含日干，地支按主气十神）：
  - 结构：
    ```python
    {
      "element": "木",
      "positions": [
        {
          "pillar": "year",        # year/month/day/hour
          "kind": "gan",           # gan/zhi
          "char": "甲",            # 该位置的字（天干或地支）
          "element": "木",         # 该字的五行（干用 GAN_WUXING，支用 ZHI_WUXING）
          "shishen": "偏印",       # 该字相对于日主的十神
        },
        ...
      ],
    }
    ```

### 1.2 主要性格 dominant_traits

- `dominant_traits: List[Dict]`
  - 只看原局（natal），排除日干，统计：
    - 年干 / 月干 / 时干（3 干）
    - 年支 / 月支 / 日支 / 时支（4 支，本气十神）
  - 权重：统一使用 `POSITION_WEIGHTS`。
  - 结构：
    ```python
    {
      "group": "财",              # 五大类之一：财 / 印 / 官杀 / 食伤 / 比劫
      "total_percent": 35.0,      # 该大类的总占比
      "mix_label": "正偏财混杂",  # 纯 / 混杂标签
      "detail": [
        {
          "name": "正财",
          "percent": 15.0,
          "stems_visible_count": 0,           # 年/月/时三干中该子类出现次数
          "breakdown": {
            "stems_percent": 0.0,             # 该子类在三干中的占比
            "branches_percent": 15.0,         # 该子类在四支本气中的占比
          },
        },
        {
          "name": "偏财",
          "percent": 20.0,
          "stems_visible_count": 2,
          "breakdown": {
            "stems_percent": 20.0,
            "branches_percent": 0.0,
          },
        },
      ],
    }
    ```

### 1.3 用神 explain 说明

- `yongshen_shishen` 和 `yongshen_tokens` 统一按**最终用神**（`final_yongshen_elements`）计算。
- **即使用神五行在原局没有落点字**，`yongshen_shishen` 也会给出理论十神解释：
  - 木 → 理论天干：甲乙 → 计算十神
  - 火 → 理论天干：丙丁 → 计算十神
  - 土 → 理论天干：戊己 → 计算十神
  - 金 → 理论天干：庚辛 → 计算十神
  - 水 → 理论天干：壬癸 → 计算十神
- `yongshen_tokens` 只记录**原局实际落点**，可能为空（这是允许的）。

### 1.4 其他字段（简要）

- `shishen_category_percentages: Dict[str,float]`：五大十神类别（比劫/财星/食伤/官杀/印星）的全局占比。
- `stem_pattern_summary: List[Dict]`：天干格局提示（哪类十神在四干上成势）。
- `natal_patterns` / `natal_conflicts`：原局十神模式与冲刑信息。
- `natal_harmonies: List[Dict]`：原局六合/三合/半合/三会组合（只解释，不计分）：
  ```python
  [
    {
      "type": "branch_harmony",
      "subtype": "liuhe" | "sanhe" | "banhe" | "sanhui",
      "role": "explain",
      "risk_percent": 0.0,
      "flow_type": "natal",
      "group": "水局" | "火局" | "木会" | "火会" | ...,
      "members": ["申", "子", "辰"],  # 该组固定成员
      "matched_branches": ["申", "子"],  # 本次实际组成的支
      "targets": [
        {
          "pillar": "year",
          "palace": "根基宫",
          "target_branch": "申",
          "position_weight": 0.10,
          "branch_gan": "庚",  # 可选
          "branch_shishen": {...},  # 可选
        },
        ...
      ]
    },
    ...
  ]
  ```

---

## 2. analyze_luck 返回结构（luck）

```python
luck = analyze_luck(birth_dt, is_male, yongshen_elements, max_dayun=8)

{
  "groups": [
    {
      "dayun": {...},      # 大运信息
      "liunian": [...],    # 对应十年流年信息
    },
    ...
  ]
}
```

### 2.1 大运 DayunLuck（摘录）

```python
dayun = {
  "index": 0,
  "gan": "甲",
  "zhi": "子",
  "gan_element": "木",
  "zhi_element": "水",
  "start_year": 2010,
  "start_age": 8,
  "gan_good": True,
  "zhi_good": False,
  "is_good": True,
  "clashes_natal": [...],   # 大运支与命局地支的冲事件
  "harmonies_natal": [...], # 大运支与原局的六合/三合/半合/三会（只解释，不计分）
}
```

### 2.2 流年 LiunianLuck（摘录）

```python
liunian = {
  "year": 2024,
  "age": 20,
  "gan": "甲",
  "zhi": "辰",
  "gan_element": "木",
  "zhi_element": "土",
  "first_half_good": True,
  "second_half_good": False,
  "clashes_natal": [...],   # 流年支与命局地支的冲
  "clashes_dayun": [...],   # 流年支与大运支的冲
}
```

前端通常只需要：

- 大运：干支 / 起运年 / 虚龄 / 好运标记；
- 流年：年份 / 虚龄 / 上半年好运? / 下半年好运? / 总风险 `total_risk_percent`；
- 冲信息可用于解释型文案；
- 六合/三合/半合/三会（`harmonies_natal`）可用于解释型文案（只解释，不计分）。

### 2.3 流年风险计算（新增）

流年字典包含：

- `total_risk_percent: float`：年度总风险（包含线运加成）
- `lineyun_bonus: float`：线运加成（0 或 6.0）
- `all_events: List[Dict]`：所有事件列表（包含冲、线运等）
- `harmonies_natal: List[Dict]`：流年支与原局的六合/三合/半合/三会（只解释，不计分）
- `harmonies_dayun: List[Dict]`：流年支与大运支的合类（目前为空，后续可扩展）

**线运规则**：
- 根据虚龄确定 `active_pillar`（0-16岁=年柱，17-32岁=月柱，33-48岁=日柱，49+岁=时柱）
- 扫描所有 `role="base"` 事件，判定触发：存在至少一条 base 事件满足：
  1. 该事件命中 `active_pillar`（`targets` 里有 `pillar == active_pillar`）
  2. 且该事件的 `risk_percent >= 10.0`
- 一旦触发，`lineyun_bonus = 6.0`，全年最多一次，不叠加、不分干支
- **年度总风险不封顶（可>100），只对单事件风险按各自规则封顶（例如冲事件自身封顶100）**


