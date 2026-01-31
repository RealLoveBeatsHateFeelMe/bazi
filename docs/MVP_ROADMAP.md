# MVP 路线图：12 个问题实施方案

## 一、问题全览

### Free Tier（4个问题）

| 问题 | 描述 | 主要数据来源 |
|------|------|------------|
| **Q1** | 最近 N 年怎么样 | index.year_grade.last5, index.turning_points, liunian.hints |
| **Q2** | 我这个人是什么样的 | facts.natal.dominant_traits, facts.natal.liuqin_zhuli |
| **Q3** | 某年运势（Year Detail） | facts.luck.groups[].liunian[year] |
| **Q4** | 过去/当前感情状况 | index.relationship.last5_years_hit, liunian.hints（感情） |

### Paid Tier（8个问题）

| 问题 | 描述 | 主要数据来源 |
|------|------|------------|
| **Q5** | 未来某年运势 | facts.luck.groups[].liunian[year]（未来） |
| **Q6** | 适合什么行业 | facts.natal.yongshen_elements, index.dayun.yongshen_swap |
| **Q7** | 我会不会有钱/出名 | index.good_year_search, index.dayun.future_dayuns（新增） |
| **Q8** | 什么时候遇到对的人 | index.relationship.years_hit（future），liunian.hints（感情） |
| **Q9** | 今年要不要做 X 决定 | facts.luck.groups[].liunian[year]（今年） |
| **Q10** | 我适合当 X 职业吗 | facts.natal.yongshen_elements + 职业映射 |
| **Q11** | TA 爱不爱我 | liunian.hints（今年感情），配偶星、合冲 |
| **Q12** | 什么样的人会爱我 | facts.natal.marriage_hint, facts.natal.marriage_structure |

---

## 二、问题优先级排序

### 优先级标准

1. **用户需求频率**：用户最常问的问题排在前面
2. **实现难度**：简单的问题优先实现
3. **数据依赖**：依赖已有数据的问题优先
4. **MVP 核心价值**：能体现产品核心价值的问题优先

### 优先级排序结果

| 优先级 | 问题 | 用户需求 | 实现难度 | 数据依赖 | MVP 重要性 | 综合评分 |
|--------|------|---------|---------|---------|-----------|---------|
| **P0** | Q1: 最近N年怎么样 | 🔥🔥🔥🔥🔥 | ★★☆☆☆ | ✅ 已有 | 🌟🌟🌟🌟🌟 | **95** |
| **P0** | Q2: 我这个人是什么样的 | 🔥🔥🔥🔥🔥 | ★☆☆☆☆ | ✅ 已有 | 🌟🌟🌟🌟🌟 | **98** |
| **P0** | Q3: 某年运势 | 🔥🔥🔥🔥 | ★☆☆☆☆ | ✅ 已有 | 🌟🌟🌟🌟 | **90** |
| **P1** | Q4: 过去/当前感情状况 | 🔥🔥🔥🔥 | ★★☆☆☆ | ✅ 已有 | 🌟🌟🌟🌟 | **85** |
| **P1** | Q6: 适合什么行业 | 🔥🔥🔥🔥 | ★★★☆☆ | ✅ 已有 | 🌟🌟🌟🌟 | **80** |
| **P1** | Q12: 什么样的人会爱我 | 🔥🔥🔥 | ★★☆☆☆ | ✅ 已有 | 🌟🌟🌟 | **75** |
| **P2** | Q7: 我会不会有钱/出名 | 🔥🔥🔥 | ★★★★☆ | ⚠️ 部分缺失 | 🌟🌟🌟🌟 | **70** |
| **P2** | Q8: 什么时候遇到对的人 | 🔥🔥🔥 | ★★☆☆☆ | ✅ 已有 | 🌟🌟🌟 | **72** |
| **P2** | Q9: 今年要不要做X决定 | 🔥🔥🔥 | ★★☆☆☆ | ✅ 已有 | 🌟🌟🌟 | **73** |
| **P3** | Q5: 未来某年运势 | 🔥🔥 | ★☆☆☆☆ | ✅ 已有 | 🌟🌟 | **60** |
| **P3** | Q10: 我适合当X职业吗 | 🔥🔥 | ★★★☆☆ | ⚠️ 需要职业映射 | 🌟🌟 | **55** |
| **P3** | Q11: TA爱不爱我 | 🔥🔥 | ★★★★☆ | ✅ 已有 | 🌟🌟 | **52** |

**优先级说明**：
- **P0**（必须实现）：Q1, Q2, Q3 - MVP 核心问题，用户需求最高
- **P1**（重要实现）：Q4, Q6, Q12 - 重要问题，体现产品差异化价值
- **P2**（尽量实现）：Q7, Q8, Q9 - 付费功能，增加产品价值
- **P3**（可后续迭代）：Q5, Q10, Q11 - 补充问题，可后续优化

---

## 三、实施路线图

### Phase 1: MVP 核心功能（P0 级别）- 第1周

#### 1.1 Q2: 我这个人是什么样的

**实现难度**：★☆☆☆☆（最简单）

**当前状态**：
- ✅ 数据已完整：facts.natal.dominant_traits, facts.natal.liuqin_zhuli
- ✅ 打印已完整：主要性格、性格快速汇总、六亲助力

**需要做的**：
1. 在 chat_api 中创建 Q2 的输出函数
2. 从 facts.natal 提取性格数据
3. 格式化输出（LLM 友好）
4. 编写回归测试

**预计工作量**：1-2天

---

#### 1.2 Q3: 某年运势（Year Detail）

**实现难度**：★☆☆☆☆（简单）

**当前状态**：
- ✅ 数据已完整：facts.luck.groups[].liunian[year]
- ✅ year_detail.py 已实现

**需要做的**：
1. 在 chat_api 中创建 Q3 的输出函数
2. 调用 generate_year_detail(facts, target_year)
3. 格式化输出（包含：半年评级、天干地支块、hints 汇总、大运简述）
4. 编写回归测试

**预计工作量**：1-2天

---

#### 1.3 Q1: 最近N年怎么样

**实现难度**：★★☆☆☆（中等）

**当前状态**：
- ✅ 基础数据已完整：index.year_grade.last5, index.turning_points
- ⚠️ 需要细化：凶年/变动年钻取、天干五合感情提醒、Turning Points 条件输出

**需要做的**：

**阶段1：基础版 Q1**（1-2天）
1. 在 chat_api 中创建 Q1 的输出函数
2. 从 index.year_grade.last5 提取最近5年评级
3. 格式化输出（年份 + 评级）
4. 编写回归测试

**阶段2：细化版 Q1**（2-3天）
1. **凶年/变动年钻取 hints**：
   - 遍历 last5_years，计算每年的 half_year_grade
   - 如果 start_grade 或 later_grade 是"凶"或"变动"，提取该年的 hints
   - 简略复述该年的主要 hints（最多3条）

2. **天干五合感情提醒**：
   - 遍历 last5_years，检查每年的 hints
   - 过滤包含"婚恋变化提醒（如恋爱）"的 hints
   - 提取并简略汇总

3. **Turning Points 条件输出**：
   - 从 index.turning_points.nearby 中过滤出"过去5年内"的转折点
   - 如果有转折点，输出；如果没有，不输出
   - 输出格式："2023年：一般 → 好运（地支转折）"

4. 编写回归测试

**预计工作量**：3-5天

**总计 Phase 1**：5-9天

---

### Phase 2: 重要功能（P1 级别）- 第2周

#### 2.1 Q4: 过去/当前感情状况

**实现难度**：★★☆☆☆（中等）

**当前状态**：
- ✅ 数据已完整：index.relationship.last5_years_hit
- ⚠️ 需要从 liunian.hints 中过滤感情相关的 hints

**需要做的**：
1. 在 chat_api 中创建 Q4 的输出函数
2. 从 index.relationship.last5_years_hit 提取命中年份
3. 对每个命中年份，提取感情相关的 hints：
   - "婚恋变化提醒（如恋爱）"
   - "提示：缘分（天干/地支）"
   - "提示：感情线合冲同现"
4. 格式化输出
5. 编写回归测试

**预计工作量**：2-3天

---

#### 2.2 Q6: 适合什么行业

**实现难度**：★★★☆☆（中等偏难）

**当前状态**：
- ✅ 数据已完整：facts.natal.yongshen_elements, index.dayun.yongshen_swap
- ⚠️ 需要建立"五行 → 行业"的映射表

**需要做的**：
1. 创建"五行 → 行业"映射表（参考 BAZI_RULES.md）：
   - 木：文教、培训、创意、设计
   - 火：营销、表达、传媒、演艺
   - 土：稳定、管理、地产、中介
   - 金：金融、法律、执行、技术
   - 水：智慧、策划、流动、贸易

2. 在 chat_api 中创建 Q6 的输出函数
3. 从 facts.natal.yongshen_elements 提取用神五行
4. 映射到推荐行业
5. 如果有用神互换，提示"在 X-X 年期间，适合转到 Y 行业"
6. 编写回归测试

**预计工作量**：3-4天

---

#### 2.3 Q12: 什么样的人会爱我

**实现难度**：★★☆☆☆（中等）

**当前状态**：
- ✅ 数据已完整：facts.natal.marriage_hint, facts.natal.marriage_structure
- ✅ 打印已完整：婚配倾向、婚恋结构

**需要做的**：
1. 在 chat_api 中创建 Q12 的输出函数
2. 从 facts.natal.marriage_hint 提取婚配倾向
3. 从 facts.natal.marriage_structure 提取婚恋结构特点（官杀混杂、财混杂、五合）
4. 格式化输出（描述适合的伴侣类型）
5. 编写回归测试

**预计工作量**：2-3天

**总计 Phase 2**：7-10天

---

### Phase 3: 付费功能（P2 级别）- 第3周

#### 3.1 Index 增强：未来两步大运

**实现难度**：★☆☆☆☆（简单）

**需要做的**：
1. 在 `request_index.py` 的 `_build_dayun_index` 中增加 `future_dayuns` 字段
2. 逻辑：
   - 找到当前大运的 index
   - 如果 `future_allowed = True`，取下两个大运（index+1, index+2）
   - 如果 `future_allowed = False`，`future_dayuns = []`
3. 编写回归测试

**预计工作量**：1天

---

#### 3.2 Index 增强：Turning Points 窗口调整

**实现难度**：★☆☆☆☆（简单）

**需要做的**：
1. 在 `request_index.py` 的 `_build_turning_points_index` 中调整窗口范围
2. 逻辑：
   - nearby: 过去5年 + 未来10年
   - nearby_start = base_year - 5
   - nearby_end = base_year + 10
3. 编写回归测试

**预计工作量**：0.5天

---

#### 3.3 Q7: 我会不会有钱/出名

**实现难度**：★★★★☆（较难）

**当前状态**：
- ✅ 部分数据已有：index.good_year_search.next_good_year
- ⚠️ 需要增加：index.dayun.future_dayuns（未来好大运）

**需要做的**：
1. 先完成 Index 增强（3.1）
2. 在 chat_api 中创建 Q7 的输出函数
3. 从 index.good_year_search 提取下一个好运年
4. 从 index.dayun.future_dayuns 提取未来好大运
5. 判断逻辑：
   - 如果未来10年内有好运年，输出"在 X 年有机会"
   - 如果未来有好大运，输出"在 X-X 年（大运）期间有机会"
6. 编写回归测试

**预计工作量**：3-4天

---

#### 3.4 Q8: 什么时候遇到对的人

**实现难度**：★★☆☆☆（中等）

**当前状态**：
- ✅ 数据已完整：index.relationship.years_hit（future）
- ✅ liunian.hints 已有感情提示

**需要做的**：
1. 在 chat_api 中创建 Q8 的输出函数
2. 从 index.relationship.years_hit 提取未来命中年份（需要过滤到未来）
3. 对每个命中年份，提取感情相关的 hints
4. 格式化输出（"在 X 年有机会遇到"）
5. 编写回归测试

**预计工作量**：2-3天

---

#### 3.5 Q9: 今年要不要做X决定

**实现难度**：★★☆☆☆（中等）

**当前状态**：
- ✅ 数据已完整：facts.luck.groups[].liunian[base_year]
- ✅ year_detail.py 已实现

**需要做的**：
1. 在 chat_api 中创建 Q9 的输出函数
2. 调用 generate_year_detail(facts, base_year) 获取今年详情
3. 分析今年的评级、用神情况、风险情况
4. 根据用户问题类型（X决定）给出建议：
   - 如果是财务决定：看财星是否用神、risk_percent 是否高
   - 如果是工作决定：看官杀星、印星情况
   - 如果是感情决定：看感情 hints
5. 格式化输出
6. 编写回归测试

**预计工作量**：3-4天

**总计 Phase 3**：9.5-12.5天

---

### Phase 4: 补充功能（P3 级别）- 第4周（可选）

#### 4.1 Q5: 未来某年运势

**实现难度**：★☆☆☆☆（简单）

**当前状态**：
- ✅ 数据已完整：facts.luck.groups[].liunian[year]（未来）
- ✅ year_detail.py 已实现

**需要做的**：
1. 复用 Q3 的逻辑
2. 增加付费门控（只有付费用户可以查询未来年份）
3. 编写回归测试

**预计工作量**：1天

---

#### 4.2 Q10: 我适合当X职业吗

**实现难度**：★★★☆☆（中等偏难）

**当前状态**：
- ✅ 数据已有：facts.natal.yongshen_elements
- ⚠️ 需要建立"职业 → 五行"的映射表

**需要做的**：
1. 创建"职业 → 五行"映射表：
   - 教师：木、火
   - 医生：木、土
   - 律师：金
   - 程序员：水、金
   - 销售：火、水
   - ...（需要补充更多职业）

2. 在 chat_api 中创建 Q10 的输出函数
3. 从用户输入中提取职业
4. 查询该职业对应的五行
5. 与 facts.natal.yongshen_elements 比对
6. 给出建议（适合/不适合/可以考虑）
7. 编写回归测试

**预计工作量**：3-4天

---

#### 4.3 Q11: TA爱不爱我

**实现难度**：★★★★☆（较难）

**当前状态**：
- ✅ 数据已有：liunian.hints（今年感情）
- ⚠️ 需要分析配偶星、合冲情况

**需要做的**：
1. 在 chat_api 中创建 Q11 的输出函数
2. 分析今年的感情 hints：
   - "提示：缘分（天干/地支）"
   - "婚恋变化提醒（如恋爱）"
   - "提示：感情线合冲同现"
3. 分析今年的配偶星情况（是否用神、是否有冲克）
4. 综合判断并给出建议
5. 编写回归测试

**预计工作量**：3-4天

---

#### 4.4 比劫影响财星助力

**实现难度**：★☆☆☆☆（简单）

**需要做的**：
1. 在 cli.py 的六亲助力打印部分（2904-3151行）
2. 在 `_get_liuqin_source` 函数中增加 `has_bijie` 参数
3. 判断年月天干是否都是比劫
4. 如果是，修改财星来源描述：
   - 男性：去掉"父亲/爸爸"，保留"妻子/老婆/伴侣"
   - 女性：去掉"父亲/爸爸"
5. 编写回归测试

**预计工作量**：1天

**总计 Phase 4**：8-10天

---

## 四、总体时间规划

### 总工作量估算

| Phase | 内容 | 预计工作量 | 优先级 |
|-------|------|-----------|--------|
| Phase 1 | MVP 核心功能（Q1, Q2, Q3） | 5-9天 | **必须** |
| Phase 2 | 重要功能（Q4, Q6, Q12） | 7-10天 | **必须** |
| Phase 3 | 付费功能（Q7, Q8, Q9, Index 增强） | 9.5-12.5天 | **重要** |
| Phase 4 | 补充功能（Q5, Q10, Q11, 比劫助力） | 8-10天 | **可选** |
| **总计** | | **29.5-41.5天** | |

### 最小可行产品（MVP）

**Phase 1 + Phase 2**（12-19天）：
- ✅ Q1: 最近N年怎么样（含细化）
- ✅ Q2: 我这个人是什么样的
- ✅ Q3: 某年运势
- ✅ Q4: 过去/当前感情状况
- ✅ Q6: 适合什么行业
- ✅ Q12: 什么样的人会爱我

**覆盖场景**：
- Free 用户：Q1, Q2, Q3, Q4（最常问的问题）
- Paid 用户：上述 + Q6, Q12（重要付费价值）

### 完整产品（Full Product）

**Phase 1 + Phase 2 + Phase 3**（21.5-31.5天）：
- ✅ 所有 MVP 功能
- ✅ Q7: 我会不会有钱/出名
- ✅ Q8: 什么时候遇到对的人
- ✅ Q9: 今年要不要做X决定
- ✅ Index 增强（未来两步大运、Turning Points 窗口）

**覆盖场景**：
- Free 用户：Q1, Q2, Q3, Q4
- Paid 用户：上述 + Q6, Q7, Q8, Q9, Q12（完整付费价值）

---

## 五、技术实施细节

### 5.1 代码结构建议

```
bazi/
├── chat_api.py                 # 主接口（现有）
├── questions/                  # 新建：问题处理模块
│   ├── __init__.py
│   ├── q1_recent_years.py      # Q1: 最近N年怎么样
│   ├── q2_personality.py       # Q2: 我这个人是什么样的
│   ├── q3_year_detail.py       # Q3: 某年运势
│   ├── q4_past_relationship.py # Q4: 过去/当前感情状况
│   ├── q5_future_year.py       # Q5: 未来某年运势
│   ├── q6_suitable_industry.py # Q6: 适合什么行业
│   ├── q7_wealth_fame.py       # Q7: 我会不会有钱/出名
│   ├── q8_meet_partner.py      # Q8: 什么时候遇到对的人
│   ├── q9_decision.py          # Q9: 今年要不要做X决定
│   ├── q10_suitable_job.py     # Q10: 我适合当X职业吗
│   ├── q11_love_me.py          # Q11: TA爱不爱我
│   └── q12_partner_type.py     # Q12: 什么样的人会爱我
├── mappings/                   # 新建：映射表模块
│   ├── __init__.py
│   ├── element_to_industry.py  # 五行 → 行业
│   └── job_to_element.py       # 职业 → 五行
└── ...
```

### 5.2 测试策略

**回归测试结构**：
```
tests/regression/
├── questions/
│   ├── test_q1_golden.py
│   ├── test_q2_golden.py
│   ├── ...
│   └── test_q12_golden.py
└── snapshots/
    ├── q1/
    │   ├── case1.txt
    │   ├── case2.txt
    │   └── ...
    ├── q2/
    └── ...
```

**每个问题的测试用例**：
- 至少 3 个测试用例
- 覆盖典型场景（好运、一般、凶）
- 覆盖边界情况（无数据、数据缺失）

### 5.3 数据依赖检查清单

在实施每个问题前，检查数据是否完整：

| 问题 | 数据来源 | 当前状态 | 备注 |
|------|---------|---------|------|
| Q1 | index.year_grade.last5 | ✅ | |
| Q1 | index.turning_points.nearby | ⚠️ | 需调整窗口 |
| Q1 | liunian.hints | ✅ | |
| Q2 | facts.natal.dominant_traits | ✅ | |
| Q2 | facts.natal.liuqin_zhuli | ✅ | |
| Q3 | facts.luck.groups[].liunian[year] | ✅ | |
| Q4 | index.relationship.last5_years_hit | ✅ | |
| Q5 | facts.luck.groups[].liunian[year] | ✅ | |
| Q6 | facts.natal.yongshen_elements | ✅ | |
| Q6 | index.dayun.yongshen_swap | ✅ | |
| Q7 | index.good_year_search | ✅ | |
| Q7 | index.dayun.future_dayuns | ❌ | 需新增 |
| Q8 | index.relationship.years_hit | ✅ | |
| Q9 | facts.luck.groups[].liunian[base_year] | ✅ | |
| Q10 | facts.natal.yongshen_elements | ✅ | 需职业映射表 |
| Q11 | liunian.hints | ✅ | 需复杂分析 |
| Q12 | facts.natal.marriage_hint | ✅ | |
| Q12 | facts.natal.marriage_structure | ✅ | |

---

## 六、风险与应对

### 6.1 主要风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| Q1 细化功能复杂度超预期 | 延期2-3天 | 中 | 先实现基础版，细化功能可后置 |
| Q6 行业映射表不完善 | 推荐不准确 | 高 | 参考 BAZI_RULES.md，先实现核心行业 |
| Q7 数据依赖未完成 | 阻塞实现 | 中 | 先完成 Index 增强（3.1） |
| Q10 职业映射表工作量大 | 延期2-3天 | 高 | 可后置到 Phase 4 |
| Q11 判断逻辑过于复杂 | 准确性低 | 中 | 简化逻辑，给出保守建议 |

### 6.2 质量保证

- **每个问题必须有回归测试**
- **每个问题必须有至少 3 个测试用例**
- **测试用例必须覆盖典型场景和边界情况**
- **代码 review 后才能合并**
- **文档必须同步更新**

---

## 七、成功标准

### MVP 成功标准（Phase 1 + Phase 2）

✅ 6 个核心问题全部实现
✅ 每个问题有完整的回归测试
✅ Free 用户体验流畅（Q1-Q4）
✅ Paid 用户有明显价值提升（Q6, Q12）
✅ 代码质量良好（无明显 bug）
✅ 文档完整（每个问题有使用说明）

### Full Product 成功标准（Phase 1 + Phase 2 + Phase 3）

✅ 9 个核心问题全部实现
✅ Index 增强完成（未来两步大运、Turning Points 窗口）
✅ 付费功能完整（Q7, Q8, Q9）
✅ 所有问题有完整的回归测试
✅ 用户体验优秀（响应快、准确性高）
✅ 代码质量优秀（可维护性好）
✅ 文档完整且清晰

---

## 八、下一步行动

1. ✅ 确认 MVP 路线图
2. 🔜 开始实施 Phase 1（Q2 → Q3 → Q1）
3. 🔜 编写回归测试
4. 🔜 完成 Phase 1 后，review 并确认 Phase 2
5. 🔜 根据实际进度调整 Phase 3 和 Phase 4

**建议起始顺序**：
1. Q2（最简单，快速验证框架）
2. Q3（复用 year_detail，建立流程）
3. Q1 基础版（建立年度汇总框架）
4. Q1 细化版（完善功能）
5. Q4, Q6, Q12（按顺序完成 Phase 2）
