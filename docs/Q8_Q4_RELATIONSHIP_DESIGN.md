# Q8 和 Q4 感情问题设计方案

---

## ✅ 功能实现状态（2026-01-31更新）

| 功能 | 状态 | 说明 |
|------|------|------|
| **Relationship Index 配偶星检测** | ✅ 已实现 | 已增加 `spouse_star_in_gan`（天干配偶星=能谈恋爱）, `spouse_star_in_zhi`（地支配偶星=遇到对的人） |
| **Relationship Index 合检测** | ✅ 已实现 | 已增加 `zhi_liuhe_combine`（地支六合）, `zhi_banhe_combine`（地支半合）=能谈恋爱 |
| **Relationship Index years_by_type** | ✅ 已实现 | 已增加 `years_by_type` 和 `last5_years_by_type` 字段 |
| **财星六亲助力删父亲** | ✅ 已实现 | 见 `IMPLEMENTATION_NOTES.md` §二 |

---

## 一、当前实现分析

### 1.1 Relationship Index 当前检测的情况

**代码位置**：`bazi/relationship_index.py`

**当前检测两种情况**：
1. **A. 冲到婚姻宫/夫妻宫**（palace_clash）
   - 流年支冲到月柱（婚姻宫）或日柱（夫妻宫）

2. **B. 天干争合官杀/财星**（competing_combine_official_kill / competing_combine_wealth）
   - 天干五合争合配偶星（第三者介入）

### 1.2 Hints 里已有的配偶星检测

**代码位置**：`bazi/enrich.py` (378-398行)

**已实现的配偶星检测**（在 `liunian.hints` 里）：

1. **天干配偶星**：
   - 男命：流年天干是正财/偏财 → `"提示：缘分（天干）：暧昧推进"`
   - 女命：流年天干是正官/七杀 → `"提示：缘分（天干）：暧昧推进"`

2. **地支配偶星**：
   - 男命：流年地支主气是正财/偏财 → `"提示：缘分（地支）：易遇合适伴侣（良缘）"`
   - 女命：流年地支主气是正官/七杀 → `"提示：缘分（地支）：易遇合适伴侣（良缘）"`

**关键发现**：
- ✅ 天干/地支配偶星的检测已经在程序里了！
- ✅ 地支配偶星的文案就是"易遇合适伴侣（良缘）"，符合用户的需求
- ✅ 天干配偶星的文案是"暧昧推进"，也符合用户说的"谈恋爱"

---

## 二、用户新需求

### 2.1 Q8: 什么时候遇到对的人

**用户定义**：
- **遇到对的人 = 地支出现配偶星**
- 地支出现配偶星，基本上会是比较合适的人
- 需要结合**婚配倾向**一起说明

**输出内容**：
1. 未来哪些年地支出现配偶星
2. 婚配倾向（什么样的人适合你）
3. 这些年的感情 hints

### 2.2 谈恋爱（是否需要单独成为一个问题？）

**用户定义**：
- **谈恋爱 = 合 + 天干/地支出现配偶星**
- 包括：
  - 冲到婚姻宫/夫妻宫
  - 天干争合配偶星
  - 天干出现配偶星
  - 地支出现配偶星

**用户疑问**：
> "是不是要分成两个问题，谈恋爱就合和天干地支配偶星都算，对的人就只算配偶星，然后把婚配倾向说出来"

### 2.3 Q4: 过去/当前感情状况

**用户要求**：
- 复查一下过去感情状态里面有没有包含天干、地支出现配偶星的
- 应该包含所有感情相关的 hints
- **也输出婚配倾向**（2026-01-30 新增）

---

## 三、实施方案

### 3.1 方案建议

**建议：不分成两个问题，而是在 Q8 和 Q4 里都展示完整的感情信息，但侧重点不同**

#### Q8: 什么时候遇到对的人

**侧重点**：地支配偶星（良缘）+ 婚配倾向

**输出结构**：
```
【最有可能遇到对的人的年份】
- 2026年：地支出现配偶星（易遇合适伴侣）
- 2029年：地支出现配偶星（易遇合适伴侣）

【婚配倾向】
适合找阳光、有正能量、有担当的伴侣

【其他感情信号年份】（可选）
- 2027年：天干出现配偶星（可能谈恋爱，但未必是对的人）
- 2028年：婚姻宫被冲（感情变动）
```

#### Q4: 过去/当前感情状况

**侧重点**：过去5年所有感情相关的 hints + 婚配倾向

**输出结构**：
```
【近5年感情状况】
- 2024年：
  - 地支出现配偶星：易遇合适伴侣（良缘）
  - 婚姻宫被冲：感情有变动

- 2023年：
  - 天干出现配偶星：暧昧推进
  - 天干争合配偶星：第三者介入风险

【婚配倾向】
适合找阳光、有正能量、有担当的伴侣

【婚恋结构】
官杀混杂，桃花多，易再婚，找不对配偶难走下去
```

---

### 3.2 Relationship Index 增强方案

**目标**：在 relationship_index 里增加配偶星检测

#### 当前结构
```python
{
    "hit": bool,
    "types": ["palace_clash", "competing_combine_official_kill", "competing_combine_wealth"],
    "years": [年份列表],
    "last5_hit": bool,
    "last5_years": [近5年命中的年份],
}
```

#### 增强后的结构
```python
{
    "hit": bool,
    "types": [
        "palace_clash",                    # 冲到婚姻宫/夫妻宫
        "competing_combine_official_kill", # 天干争合官杀
        "competing_combine_wealth",        # 天干争合财星
        "spouse_star_in_gan",              # 新增：天干出现配偶星
        "spouse_star_in_zhi",              # 新增：地支出现配偶星（良缘）
    ],
    "years": [年份列表],
    "years_by_type": {                     # 新增：按类型分组的年份
        "palace_clash": [年份],
        "competing_combine": [年份],        # 合并两种争合
        "spouse_star_in_gan": [年份],
        "spouse_star_in_zhi": [年份],       # 重点：遇到对的人
    },
    "last5_hit": bool,
    "last5_years": [近5年命中的年份],
    "last5_years_by_type": {               # 新增：近5年按类型分组
        "palace_clash": [年份],
        "competing_combine": [年份],
        "spouse_star_in_gan": [年份],
        "spouse_star_in_zhi": [年份],
    },
}
```

---

### 3.3 实施步骤

#### Step 1: 增强 Relationship Index（priority: P0）

**文件**：`bazi/relationship_index.py`

**修改内容**：
1. 增加两个新的类型常量：
   ```python
   RELATIONSHIP_TYPE_SPOUSE_STAR_IN_GAN = "spouse_star_in_gan"
   RELATIONSHIP_TYPE_SPOUSE_STAR_IN_ZHI = "spouse_star_in_zhi"
   ```

2. 在 `generate_relationship_index` 函数里增加配偶星检测：
   ```python
   # ===== C. 检查天干/地支出现配偶星 =====
   # C1. 检查天干配偶星
   liunian_gan = liunian.get("gan", "")
   if liunian_gan:
       gan_shishen = get_shishen(day_gan, liunian_gan)
       if gan_shishen:
           if is_male:
               if gan_shishen in ("正财", "偏财"):
                   year_hit = True
                   year_types.add(RELATIONSHIP_TYPE_SPOUSE_STAR_IN_GAN)
           else:
               if gan_shishen in ("正官", "七杀"):
                   year_hit = True
                   year_types.add(RELATIONSHIP_TYPE_SPOUSE_STAR_IN_GAN)

   # C2. 检查地支配偶星（重点：遇到对的人）
   liunian_zhi = liunian.get("zhi", "")
   if liunian_zhi:
       main_gan = get_branch_main_gan(liunian_zhi)
       if main_gan:
           zhi_shishen = get_shishen(day_gan, main_gan)
           if zhi_shishen:
               if is_male:
                   if zhi_shishen in ("正财", "偏财"):
                       year_hit = True
                       year_types.add(RELATIONSHIP_TYPE_SPOUSE_STAR_IN_ZHI)
               else:
                   if zhi_shishen in ("正官", "七杀"):
                       year_hit = True
                       year_types.add(RELATIONSHIP_TYPE_SPOUSE_STAR_IN_ZHI)
   ```

3. 增加 `years_by_type` 和 `last5_years_by_type` 的计算

**实现难度**：★☆☆☆☆（简单）

**预计工作量**：0.5-1天

---

#### Step 2: 实现 Q8 输出函数（priority: P1）

**文件**：`bazi/questions/q8_meet_partner.py`（新建）

**输出逻辑**：
1. 从 `index.relationship.years_by_type.spouse_star_in_zhi` 提取地支配偶星年份（未来）
2. 如果有，输出"最有可能遇到对的人的年份"
3. 从 `facts.natal.marriage_hint` 提取婚配倾向
4. 可选：输出其他感情信号年份（天干配偶星、合、冲）

**实现难度**：★★☆☆☆（中等）

**预计工作量**：1-2天

---

#### Step 3: 增强 Q4 输出函数（priority: P1）

**文件**：`bazi/questions/q4_past_relationship.py`（新建）

**输出逻辑**：
1. 从 `index.relationship.last5_years_by_type` 提取近5年按类型分组的年份
2. 对每个命中年份，提取该年的所有感情 hints：
   - `"提示：缘分（天干）：暧昧推进"`
   - `"提示：缘分（地支）：易遇合适伴侣（良缘）"`
   - `"婚恋变化提醒（如恋爱）：..."`
   - 冲到婚姻宫的 hints
3. 从 `facts.natal.marriage_hint` 提取婚配倾向（2026-01-30 新增）
4. 从 `facts.natal.marriage_structure` 提取婚恋结构

**实现难度**：★★☆☆☆（中等）

**预计工作量**：1-2天

---

## 四、财星六亲助力"父亲/爸爸"输出规则（✅ 已实现 2026-01-31）

### 4.1 规则说明

**默认不输出父亲**。只有满足以下**全部条件**时才输出：

1. 财星是用神
2. 天干有财星透出（年/月/时柱天干有正财或偏财）
3. 年月天干都不是比劫（年OR月有比劫就不输出）

### 4.2 代码位置

- **判断函数**：`bazi/cli.py` → `_should_output_father_in_cai()`
- **打印函数**：`bazi/cli.py` → `_get_liuqin_source()` 增加 `should_output_father` 参数

### 4.3 Regression 测试

**测试文件**：`tests/regression/test_father_in_liuqin.py`

| 案例 | 预期 | 原因 |
|------|------|------|
| 2005-9-17 12:00女 | ❌不输出 | 年月柱天干有比劫 |
| 1965-10-4 6:00男 | ✅输出 | 财星是用神 + 天干透财星 + 年月无比劫 |
| 2005-2-5 12:00女 | ✅输出 | 天干透了财星，时柱劫财不算 |
| 2006-3-28 12:00女 | ❌不输出 | 年月有比劫 |
| 2003-11-28 2:00男 | ❌不输出 | 财星没有透 |

**状态**：✅ 已实现

---

## 五、总结

### 5.1 关键发现

1. ✅ **配偶星检测已经在程序里了**：
   - 天干配偶星：`"提示：缘分（天干）：暧昧推进"`
   - 地支配偶星：`"提示：缘分（地支）：易遇合适伴侣（良缘）"`
   - 这些都在 `liunian.hints` 里

2. ✅ **Relationship Index 需要增强**：
   - 当前只检测冲和争合
   - 需要增加配偶星检测
   - 需要按类型分组年份

3. ✅ **Q8 和 Q4 的区别**：
   - Q8：侧重地支配偶星（良缘）+ 婚配倾向 + 合（可谈恋爱）
   - Q4：过去5年所有感情相关的 hints + 婚配倾向 + 婚恋结构

### 5.2 实施优先级

**立即实施**：
1. 财星六亲助力修改（10分钟）

**P0 级别**：
1. Relationship Index 增强（0.5-1天）

**P1 级别**：
1. Q8: 什么时候遇到对的人（1-2天）
2. Q4: 过去/当前感情状况（1-2天）

**总计**：2.5-5天

---

## 六、已确认的设计决策

1. ✅ **Q8 输出内容**（2026-01-30 确认）：
   - 输出：合 + 配偶星（天干和地支）
   - 不输出：冲（冲一般不能谈成）
   - 强调：地支配偶星 = 遇到对的人，可以结婚
   - 说明：合 = 能谈恋爱
   - 包含：婚配倾向

2. ✅ **Q4 输出内容**（2026-01-30 确认）：
   - 输出：近5年所有感情相关的 hints
   - 包含：婚配倾向
   - 包含：婚恋结构

3. ✅ **不需要新增"谈恋爱"问题**：
   - Q8 和 Q4 都会区分"谈恋爱"和"遇到对的人"
   - Q8 通过说明"合=能谈恋爱，地支配偶星=对的人"来区分
   - Q4 通过展示所有感情 hints 来涵盖所有情况

---

## 七、下一步行动（2026-01-31更新）

1. ✅ 用户确认方案
2. ✅ 财星六亲助力修改（已完成 2026-01-31）
3. ✅ 增强 Relationship Index（已完成 2026-01-31）
   - ✅ `spouse_star_in_gan`（天干配偶星=能谈恋爱）
   - ✅ `spouse_star_in_zhi`（地支配偶星=遇到对的人）
   - ✅ `zhi_liuhe_combine`（地支六合=能谈恋爱）
   - ✅ `zhi_banhe_combine`（地支半合=能谈恋爱）
   - ✅ `years_by_type` 和 `last5_years_by_type` 字段
4. 🔜 实现 Q8 和 Q4（Index层已就绪）
