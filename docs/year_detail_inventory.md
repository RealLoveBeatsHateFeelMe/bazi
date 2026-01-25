# Year Detail 识别 + 阈值总清单

> **生成日期**：2026-01-25
> **版本**：v1.0

---

## 1. Entry Points & Data Flow

### 1.1 主要入口文件

| 文件 | 函数 | 职责 |
|------|------|------|
| `bazi/cli.py` | `main()` → `_run_year_scope()` | CLI 入口，处理 `--year` 参数时调用年份报告生成 |
| `bazi/cli.py` | `_print_liunian_block()` | 打印单个流年块（含提示汇总区） |
| `bazi/year_detail.py` | `generate_year_detail()` | 生成 year_detail 结构化数据 |
| `bazi/luck.py` | `analyze_luck()` | 核心排盘 + 好运/坏运 + 冲信息 |
| `bazi/enrich.py` | `enrich_liunian()` | 为流年数据补充 hints、wuhe_events、love_signals |

### 1.2 Data Flow

```
用户输入 (生日 + 年份)
       │
       ▼
cli.py::main() → analyze_complete()
       │
       ▼
lunar_engine.py::analyze_complete() → luck.py::analyze_luck()
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
detect_branch_clash()                    detect_liunian_patterns()
detect_branch_punishments()              detect_flow_harmonies()
detect_sanhe_complete()                  detect_sanhui_complete()
       │                                         │
       └─────────────┬───────────────────────────┘
                     ▼
            luck.py: 汇总 all_events + 计算风险
                     │
                     ▼
            enrich.py::enrich_liunian() → 生成 hints[]
                     │
                     ▼
            year_detail.py::generate_year_detail()
                     │
                     ▼
            cli.py::_print_liunian_block() → 提示汇总区打印
```

---

## 2. Signals Inventory（信号清单）

### 2.1 Patterns（模式）

| Signal ID | 中文名 | 检测函数 | 风险系数 | 输出位置 |
|-----------|--------|----------|----------|----------|
| `hurt_officer` | 伤官见官 | `patterns.py::detect_liunian_patterns()` | 默认15%；若伤官是用神则10% | 提示汇总 |
| `pianyin_eatgod` | 枭神夺食 | `patterns.py::detect_liunian_patterns()` | 默认15%；若枭神是用神则10% | 提示汇总 |
| `pattern_static_activation` | 静态模式激活 | `luck.py` | 命局5%/组；大运5%/组 | 事件区 |

**提示汇总文案**：

| 模式 | 单次格式 | 多次格式 |
|------|----------|----------|
| 伤官见官 | `（{位置串}）引动伤官见官：{文案}` | `引发多次伤官见官：{文案}` |
| 枭神夺食 | `（{位置串}）引动枭神夺食：{文案}` | `引发多次枭神夺食：{文案}` |

**Hint 文案常量**（定义于 `cli.py`）：

```python
_HURT_OFFICER_HINT = "主特征｜外部对抗：更容易出现来自外部的人/权威/规则的正面冲突与摩擦。表现形式（仅类别）：口舌是非/名声受损；合同/合规/官非；意外与身体伤害；（女性）伴侣关系不佳或伴侣受伤。"

_PIANYIN_EATGOD_HINT = "主特征｜突发意外：更容易出现突如其来的变故与波折，打乱节奏。表现形式（仅类别）：判断失误/信息偏差→麻烦与灾祸；钱财损失；犯小人/被拖累；意外的身体伤害风险上升。"
```

---

### 2.2 Collisions（冲）

| Signal ID | 中文名 | 检测函数 | 风险系数 | 输出位置 |
|-----------|--------|----------|----------|----------|
| `branch_clash` | 流年与命局冲 | `clash.py::detect_branch_clash()` | 基础10%；墓库+5%；天克地冲+10% | 事件区 |
| `dayun_liunian_branch_clash` | 运年相冲 | `luck.py` | 基础10%；墓库+5%；运年天克地冲+20% | 事件区 |
| `static_clash_activation` | 静态冲激活 | `luck.py` | 基础风险的一半 | 事件区 |
| `tian_ke_di_chong` | 天克地冲 | `clash.py::_check_tian_ke_di_chong()` | 额外+10%（叠加在冲之上） | 提示汇总 |

**天克地冲提示汇总文案**：

| 情况 | 格式 |
|------|------|
| 单次 | `（{位置串}）引动天克地冲：{文案}` |
| 多次 | `引发多次天克地冲：{文案}` |

**Hint 文案常量**：

```python
_TKDC_HINT = "可能出现意外、生活环境剧变，少数情况下牵动亲缘离别。"
```

---

### 2.3 Hour Clash（时支被流年冲）

| Signal ID | 中文名 | 检测函数 | 输出位置 |
|-----------|--------|----------|----------|
| `hour_clash_by_liunian` | 时支被流年冲 | `cli.py::_check_hour_clash_by_liunian()` | 提示汇总 |

**提示汇总格式**：

```
（时支{hour_zhi}/流年{liunian_zhi}）时支被流年冲：可能搬家/换工作。
```

---

### 2.4 Amplifiers（增幅器）

| Signal ID | 中文名 | 检测函数 | 风险系数 | 触发条件 |
|-----------|--------|----------|----------|----------|
| `lineyun_bonus` | 线运加成 | `luck.py::_compute_lineyun_bonus()` | 天干侧6% + 地支侧6% | 单柱总风险 >= 10% |
| `sanhe_sanhui_clash_bonus` | 三合/三会逢冲加分 | `luck.py::_detect_sanhe_sanhui_clash_bonus()` | 35%（用神）或15%（非用神） | 当年有冲 + 三合/三会成立 |
| `clash_pattern_bonus` | 冲+模式重叠加成 | `luck.py` | +10%（叠加在冲之上） | 同一对地支既冲又模式 |

---

### 2.5 Relationship（感情信号）

| Signal ID | 中文名 | 来源 | 输出位置 |
|-----------|--------|------|----------|
| `liuyuan_gan` | 缘分（天干） | `enrich.py` | 提示汇总 |
| `liuyuan_zhi` | 缘分（地支） | `enrich.py` | 提示汇总 |
| `marriage_palace_clash` | 婚姻宫/夫妻宫被冲 | `enrich.py` | 提示汇总 |
| `marriage_palace_harmony` | 婚姻宫/夫妻宫被合 | `enrich.py` | 提示汇总 |
| `he_and_chong_coexist` | 合冲同现 | `enrich.py::_compute_love_signals()` | 提示汇总 |
| `marriage_wuhe_hints` | 天干五合婚恋提醒 | `marriage_wuhe.py::detect_marriage_wuhe_hints()` | 提示汇总 |

**提示汇总文案**：

| 信号 | 文案 |
|------|------|
| 缘分（天干） | `提示：缘分（天干）：暧昧推进` |
| 缘分（地支） | `提示：缘分（地支）：易遇合适伴侣（良缘）` |
| 婚姻宫/夫妻宫被冲 | `提示：感情（单身：更易暧昧/受阻；有伴侣：争执起伏）` |
| 婚姻宫/夫妻宫被合 | `提示：{宫位}引动（单身：更容易出现暧昧/推进；有伴侣：关系推进或波动）` |
| 合冲同现 | `提示：感情线合冲同现（进展易受阻/反复拉扯；仓促定论的稳定性更低）` |

---

### 2.6 Relocation（搬迁/工作变动）

| Signal ID | 中文名 | 触发条件 | 输出位置 |
|-----------|--------|----------|----------|
| `hour_clash_hint` | 时支被流年冲 | 流年地支冲时支 | 提示汇总 |
| `hour_tkdc_hint` | 事业家庭宫天克地冲 | 天克地冲命中时柱 | 提示汇总 |
| `family_change_hint` | 家庭变动 | 事业家庭宫被冲（且无时柱天克地冲） | 提示汇总 |
| `dayun_liunian_tkdc_hint` | 运年天克地冲 | 大运与流年天克地冲 | 提示汇总 |

**提示汇总文案**：

| 信号 | 文案 |
|------|------|
| 时支被流年冲 | `（时支{zhi}/流年{zhi}）时支被流年冲：可能搬家/换工作。` |
| 事业家庭宫天克地冲 | `提示：事业家庭宫天克地冲（工作变动概率上升/可能出现搬家窗口）` |
| 家庭变动 | `提示：家庭变动（搬家/换工作/家庭节奏变化）` |
| 运年天克地冲 | `提示：运年天克地冲（家人去世/生活环境变化剧烈，如出国上学打工）` |

---

### 2.7 Advice（建议信号）

| Signal ID | 中文名 | 触发条件 | 输出位置 |
|-----------|--------|----------|----------|
| `risk_management_advice` | 风险管理选项 | `total_risk_percent >= 40%` | 提示汇总 |

**提示汇总文案**：

```
风险管理选项（供参考）：保险/预案；投机回撤风险更高；合规优先；职业变动成本更高；情绪波动时更易误判；重大决定适合拉长周期
```

---

### 2.8 Meta（元信息）

| Signal ID | 中文名 | 来源 | 用途 |
|-----------|--------|------|------|
| `year` | 年份 | `liunian["year"]` | 标识 |
| `gan` / `zhi` | 流年干支 | `liunian` | 天干块 / 地支块 |
| `gan_shishen` / `zhi_shishen` | 流年十神 | `luck.py` | 天干块 / 地支块 |
| `is_gan_yongshen` / `is_zhi_yongshen` | 是否用神 | `luck.py` | 天干块 / 地支块 |
| `risk_from_gan` / `risk_from_zhi` | 天干/地支风险 | `luck.py` | 风险拆分 |
| `total_risk_percent` | 总风险 | `luck.py` | 整体风险评估 |

---

## 3. Thresholds Inventory（阈值清单）

### 3.1 开始/后来等级判定

**判定逻辑**（定义于 `year_detail.py::_compute_half_year_grade()`）：

#### 开始（天干侧）

| 条件 | 等级 |
|------|------|
| `start_good == None` | 变动 |
| `start_good == True` 且 `risk_from_gan <= 20` | 好运 |
| `start_good == True` 且 `risk_from_gan > 20` | 一般 |
| `start_good == False` 且 `risk_from_gan <= 30` | 一般 |
| `start_good == False` 且 `risk_from_gan > 30` | 凶 |

#### 后来（地支侧）

| 条件 | 等级 |
|------|------|
| `later_good == None` | 变动 |
| `later_good == True` 且 `risk_from_zhi <= 20` | 好运 |
| `later_good == True` 且 `risk_from_zhi > 20` | 一般 |
| `later_good == False` 且 `risk_from_zhi <= 30` | 一般 |
| `later_good == False` 且 `risk_from_zhi > 30` | 凶 |

---

### 3.2 大运好坏判定

**判定逻辑**（定义于 `luck.py`）：

| 条件 | 标签 |
|------|------|
| 地支是用神 且 `risk_dayun_total < 30` | 好运 |
| 地支是用神 且 `risk_dayun_total >= 30` | 坏运（用神过旺/变动过大） |
| 地支非用神 且 `risk_dayun_total <= 15` | 一般 |
| 地支非用神 且 `15 < risk_dayun_total <= 30` | 一般（有变动） |
| 地支非用神 且 `risk_dayun_total > 30` | 坏运 |

---

### 3.3 流年好运判定

**判定逻辑**（定义于 `luck.py`）：

| 条件 | is_good |
|------|---------|
| `(gan_good OR zhi_good)` 且 `total_risk_percent <= 15` | True |
| 其他 | False |

---

### 3.4 风险管理建议阈值

| 阈值 | 触发信号 |
|------|----------|
| `total_risk_percent >= 40` | `risk_management_advice` |

---

### 3.5 线运加成触发阈值

| 阈值 | 触发信号 |
|------|----------|
| 单柱总风险 >= 10% | 触发该侧（天干侧或地支侧）+6% |

---

### 3.6 风险系数常量

**定义于 `config.py`**：

| 常量名 | 值 | 说明 |
|--------|-----|------|
| `PATTERN_GAN_RISK_LIUNIAN` | 15.0 | 流年天干层模式每组 |
| `PATTERN_ZHI_RISK_LIUNIAN` | 15.0 | 流年地支层模式每组 |
| `PATTERN_GAN_RISK_STATIC` | 10.0 | 静态天干层模式每组 |
| `PATTERN_ZHI_RISK_STATIC` | 10.0 | 静态地支层模式每组 |
| `CLASH_NORMAL_RISK` | 10.0 | 普通冲 |
| `CLASH_GRAVE_RISK` | 15.0 | 墓库冲（辰戌丑未之间） |
| `STATIC_CLASH_NORMAL_RISK` | 5.0 | 静态普通冲（一半） |
| `STATIC_CLASH_GRAVE_RISK` | 7.5 | 静态墓库冲（一半） |
| `TIAN_KE_DI_CHONG_EXTRA_RISK` | 10.0 | 天克地冲额外风险 |

---

## 4. 提示汇总区打印顺序

**定义于 `cli.py::_print_liunian_block()`**：

1. 伤官见官（来自 `pattern_hints`）
2. 枭神夺食（来自 `pattern_hints`）
3. 天克地冲（来自 `_generate_tkdc_hint()`）
4. 时支被流年冲（来自 `_generate_hour_clash_hint()`）
5. 其他 hints（来自 `liunian["hints"]`）

---

## 5. Gap Report（缺口报告）

### 5.1 MISSING_HINT（有 Evidence 但无 Hint）

| Evidence | 当前状态 | 建议 |
|----------|----------|------|
| `branch_punishment` | 只计风险，无专属提示 | 考虑添加「刑」相关提示 |
| `sanhe_complete` / `sanhui_complete` | 只在事件区展示，无提示 | 考虑添加三合/三会成局提示 |
| `static_clash_activation` | 只计风险，无专属提示 | 考虑添加静态冲激活提示 |
| `static_punish_activation` | 只计风险，无专属提示 | 考虑添加静态刑激活提示 |

---

### 5.2 MISSING_EVIDENCE（有 Hint 但无明确 Evidence 溯源）

| Hint | 当前状态 | 建议 |
|------|----------|------|
| `婚恋变化提醒（如恋爱）` | 来自 `marriage_wuhe_hints`，但无 fact_id 链接 | 建议通过 FindingsCollector 建立 link |
| `缘分（天干）/缘分（地支）` | 直接基于十神判断，无 fact_id | 考虑创建 fact 记录十神信号 |

---

### 5.3 NOT_IN_HINT_SUMMARY（识别到但未进入提示汇总）

| Signal | 当前输出位置 | 是否应进入提示汇总 |
|--------|--------------|-------------------|
| `lineyun_bonus` | 事件区 | 否（增幅器，非主要提示） |
| `sanhe_sanhui_clash_bonus` | 事件区 | 否（增幅器） |
| `clash_pattern_bonus` | 事件区（叠加在冲上） | 否（已体现在模式提示中） |
| `dayun_patterns` | 大运块 | 否（大运层提示，非流年） |
| `branch_clash` 基础信息 | 事件区 | 部分（天克地冲单独提示） |

---

## 6. 附录：关键文件索引

| 文件 | 主要职责 |
|------|----------|
| `bazi/cli.py` | CLI 入口 + 打印逻辑 + pattern_hints 生成 |
| `bazi/luck.py` | 核心排盘 + 冲/刑/模式检测 + 风险计算 |
| `bazi/year_detail.py` | year_detail 结构化数据生成 |
| `bazi/enrich.py` | hints 生成 + love_signals + wuhe_events |
| `bazi/patterns.py` | 伤官见官 / 枭神夺食检测 |
| `bazi/clash.py` | 冲检测 + 天克地冲 |
| `bazi/punishment.py` | 刑检测 |
| `bazi/harmony.py` | 六合 / 三合 / 三会检测 |
| `bazi/marriage_wuhe.py` | 天干五合婚恋提醒 |
| `bazi/config.py` | 风险系数常量 + 映射表 |
| `bazi/findings_collector.py` | facts / hints / links 收集器 |

---

## 7. 更新记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-01-25 | v1.0 | 初版创建 |
