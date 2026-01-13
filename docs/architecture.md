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
    child_router?: RouterMeta | null
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

### Preview Rules

- `preview` length unit: **chars** (string character count)
- Default `PREVIEW_MAX_CHARS = 600`
- `full_text`: Currently returned inline (not lazy-loaded)

### Deprecated Fields

- `facts_trace`: Deprecated. Frontend must NOT read/render.
- Any field containing "evidence": Deleted.

---

## 6. UI/Debug Minimum Acceptance

### Default State
- Main chat UI: Clean (like ChatGPT)
- Debug Drawer: **Closed by default**

### Debug Drawer Tabs

| Tab | Data Source | Content |
|-----|-------------|---------|
| **Router** | `context_trace.router` | `router_id`, `intent`, `mode`, `reason`; `used_blocks` grouped by `kind` |
| **Facts** | `context_trace.used_blocks` where `kind='facts'` | Each block: `block_type`, `chars_total`, `preview`, expandable `full_text` |
| **Index** | `context_trace.used_blocks` where `kind='index'` + full `index` object | Used blocks + collapsible "Full Index (raw)" |

### Prohibitions
- ❌ No "Evidence" tab
- ❌ No raw engine JSON in Facts tab default view
- ❌ No "payload" label (use "Full Index" instead)

---

## 7. Regression / Acceptance Checklist

### Fixed Test Queries

| # | Query | Expected Blocks | Expected Index Hits | Fail Condition |
|---|-------|-----------------|---------------------|----------------|
| 1 | "我的性格特点" | `PERSONALITY_FACTS_BLOCK` (if exists) | `INDEX_PERSONALITY` | Missing `INDEX_PERSONALITY` in `index_usage` |
| 2 | "最近5年怎么样" | `FACTS_LAST5_COMPACT_BLOCK` + `YEAR_DETAIL_TEXT` for risky years | `INDEX_LAST5`, `INDEX_DAYUN` | Years not 2022-2026 ascending; risk% > 100 |
| 3 | "2025年运势" | `DAYUN_BRIEF`, `YEAR_DETAIL_TEXT` | `INDEX_YEAR_GRADE` | Missing year_detail 4 sections |
| 4 | "今年运势" | Same as year_detail for current year | Same | Missing half-year risk explanation |
| 5 | "什么是用神" | `GLOSSARY_BLOCK` or fallback | - | (optional, may fallback) |
| 6 | "感情方面最近怎么样" | `FACTS_LAST5_COMPACT_BLOCK` or `RELATIONSHIP_FACTS_BLOCK` | `INDEX_RELATIONSHIP` | - |

### Invariants (Always True)

- [ ] `context_trace.used_blocks` is non-empty for any successful response
- [ ] All `kind='facts'` blocks have `chars_total > 0`
- [ ] `preview` length ≤ 600 chars
- [ ] No block contains raw JSON as preview/full_text
- [ ] No "evidence" terminology in response fields
- [ ] last5 years are `[base_year-4 .. base_year]` in ascending order
- [ ] Risk percentages in range `[0, 100]`
- [ ] Risky years (`total_risk >= 25`) have `YEAR_DETAIL_TEXT` appended

---

## Version History

| Date | Change |
|------|--------|
| 2026-01-13 | Initial creation: router/index/context_trace contracts, blocks, regression |

