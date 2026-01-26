# System Architecture Specification

> **Scope**: This document defines system contracts (router/index/context_trace/blocks).  
> **Business rules**: See `bazi/BAZI_RULES.md`.

---

## 1. Single Source of Truth

| Term | Definition |
|------|------------|
| **facts** | The ONLY truth source = print-layer/render-layer output as readable text blocks. LLM and frontend consume only these blocks. |
| **index** | Navigation/routing metadata. NOT a facts replacement. Used only for "decide" phase (which modules/blocks to select). |
| **context_trace** | The ONLY authoritative trace of "what LLM actually consumed". Frontend Debug Drawer reads ONLY this. |

### Prohibitions
- ❌ No "evidence" terminology anywhere (variables, fields, UI text, comments)
- ❌ Index must never be fed to LLM as "facts content"
- ❌ No second facts source (facts.json / snapshots / exports)

---

## 2. Data Flow

```
User Query
    ↓
Router (intent recognition)
    ↓
Select Blocks (from facts + index routing)
    ↓
Build LLM Context (only facts blocks as content)
    ↓
LLM Answer
    ↓
Response { llm_answer, context_trace, index }
```

### Layer Responsibilities

| Layer | Does | Does NOT |
|-------|------|----------|
| **Router** | Recognize intent, select blocks/modules | Generate facts content |
| **Index** | Provide routing metadata (years, flags, hits) | Replace facts as content source |
| **Facts Blocks** | Provide readable text for LLM | Contain raw engine JSON |
| **context_trace** | Record which blocks LLM consumed | Drive business logic |

---

## 3. Router Specification

### Intent List

| Intent | Description | Required Blocks (minimum) |
|--------|-------------|---------------------------|
| `personality` | User asks about personality/traits | `INDEX_PERSONALITY`, `PERSONALITY_FACTS_BLOCK` |
| `year_detail` | User asks about specific year | `DAYUN_BRIEF`, `YEAR_DETAIL_TEXT` |
| `last5` | User asks about recent 5 years | `FACTS_LAST5_COMPACT_BLOCK`, plus `YEAR_DETAIL_TEXT` for each risky year |
| `glossary` | User asks terminology explanation | `GLOSSARY_BLOCK` (if implemented) |
| `overall` | General fortune overview | `FACTS_LAST5_COMPACT_BLOCK` + `DAYUN_BRIEF` |

### Child Router Trigger Rules

| Parent Intent | Trigger Condition | Child Action |
|---------------|-------------------|--------------|
| `last5` | Year has `total_risk >= 25` OR `year_category in {凶, 有变动}` | Append `YEAR_DETAIL_TEXT(YYYY)` for that year |

---

## 4. Index Specification

### Required Index Blocks

| Block ID | Purpose | Key Fields (contract) |
|----------|---------|----------------------|
| `INDEX_NATAL_BAZI` | Four pillars + positions | `year/month/day/hour` objects with `gan`, `zhi` |
| `INDEX_YONGSHEN` | Yongshen candidates/mapping | `yongshen_elements[]`, `yongshen_explain` |
| `INDEX_PERSONALITY` | Personality traits summary | `dominant_traits[]`, `xiongshen_status` |
| `INDEX_LAST5` | Last5 years window + labels | `last5[]` array with `year`, `year_label`, `risk_from_gan`, `risk_from_zhi` |
| `INDEX_DAYUN` | Current dayun reference | `current_dayun_ref`, `fortune_label` |
| `INDEX_TURNING_POINTS` | Nearby turning points | `nearby[]`, `should_mention` |
| `INDEX_RELATIONSHIP` | Relationship windows | `hit`, `years_hit[]`, `last5_years_hit[]` |

### Field Stability

- **Contract fields** (above): Must exist, type stable
- **Extensible fields**: Additional fields may be added without breaking

---

## 5. context_trace Contract

### Structure

```typescript
interface ContextTrace {
  router: {
    router_id: string
    intent: string
    mode: 'year' | 'range' | 'general'
    reason: string
    child_router?: RouterMeta | null  // 下钻时会有
  }
  used_blocks: ContextBlock[]
  context_order: string[]
  facts_selection: {
    selected_facts_paths: string[]
    selected_fact_ids: string[]
  }
  index_usage: {
    index_hits: string[]
    used_index_block_ids: string[]
  }
  run_meta: {
    timing_ms: { router, engine, llm }
    llm_input_preview?: string
  }
  context?: LLMContextFull  // 完整 LLM 上下文（见下）
}

interface ContextBlock {
  kind: 'facts' | 'index' | 'other'
  block_type: string
  block_id: string
  used: boolean
  source: 'engine' | 'index' | 'stub'
  chars_total: number           // Character count (汉字/punct/newline all count as 1)
  preview: string               // First 600 chars
  full_text?: string            // Full content (current: inline, not lazy-loaded)
  year?: number
  reason?: string
}
```

### 5.1 LLM Context Full（完整 LLM 输入追踪）

用于 Debug 模式，一眼定位"某个 block 是否真的进了 LLM 输入"。

```typescript
interface LLMContextFull {
  full_text: string              // 完整 LLM 输入（只在 debug_context=true 时返回）
  full_text_preview?: string     // 前后各 3k chars（默认返回）
  full_text_sha256?: string      // 用于验证一致性
  parts: ContextPart[]           // 每一段的来源追踪
  token_est: number              // 估算 token（chars/2.5）
  was_truncated: boolean         // 是否被截断
  drilldown_summary?: {          // last5 下钻诊断
    risky_years_detected: number[]
    year_detail_blocks_added: string[]
    drilldown_triggered: boolean
  }
}

interface ContextPart {
  part_id: number
  role: 'system' | 'developer' | 'user' | 'facts' | 'separator' | 'instruction'
  block_id?: string
  block_type?: string
  year?: number
  reason?: string
  start_char: number
  end_char: number
  chars_total: number
  preview: string
}
```

### 5.2 Debug 开关

| 参数 | 方式 | 效果 |
|------|------|------|
| `debug_context=true` | Query param 或 Header `X-Debug-Context: 1` | 返回完整 `full_text` |
| `dry_run=true` | Query param | 不调用 LLM，只返回 context_trace + `_debug` 诊断信息 |

### 5.3 full_text 分隔符格式

```
--- SYSTEM ---
{system_prompt}

--- USER ---
{user_query}

--- FACTS block_id=xxx block_type=YYY year=ZZZZ reason=RRR ---
{facts_content}
```

### Preview Rules

- `preview` length unit: **chars** (string character count)
- Default `PREVIEW_MAX_CHARS = 600`
- `full_text`: 默认不返回（节省带宽），`debug_context=true` 时返回

### Deprecated Fields

- `facts_trace`: Deprecated. Frontend must NOT read/render.
- Any field containing "evidence": Deleted.

---

## 6. UI/Debug Minimum Acceptance

### Default State
- Main chat UI: Clean (like ChatGPT)
- Debug Drawer: **Closed by default**

### Debug Drawer Tabs (4 tabs)

| Tab | Data Source | Content |
|-----|-------------|---------|
| **LLM Input** ⭐ | `context_trace.context` | `full_text` 完整 LLM 输入、`parts[]` 段落分解、`drilldown_summary` 下钻诊断、`token_est`、`was_truncated` |
| **Router** | `context_trace.router` | `router_id`, `intent`, `mode`, `reason`; `used_blocks` grouped by `kind` |
| **Facts** | `context_trace.used_blocks` where `kind='facts'` | Each block: `block_type`, `chars_total`, `preview`, expandable `full_text` |
| **Index** | `context_trace.used_blocks` where `kind='index'` + full `index` object | Used blocks + collapsible "Full Index (raw)" |

> **LLM Input tab** 是调试核心：一眼看清 LLM 到底吃了什么。默认打开此 tab。

### Prohibitions
- ❌ No "Evidence" tab
- ❌ No raw engine JSON in Facts tab default view
- ❌ No "payload" label (use "Full Index" instead)

---

## 7. Regression / Acceptance Checklist

### 7.1 Fixed Test Queries (使用 `dry_run=true` 测试)

| # | Query | Expected Blocks | Expected in `full_text` | Fail Condition |
|---|-------|-----------------|-------------------------|----------------|
| 1 | "我的性格特点" | `PERSONALITY_FACTS_BLOCK` (if exists) | - | Missing `INDEX_PERSONALITY` in `index_usage` |
| 2 | "最近5年怎么样" | `FACTS_LAST5_COMPACT_BLOCK` + `YEAR_DETAIL_TEXT` for risky years | `【具体表现与提示】` | `drilldown_summary.drilldown_triggered=true` 但 `year_detail_blocks_added` 为空 |
| 3 | "2025年运势" | `DAYUN_BRIEF`, `YEAR_DETAIL_TEXT` | `【为什么会这样？】` | Missing year_detail 4 sections |
| 4 | "今年运势" | Same as year_detail for current year | Same | Missing half-year risk explanation |
| 5 | "什么是用神" | `GLOSSARY_BLOCK` or fallback | - | (optional, may fallback) |
| 6 | "感情方面最近怎么样" | `FACTS_LAST5_COMPACT_BLOCK` or `RELATIONSHIP_FACTS_BLOCK` | - | - |

### 7.2 last5 下钻诊断（关键）

使用 `dry_run=true&debug_context=true` 测试 last5 请求：

```bash
# 检查 _debug 字段
curl -X POST "http://localhost:3000/api/test-chat?dry_run=true&debug_context=true" \
  -H "Content-Type: application/json" \
  -d '{"message":"最近5年怎么样","birth_date":"1985-03-10","birth_time":"14:00","is_male":true}'
```

**必须满足：**
- `_debug.contains_year_detail_text = true`（如果有 risky year）
- `_debug.contains_具体表现与提示 = true`（如果有 drilldown）
- `context_trace.context.drilldown_summary.year_detail_blocks_added` 与 `risky_years_detected` 匹配

**如果 `full_text` 包含 YEAR_DETAIL_TEXT 但 LLM 答案没复述**：
→ 问题在 LLM 写作规则，而非选块/拼接

### 7.3 Invariants (Always True)

- [ ] `context_trace.used_blocks` is non-empty for any successful response
- [ ] All `kind='facts'` blocks have `chars_total > 0`
- [ ] `preview` length ≤ 600 chars
- [ ] No block contains raw JSON as preview/full_text
- [ ] No "evidence" terminology in response fields
- [ ] last5 years are `[base_year-4 .. base_year]` in ascending order
- [ ] Risk percentages in range `[0, 100]`
- [ ] Risky years (`total_risk >= 25`) have `YEAR_DETAIL_TEXT` appended
- [ ] `context_trace.context.was_truncated = false`（开发期）

---

## 8. Personality Talent Cards (性格天赋卡)

### 8.1 Design Overview

Talent Cards are detailed personality descriptions for each of the 5 Shishen categories. They are printed **only in the "主要性格" (Major Personality) section**, never in "其他性格" (Other Personality).

### 8.2 Card Structure

Each talent card consists of:
1. **共性行** (Common trait): 1 line applicable to all tiers
2. **主卡** (Main card): 5 lines × 5 aspects (思维/社交/兴趣/生活/提高)
3. **补充句** (Supplement): Optional 1 line when one side dominates

### 8.3 5-Tier Selection (pian_ratio threshold)

```
pian_ratio = 偏% / (正% + 偏%)
```

| Tier | Condition | Output |
|------|-----------|--------|
| 纯正 | 偏%=0 | 共性 + 正主卡 |
| 纯偏 | 正%=0 | 共性 + 偏主卡 |
| 正主导 | pian_ratio ≤ 0.30 | 共性 + 正主卡 + 偏补充 |
| 各半 | 0.30 < pian_ratio ≤ 0.60 | 共性 + 融合版 |
| 偏主导 | pian_ratio > 0.60 | 共性 + 偏主卡 + 正补充 |

### 8.4 Implementation Status

| Category | Status | File |
|----------|--------|------|
| 印星 (Yin Xing) | ✅ Done | `bazi/cli.py` |
| 财星 (Cai Xing) | ✅ Done | `bazi/cli.py` |
| 比劫 (Bi Jie) | ✅ Done | `bazi/cli.py` |
| 官杀 (Guan Sha) | ✅ Done | `bazi/cli.py` |
| 食伤 (Shi Shang) | ✅ Done | `bazi/cli.py` |

> **详细规则**: See `bazi/BAZI_RULES.md` §13

---

## 9. 性格快速汇总 (Personality Quick Summary)

### 9.1 Overview

The "性格快速汇总" section is printed immediately after "其他性格" section, providing a condensed summary of the user's main personality traits.

### 9.2 Structure

1. **总览** (Overview): Lists all major personality traits in fixed order: 财 → 印 → 食伤 → 比劫 → 官杀
2. **思维天赋** (Mind): One-liner for 财星 and 印星 only
3. **社交天赋** (Social): One-liner for 财星 and 印星 only
4. **备注** (Notes): Lists other traits not yet summarized (食伤/比劫/官杀)

### 9.3 Naming Convention

| Group | Pure 正 | Pure 偏 | Mixed |
|-------|---------|---------|-------|
| 财 | 正财 | 偏财 | 正偏财 |
| 印 | 正印 | 偏印 | 正偏印 |
| 食伤 | 食神 | 伤官 | 食神伤官 |
| 比劫 | 比肩 | 劫财 | 比肩劫财 |
| 官杀 | 正官 | 七杀 | 正官七杀 |

### 9.4 Implementation

- Function: `build_personality_quick_summary()` in `bazi/cli.py`
- Constants: `QUICK_SUMMARY_MIND`, `QUICK_SUMMARY_SOCIAL` in `bazi/cli.py`

---

## Version History

| Date | Change |
|------|--------|
| 2026-01-25 | Year detail report rendering complete; fixed hour TKDC/clash hints; about to build payload |
| 2026-01-18 | Add §9 性格快速汇总; complete 食伤天赋卡; remove 财星关系倾向句 |
| 2026-01-18 | Add §8 Personality Talent Cards (印星/财星/比劫/官杀 completed, 食伤 pending) |
| 2026-01-13 | Add LLM Input tab to Debug Drawer; full_text 默认返回（开发期） |
| 2026-01-13 | Initial creation: router/index/context_trace contracts, blocks, regression |

