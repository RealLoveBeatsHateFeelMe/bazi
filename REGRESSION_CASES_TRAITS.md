## Traits 回归用例（dominant_traits）

本文件记录与 `dominant_traits`（主要性格）相关的黄金回归用例，  
对应实现位于：`bazi/traits.py` 与 `bazi/lunar_engine.analyze_basic`，  
回归入口位于：`bazi/regress.py` 中的 `test_traits_T1` / `test_traits_T2`。

---

## 目录

- T-1：2005-09-20 10:00 男  
- T-2：2007-01-28 12:00 男  

---

## T-1：2005-09-20 10:00 男

- **输入**：
  - 公历生日：`2005-09-20`
  - 时间：`10:00`
  - 性别：男（`is_male=True`）
- **只看原局**：大运 / 流年不参与 traits 计算。

### 期望（dominant_traits 摘要）

- **印星（印）**
  - `total_percent = 20`  
  - 子类：
    - `偏印 = 20`
    - `正印 = 0`
  - `mix_label = "纯偏印"`
  - `偏印.stems_visible_count = 2`（三天干中偏印透出两次）

- **财星（财）**
  - `total_percent = 45`
  - 子类：
    - `偏财 = 45`
    - `正财 = 0`
  - `mix_label = "纯偏财"`

### 断言位置

- 文件：`bazi/regress.py`
- 函数：`test_traits_T1()`
- 断言内容：
  - 从 `analyze_basic(datetime(2005, 9, 20, 10, 0))["dominant_traits"]` 中读取（按 group / name 查找）：
    - `"印"` 这一组：
      - `total_percent ≈ 30`
      - `detail["偏印"].percent ≈ 30`
      - `detail["正印"].percent ≈ 0`
      - `detail["偏印"].stems_visible_count == 3`
      - `mix_label == "纯偏印"`
    - `"财"` 这一组：
      - `total_percent ≈ 45`
      - `detail["偏财"].percent ≈ 45`
      - `detail["正财"].percent ≈ 0`
      - `mix_label == "纯偏财"`

---

## T-2：2007-01-28 12:00 男

- **输入**：
  - 公历生日：`2007-01-28`
  - 时间：`12:00`
  - 性别：男（`is_male=True`）
- **只看原局**：大运 / 流年不参与 traits 计算。

### 期望（dominant_traits 摘要）

- **财星（财）**
  - `total_percent = 35`
  - 子类：
    - `偏财 = 20`（来自天干两个透出）
    - `正财 = 15`（来自地支本气）
  - `mix_label = "正偏财混杂"`
  - `偏财.stems_visible_count = 2`

- **官杀**
  - 子类：
    - `正官 = 35`
    - `七杀 = 20`
  - `total_percent = 55`
  - `mix_label = "官杀混杂"`

### 断言位置

- 文件：`bazi/regress.py`
- 函数：`test_traits_T2()`
- 断言内容：
  - 从 `analyze_basic(datetime(2007, 1, 28, 12, 0))["dominant_traits"]` 中读取（按 group / name 查找）：
    - `"财"` 这一组：
      - `total_percent ≈ 35`
      - `detail["偏财"].percent ≈ 20`
      - `detail["正财"].percent ≈ 15`
      - `detail["偏财"].stems_visible_count == 2`
      - `mix_label == "正偏财混杂"`
    - `"官杀"` 这一组：
      - `total_percent ≈ 55`
      - `detail["正官"].percent ≈ 35`
      - `detail["七杀"].percent ≈ 20`
      - `mix_label == "官杀混杂"`

---

## 验证方式

1. 自动回归：
   - 在仓库根目录执行：`python -m bazi.regress`
   - 输出中应包含：
     - `[PASS] traits T-1 用例通过`
     - `[PASS] traits T-2 用例通过`
     - `ALL REGRESSION TESTS PASS`

2. 人工核对 dominant_traits JSON：
   - 在本地执行（示例）：
     - `python -c "from datetime import datetime; from bazi.lunar_engine import analyze_basic; import json; print(json.dumps(analyze_basic(datetime(2005,9,20,10,0))['dominant_traits'], ensure_ascii=False, indent=2))"`
     - `python -c "from datetime import datetime; from bazi.lunar_engine import analyze_basic; import json; print(json.dumps(analyze_basic(datetime(2007,1,28,12,0))['dominant_traits'], ensure_ascii=False, indent=2))"`
   - 对照本文件描述的期望值检查各字段是否一致。


