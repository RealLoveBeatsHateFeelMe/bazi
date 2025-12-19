## 0. 总览（bazi/ 各文件职责）

- `bazi/lunar_engine.py`：封装对 `lunar_python` 的调用，负责从公历生日推导出农历、八字四柱、日主五行等基础信息。核心输出结构是 `analyze_basic(birth_dt)` 返回的 `dict`，其中包含 `bazi`（年/月/日/时四柱）、`day_master_element`、`yongshen_elements` 等。
- `bazi/strength.py`：根据全局五行分布和位置权重，计算日主强弱、原始得分、支持/消耗比例等。主要被 `lunar_engine.analyze_basic` 调用，输出字段如 `strength_score_raw`、`strength_percent` 等。
- `bazi/yongshen.py`：根据日主五行和强弱，推导用神五行列表。供 `analyze_basic` 使用，输出 `yongshen_elements: List[str]`。
- `bazi/shishen.py`：十神相关工具函数。包含：
  - `get_shishen(day_gan, other_gan)`：返回某天干相对日干的十神。
  - `get_branch_shishen(bazi, branch)`：返回某地支（按主气）对应的十神（`{"gan": ..., "shishen": ...}`），用于冲/刑/模式中标注“流年/命局十神”。
- `bazi/config.py`：全局配置与常量：
  - 位置权重 `POSITION_WEIGHTS`；
  - 天干/地支五行 `GAN_WUXING`, `ZHI_WUXING`；
  - 克制关系 `KE_MAP`；
  - 冲/刑/模式/TKDC 风险系数，例如 `CLASH_NORMAL_RISK`, `PATTERN_GAN_RISK_LIUNIAN`, `TIAN_KE_DI_CHONG_EXTRA_RISK` 等；
  - 宫位映射 `PILLAR_PALACE`, `PILLAR_PALACE_CN`。
- `bazi/clash.py`：所有“地支冲 + 天克地冲”逻辑：
  - 检测流年/大运地支是否冲命局；
  - 计算冲的基础力量 `base_power_percent`；
  - 计算墓库冲加成 `grave_bonus_percent`；
  - 检测并叠加天克地冲 TKDC；
  - 返回标准化的 `branch_clash` 事件结构。
- `bazi/punishment.py`：所有“地支刑”逻辑：
  - 检测流年/大运刑命局；
  - 区分普通刑与墓库刑；
  - 使用固定风险值（普通 5.0 / 墓库 6.0，不按命中柱位数倍增）；
  - 检测命局内部静态刑与大运-命局之间的刑。
- `bazi/patterns.py`：十神模式检测（伤官见官、枭神夺食），**目前为占位实现（TODO）**：
  - 未来将收集所有位置的十神信息；
  - 构造天干/地支层的配对；
  - 区分命局/大运/流年层；
  - 对流年触发的模式计算风险，并生成 `pattern` 事件。
- `bazi/luck.py`：大运 / 流年运势与年度风险主引擎：
  - 从 `analyze_basic` 的 `bazi` 和用神出发；
  - 生成大运列表和每步大运下的十年流年；
  - 实现：用神标记 + 冲信息（命局冲 & 运年相冲）+ 线运加成（命中 active_pillar 的 base 事件 risk>=10 触发，全年一次+6%）+ 六合/三合/半合/三会检测。
  - 尚未实现：模式/静态激活等完整风险账本逻辑（预留扩展位）。
- `bazi/harmony.py`：六合/三合/半合/三会检测：
  - `detect_natal_harmonies(bazi)`：检测命局内部的六合、三合、半合、三会
  - `detect_flow_harmonies(bazi, flow_branch, ...)`：检测流年/大运与原局形成的六合、三合、半合、三会
  - 只解释，不计分（`risk_percent = 0`，不进入线运扫描，不影响 `total_risk_percent`）
  - 统一事件类型：`type="branch_harmony"`，`subtype="liuhe"|"sanhe"|"banhe"|"sanhui"`
  - 必须包含 `targets` 字段，每个命中柱位都要列出 `pillar` 和 `palace`（中文宫位名）
- `bazi/cli.py`：命令行交互入口：
  - 读入生日与性别；
  - 调用 `analyze_basic` 和 `analyze_luck`；
  - 以树状结构打印大运/流年 + 冲信息；
  - 未来可扩展 `--debug-ledger`, `--dump-year-json` 等调试参数（当前尚未实现完整账本逻辑）。
- `bazi/regress.py`：回归测试入口：
  - 使用固定出生信息与期望结果，调用 `analyze_basic`；
  - 目前覆盖：刑规则回归 + traits T1/T2；
  - 尚未覆盖用神 special_rules、线运、模式等高级特性（预留扩展位）。
- `bazi/__init__.py`：包初始化（当前只做最小导出或占位）。
- `main.py`：项目入口，简单调用 `from bazi.cli import run_cli; run_cli()`。

主调用链概览：

- 交互模式：`python main.py`
  - `main.py` → `cli.run_cli()` →
    - `lunar_engine.analyze_basic(birth_dt)`（生成 `bazi`、用神、日主强弱等）；
    - `luck.analyze_luck(birth_dt, is_male, yongshen_elements)`（生成大运/流年基本结构和冲事件）。
- 回归模式：`python -m bazi.regress`
  - `bazi.regress.main()` →
    - `analyze_basic` →
    - 对刑规则和 traits 结果做断言；
    - 任一断言失败即 `sys.exit(1)`。

---

## 1. 年度风险计算主流程（Year pipeline）

### 1.1 生成大运 / 流年列表

- 文件：`bazi/luck.py`
- 函数：`analyze_luck(birth_dt: datetime, is_male: bool, yongshen_elements: List[str], max_dayun: int = 8) -> Dict[str, Any]`
  - 关键步骤：
    - 使用 `lunar_python.Solar` 生成农历与 `EightChar`：`solar.getLunar().getEightChar()`。
    - 构造命盘 `bazi`：
      - `year/month/day/hour` 各自有 `{"gan": ..., "zhi": ...}`。
    - 调用 `ec.getYun(1 if is_male else 0)` 获取大运起运信息与各步大运 `DaYun` 对象。
      - 对每步大运构造 `DayunLuck` dataclass → `dayun_dict`。
    - 对每步大运下的十个流年：
      - 生成 `liunian_list`，每个元素包含年份、虚龄、干支、用神标记、冲事件、线运加成、六合/三合等字段。
    - 返回结构：`{"groups": [{"dayun": dayun_dict, "liunian": liunian_list}, ...]}`。

### 1.2 线运加成计算

- 文件：`bazi/luck.py`
- 函数：`_compute_lineyun_bonus(age: int, base_events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]`
  - 规则：
    1. 根据虚龄 `age` 确定 `active_pillar`（`_get_active_pillar`）：
       - 0-16 岁 → `"year"`
       - 17-32 岁 → `"month"`
       - 33-48 岁 → `"day"`
       - 49+ 岁 → `"hour"`
    2. 扫描所有 `role="base"` 的事件（例如 `branch_clash`）
    3. 判定触发：存在至少一条 base 事件满足：
       - 该事件命中 `active_pillar`（`targets` 中有 `pillar == active_pillar`）
       - 且该事件的 `risk_percent >= 10.0`
    4. 一旦触发，立即返回线运事件（全年只加一次）：
       - `type: "lineyun_bonus"`
       - `role: "lineyun"`
       - `risk_percent: 6.0`
       - `active_pillar: "year"/"month"/"day"/"hour"`
       - `trigger_events: [<触发来源事件的简化引用>]`
    5. 否则返回 `None`（不触发）
  - **全年最多只加一次 6%，不叠加、不分干支**

### 1.3 年度总风险计算

- 在 `analyze_luck` 的流年循环中：
  - `other_effect = sum(所有 role != "punisher" 事件的 risk_percent)`
  - `lineyun_bonus = lineyun_event.get("risk_percent", 0.0) if lineyun_event else 0.0`
  - `total_risk_percent = other_effect + lineyun_bonus`（**不封顶，可>100**）
  - 写入 `liunian_dict["total_risk_percent"]` 和 `liunian_dict["lineyun_bonus"]`
  - **注意**：年度总风险不封顶，只对单事件风险按各自规则封顶（例如冲事件自身封顶100）

### 1.4 六合/三合/半合/三会检测

- 文件：`bazi/harmony.py`
- 函数：
  - `detect_natal_harmonies(bazi)`：检测命局内部的六合、三合、半合、三会，返回事件列表
  - `detect_flow_harmonies(bazi, flow_branch, ...)`：检测流年/大运与原局形成的六合、三合、半合、三会
- **规则**：只解释，不计分（`risk_percent = 0`，不进入线运扫描，不影响 `total_risk_percent`）
- **事件结构**：
  - `type: "branch_harmony"`
  - `subtype: "liuhe" | "sanhe" | "banhe" | "sanhui"`
  - `role: "explain"`
  - `targets[]`：每个命中柱位必须包含 `pillar`、`palace`（中文宫位名）、`target_branch`
- 在 `analyze_basic` 中调用 `detect_natal_harmonies`，输出到 `natal_harmonies: []`
- 在 `analyze_luck` 中调用 `detect_flow_harmonies`，输出到：
  - 流年的 `harmonies_natal: []`（流年与原局的合类）
  - 大运的 `harmonies_natal: []`（大运与原局的合类）
- **半合判定补充规则（重要）**：
  - 三合四局：
    - 水局：申子辰
    - 火局：寅午戌
    - 木局：亥卯未
    - 金局：巳酉丑
  - 半合必须包含三合局的“中间那一支”，只认三合局中的前两支或后两支：
    - 申子辰：只认「申子半合」「子辰半合」，不认「申辰」；
    - 寅午戌：只认「寅午半合」「午戌半合」，不认「寅戌」；
    - 亥卯未：只认「亥卯半合」「卯未半合」，不认「亥未」；
    - 巳酉丑：只认「巳酉半合」「酉丑半合」，不认「巳丑」。
  - `matched_branches` 中记录本次实际参与半合的两支（例如 `["巳","酉"]`），`members` 中记录完整三合局三支（例如 `["巳","酉","丑"]`）。

---

> **注意**：关于“模式 / 静态激活 / ledger 账本”的完整实现，属于与 `BAZI_RULES.md` 对齐的**目标设计**，当前版本尚未完全实现。实现时应以 `BAZI_RULES.md` 为最终口径。
