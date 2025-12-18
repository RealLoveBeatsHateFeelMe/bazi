## 回归用例总览（Golden Cases）

本文件用于**人工可读地记录所有“黄金回归用例”**，与 `bazi/regress.py` 中的断言保持一致。  
约定：**回归脚本是机器真相，本文档是人读说明**——当回归期望值调整时，必须同步更新此文档。

---

## 目录

- A 盘（3 条）
  - A-1
  - A-2
  - A-3
- B 盘（2 条）
  - B-1
  - B-2
- 现有规则级回归（辰未不刑）
- 如何验证与人工核对步骤

---

## A 盘

> 说明：当前代码仓库中的 `bazi/regress.py` 尚未包含 A 盘 / B 盘的完整实现（`run_case_A` / `run_case_B` 等），  
> 仅保留了“辰未不刑”的规则回归。因此本节先占位结构，待黄金用例回归脚本落地后再补齐**具体输入与期望值**。

### Case A-1

- **Case 名**：A-1  
- **输入**：生日 / 时间 / 性别（待补充，对应 `run_case_A` 中的第 1 条）  
- **对应年份**：待补充  
- **期望**：  
  - `core_total`：待补充  
  - `total_risk_percent`：待补充（若与 `core_total` 一致，注明为“与 core_total 相同”；若因线运 / 加成不同，则写明差异来源）  
- **关键事件拆分（基于 ledger 字段名）**：  
  - `branch_clash`：基础冲、墓库加成、TKDC 加成等  
  - `punishment`：刑事件的 `risk_percent` 与 `targets`  
  - `pattern` / `pattern_static_activation`：十神模式与静态激活  
  - `dayun_liunian_branch_clash`：运年相冲  
  - `tkdc_static_activation`：静态 TKDC 额外档位  
- **如何验证**：  
  - 跑回归：`python -m bazi.regress`，确认对应 A-1 断言通过；  
  - 人工核对：`python main.py --debug-ledger --dump-year-json YEAR`，  
    - 在 `YEAR` 对应的 `liunian_dict` 中查看：`total_risk_percent`、`ledger.sum_*`、以及 `ledger.events`；  
    - 对照上面列出的关键事件拆分，确认各事件的 `risk_percent` 与 `breakdown` 一致。

### Case A-2

> 结构同 A-1，待 `bazi/regress.py` 中对应用例实现后补充：  
> - 输入（生日 / 时间 / 性别）  
> - 对应年份  
> - `core_total` / `total_risk_percent` 期望值  
> - 关键事件（冲 / 刑 / 模式 / 运年相冲 / TKDC / 静态激活）  

### Case A-3

> 结构同 A-1，待 `bazi/regress.py` 中对应用例实现后补充。

---

## B 盘

### Case B-1

> 结构同 A-1，待 `bazi/regress.py` 中对应用例实现后补充。

### Case B-2

> 结构同 A-1，待 `bazi/regress.py` 中对应用例实现后补充。

---

## 现有规则级回归：辰未不刑

虽然 A/B 盘的黄金回归尚未在当前代码中落地，但已经存在一条**关键规则级回归**：  
“辰未不刑”（防止误把辰未当成刑）。

### Case R-1：表级规则——辰未不刑

- **Case 名**：R-1（规则级）  
- **对应代码**：`bazi/punishment.py` 与 `bazi/regress.py`  
- **期望**：
  - 组合层面：
    - `("辰", "未")` 和 `("未", "辰")` **不在** `ALL_PUNISH_PAIRS` 中；
    - `("辰", "未")` 和 `("未", "辰")` **不在** `GRAVE_PUNISH_PAIRS` 中。
  - 运行层面：
    - 对任意包含“未”的命盘，当 `flow_branch="辰"` 调用 `detect_branch_punishments(...)` 时，  
      返回的所有事件中 **不应出现** `target_branch="未"`。

- **关键字段 / ledger 对应**：
  - 规则层：
    - `ALL_PUNISH_PAIRS`  
    - `GRAVE_PUNISH_PAIRS`
  - 运行层：
    - 事件结构：`{"type": "punishment", "flow_branch", "target_branch", "risk_percent", ...}`  
    - 其中只要 `flow_branch == "辰"`，则 `target_branch != "未"` 必须成立。

- **如何验证**：
  - 跑回归：  
    - `python -m bazi.regress`  
    - 期待输出包含：  
      - `[PASS] 辰未不刑断言通过`  
      - `[PASS] 辰不刑未的运行时断言通过`  
      - `ALL REGRESSION TESTS PASS`
  - 人工检查（如需）：  
    - 在 REPL 或临时脚本中构造包含“未”的测试八字，调用：  
      - `detect_branch_punishments(bazi, flow_branch="辰", flow_type="test")`  
    - 确认返回列表中所有事件的 `target_branch` 字段均不为 `"未"`。

---

## 如何验证与人工核对步骤（通用）

1. **自动回归**  
   - 在仓库根目录执行：  
     - `python -m bazi.regress`  
   - 期望：所有断言通过，最终打印 `"ALL REGRESSION TESTS PASS"`。

2. **交互式 / JSON 调试（设计预期）**  
   - 待 CLI 完整支持后，可通过：  
     - `python main.py --debug-ledger --dump-year-json YEAR`  
   - 其中：  
     - `--debug-ledger`：打印该年的 `sum_gan`, `sum_zhi`, `sum_total_pre_cap`, `total_after_cap` 以及所有 `ledger.events`；  
     - `--dump-year-json YEAR`：将 `YEAR` 对应的 `liunian_dict` 完整输出为 JSON，便于对 `total_risk_percent`、  
       `core_total`、`patterns`、`punishments`、`tkdc_static_activation` 等字段做精细比对。

> 提示：当未来在 `bazi/regress.py` 中补充 / 修改 A-1 ~ B-2 等黄金回归用例时，  
> 请务必同步更新本文件中的“输入 / 年份 / core_total / total_risk_percent / 关键事件拆分”描述。


