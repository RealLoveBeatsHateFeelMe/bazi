import { NextRequest, NextResponse } from 'next/server'
import { route, RouterResult } from '@/lib/router'
import OpenAI from 'openai'

// OpenAI client
const OPENAI_API_KEY = process.env.OPENAI_API_KEY
const openai = OPENAI_API_KEY ? new OpenAI({ apiKey: OPENAI_API_KEY }) : null

// Python Engine URL
const PYTHON_ENGINE_URL = process.env.PYTHON_ENGINE_URL || 'http://localhost:5000'

// Facts topK 配置
const FACTS_TOP_K = 5

// ============================================================
// Types
// ============================================================

interface UsedFact {
  fact_id: string
  type: string
  scope: string
  fact_year: number | null
  year_source: string  // 年份从哪提取的
  label: string
  text_preview: string
  reason: string  // 为什么入选
}

interface SelectionStep {
  step: string
  filter: string
  before_count: number
  after_count: number
  reason: string
}

interface FactSelectionTrace {
  time_scope: { type: string; year?: number; years?: number }
  focus: string
  allowed_years: number[]
  steps: SelectionStep[]
  fallback_triggered: boolean
  fallback_reason: string
  final_count: number
}

interface FactsTraceOutput {
  used_facts: UsedFact[]
  used_count: number
  available_count: number
  source: string
  selection_trace: FactSelectionTrace
  // 诊断字段
  debug_year_histogram: Record<number, number>
  extracted_year_null_count: number
  sample_extracted_years: Array<{ fact_id: string; scope: string; extracted_year: number | null; year_source: string }>
}

// Python engine 返回的 findings.facts 结构
interface EngineFact {
  fact_id: string
  type: string
  kind: string
  scope: string
  label: string
  flow_year?: number
  year?: number
  risk_percent?: number
  [key: string]: unknown
}

// 标准化后的 fact
interface NormalizedFact extends EngineFact {
  fact_year: number | null
  year_source: string
}

// Year Detail 结构（年请求专用）
interface YearDetail {
  year: number
  half_year_grade: {
    first: '好运' | '一般' | '凶' | '变动'
    second: '好运' | '一般' | '凶' | '变动'
  }
  gan_block: {
    gan: string
    shishen: string
    yongshen_yesno: '是' | '否'
    tags: string[]
    risk_pct: number
  }
  zhi_block: {
    zhi: string
    shishen: string
    yongshen_yesno: '是' | '否'
    tags: string[]
    risk_pct: number
  }
  hint_summary_lines: string[]
  dayun_brief: {
    name: string
    start_age: number
    end_age: number
    grade: '好' | '一般'
  } | null
  raw_text: string
}

// Year Detail Trace
interface YearDetailTrace {
  year: number
  parse_status: 'success' | 'failed'
  raw_text_preview: string
  year_detail: YearDetail | null
}

// Evidence Block（证据块）
interface EvidenceBlock {
  block_id: string
  block_type: string
  source: 'engine' | 'index' | 'stub'
  scope: 'year' | 'range' | 'general'
  year?: number
  used: boolean
  reason: string
  preview: string  // 前300字符
  length_chars: number
  full_text?: string  // 可选：完整文本
}

// Evidence Trace
interface EvidenceTrace {
  used_blocks: EvidenceBlock[]
  llm_context_order: string[]
}

// Module with produced blocks
interface ModuleTrace {
  module: string
  source: string
  used: boolean
  reason?: string
  produced_blocks: string[]
}

// ============================================================
// Main Handler
// ============================================================

export async function POST(request: NextRequest) {
  const startTime = Date.now()
  const timings = { router: 0, engine: 0, llm: 0 }

  try {
    const body = await request.json()
    const { message, birth_date, birth_time, is_male } = body

    if (!message || !birth_date || !birth_time) {
      return NextResponse.json(
        { error: 'Missing required fields: message, birth_date, birth_time' },
        { status: 400 }
      )
    }

    // 运行 Router（先运行以确定 time_scope）
    const routerStart = Date.now()
    // 先用默认 dayunGrade 运行一次来获取 time_scope
    let routerResult = route(message, '一般')
    timings.router = Date.now() - routerStart

    // 判断是否是年请求
    const isYearScope = routerResult.trace.time_scope.type === 'year'
    const targetYear = isYearScope ? routerResult.trace.time_scope.year : undefined

    // 调用 Python Engine
    const engineStart = Date.now()
    let engineData: {
      index: Record<string, unknown>
      facts: Record<string, unknown>
      findings?: {
        facts?: EngineFact[]
        hints?: unknown[]
        links?: unknown[]
      }
      year_detail?: YearDetail | null
    } | null = null

    try {
      const engineResponse = await fetch(`${PYTHON_ENGINE_URL}/v1/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          birth_date,
          birth_time,
          is_male: is_male !== false,
          base_year: new Date().getFullYear(),
          target_year: targetYear,  // 年请求时传入目标年份
        }),
      })

      if (engineResponse.ok) {
        engineData = await engineResponse.json()
      } else {
        console.warn('Engine returned:', engineResponse.status)
      }
    } catch (err) {
      console.warn('Python engine not available:', err)
    }

    if (!engineData) {
      engineData = getStubEngineData(birth_date, birth_time, is_male)
    }

    timings.engine = Date.now() - engineStart

    // 用实际的 dayunGrade 重新运行 Router
    const dayunGrade = (engineData.index as { dayun?: { fortune_label?: string } })?.dayun?.fortune_label as '好运' | '一般' | '坏运' || '一般'
    routerResult = route(message, dayunGrade)

    // 提取 index slices（年请求只用 dayun 简述）
    const indexSlices: Record<string, unknown> = {}
    if (isYearScope) {
      // 年请求：只取 dayun 用于大运背景
      if ('dayun' in (engineData.index as Record<string, unknown>)) {
        indexSlices['dayun'] = (engineData.index as Record<string, unknown>)['dayun']
      }
    } else {
      for (const slice of routerResult.slices) {
        if (slice in (engineData.index as Record<string, unknown>)) {
          indexSlices[slice] = (engineData.index as Record<string, unknown>)[slice]
        }
      }
    }

    // ============================================================
    // Year Detail Trace（年请求专用）
    // ============================================================
    let yearDetailTrace: YearDetailTrace | null = null
    
    if (isYearScope && targetYear) {
      const yearDetail = engineData.year_detail
      yearDetailTrace = {
        year: targetYear,
        parse_status: yearDetail ? 'success' : 'failed',
        raw_text_preview: yearDetail?.raw_text?.slice(0, 300) || '',
        year_detail: yearDetail || null,
      }
    }

    // ============================================================
    // 提取 facts（年请求禁用 atomic facts）
    // ============================================================
    let usedFacts: UsedFact[] = []
    let selectionTrace: FactSelectionTrace
    let availableCount = 0
    let debugYearHistogram: Record<number, number> = {}
    let extractedYearNullCount = 0
    let sampleExtractedYears: Array<{ fact_id: string; scope: string; extracted_year: number | null; year_source: string }> = []

    if (isYearScope) {
      // 年请求：禁用 atomic facts，使用 YEAR_DETAIL
      const factsResult = selectFactsStrict(engineData.facts, engineData.findings, routerResult)
      availableCount = factsResult.availableCount
      debugYearHistogram = factsResult.debugYearHistogram
      extractedYearNullCount = factsResult.extractedYearNullCount
      sampleExtractedYears = factsResult.sampleExtractedYears
      
      // 不使用 facts，只记录 trace
      selectionTrace = {
        time_scope: routerResult.trace.time_scope,
        focus: routerResult.trace.focus,
        allowed_years: targetYear ? [targetYear] : [],
        steps: [{
          step: 'year_detail_mode',
          filter: 'disabled',
          before_count: availableCount,
          after_count: 0,
          reason: 'year_detail 模式禁用 atomic facts，使用 YEAR_DETAIL_BLOCK',
        }],
        fallback_triggered: false,
        fallback_reason: 'facts_policy=disabled_for_year_detail',
        final_count: 0,
      }
    } else {
      const factsResult = selectFactsStrict(
        engineData.facts,
        engineData.findings,
        routerResult,
      )
      usedFacts = factsResult.usedFacts
      selectionTrace = factsResult.selectionTrace
      availableCount = factsResult.availableCount
      debugYearHistogram = factsResult.debugYearHistogram
      extractedYearNullCount = factsResult.extractedYearNullCount
      sampleExtractedYears = factsResult.sampleExtractedYears
    }

    // 构建 debug_used_fact_ids
    const debugUsedFactIds = usedFacts.map(f => f.fact_id)

    // ============================================================
    // 构建 LLM Context
    // ============================================================
    let llmContext: string
    
    if (isYearScope && yearDetailTrace?.year_detail) {
      // 年请求专用 Context
      llmContext = buildYearDetailContext(
        message,
        yearDetailTrace.year_detail,
        indexSlices,
        birth_date,
        birth_time,
        is_male
      )
    } else {
      // 普通请求
      llmContext = buildLLMContext(
        message,
        routerResult,
        usedFacts,
        indexSlices,
        birth_date,
        birth_time,
        is_male
      )
    }

    const llmInputPreview = llmContext.slice(0, 4000)

    // 构建 modules_trace
    const modulesTrace = buildModulesTrace(
      routerResult.slices, 
      usedFacts.length > 0,
      isYearScope,
      yearDetailTrace !== null,
      targetYear
    )

    // 构建 evidence_trace
    const evidenceTrace = buildEvidenceTrace(
      isYearScope,
      targetYear,
      yearDetailTrace?.year_detail,
      yearDetailTrace?.year_detail?.dayun_brief,
      indexSlices,
      usedFacts
    )

    // 调用 LLM
    let assistantText = ''
    let llmUsedFactIds: string[] = []
    const llmStart = Date.now()

    // 选择 system prompt
    const systemPrompt = isYearScope 
      ? getYearDetailSystemPrompt(targetYear || 0)
      : getSystemPrompt(routerResult.trace.flags, debugUsedFactIds)

    if (openai) {
      try {
        const completion = await openai.chat.completions.create({
          model: 'gpt-4o-mini',
          messages: [
            {
              role: 'system',
              content: systemPrompt,
            },
            {
              role: 'user',
              content: llmContext,
            },
          ],
          temperature: 0.7,
          max_tokens: 1200,
        })

        const rawContent = completion.choices[0]?.message?.content || ''
        const parsed = parseLLMResponse(rawContent, debugUsedFactIds)
        assistantText = parsed.text
        llmUsedFactIds = parsed.usedFactIds

      } catch (llmError) {
        console.error('LLM error:', llmError)
        assistantText = isYearScope && yearDetailTrace?.year_detail
          ? generateYearDetailStubResponse(yearDetailTrace.year_detail)
          : generateStubResponse(routerResult, indexSlices, usedFacts)
        llmUsedFactIds = []
      }
    } else {
      assistantText = isYearScope && yearDetailTrace?.year_detail
        ? generateYearDetailStubResponse(yearDetailTrace.year_detail)
        : generateStubResponse(routerResult, indexSlices, usedFacts)
      llmUsedFactIds = []
    }

    timings.llm = Date.now() - llmStart

    // 构建 facts_trace 输出
    const factsTrace: FactsTraceOutput = {
      used_facts: usedFacts,
      used_count: usedFacts.length,
      available_count: availableCount,
      source: engineData ? 'engine' : 'stub',
      selection_trace: selectionTrace,
      debug_year_histogram: debugYearHistogram,
      extracted_year_null_count: extractedYearNullCount,
      sample_extracted_years: sampleExtractedYears,
    }

    // 构建响应
    return NextResponse.json({
      assistant_text: assistantText,
      debug_used_fact_ids: llmUsedFactIds.length > 0 ? llmUsedFactIds : debugUsedFactIds,
      router_trace: routerResult.trace,
      modules_trace: modulesTrace,
      index_trace: {
        slices_used: isYearScope ? ['dayun'] : routerResult.slices,
        slices_payload: indexSlices,
      },
      facts_trace: {
        ...factsTrace,
        facts_policy: isYearScope ? 'disabled_for_year_detail' : 'enabled',
      },
      evidence_trace: evidenceTrace,  // 证据块回放
      year_detail_trace: yearDetailTrace,  // 年请求专用
      run_meta: {
        timing_ms: timings,
        llm_input_preview: llmInputPreview,
      },
    })

  } catch (error) {
    console.error('Test chat error:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: String(error) },
      { status: 500 }
    )
  }
}

// ============================================================
// normalize_facts: 为每条 fact 提取 fact_year
// ============================================================

function normalizeFacts(rawFacts: EngineFact[]): NormalizedFact[] {
  return rawFacts.map(f => {
    const { year, source } = extractFactYear(f)
    return {
      ...f,
      fact_year: year,
      year_source: source,
    }
  })
}

function extractFactYear(f: EngineFact): { year: number | null; source: string } {
  // 优先级 1: fact.year 或 fact.flow_year
  if (typeof f.year === 'number' && f.year > 1900 && f.year < 2200) {
    return { year: f.year, source: 'fact.year' }
  }
  if (typeof f.flow_year === 'number' && f.flow_year > 1900 && f.flow_year < 2200) {
    return { year: f.flow_year, source: 'fact.flow_year' }
  }

  // 优先级 2: 从 scope 抓 liunian_YYYY
  if (f.scope) {
    const scopeMatch = f.scope.match(/liunian_(\d{4})/)
    if (scopeMatch) {
      const year = parseInt(scopeMatch[1], 10)
      if (year > 1900 && year < 2200) {
        return { year, source: 'scope:liunian_YYYY' }
      }
    }
    // dayun_YYYY
    const dayunMatch = f.scope.match(/dayun_(\d{4})/)
    if (dayunMatch) {
      const year = parseInt(dayunMatch[1], 10)
      if (year > 1900 && year < 2200) {
        return { year, source: 'scope:dayun_YYYY' }
      }
    }
  }

  // 优先级 3: 从 label 抓 (19|20)\d{2}
  if (f.label) {
    const labelMatch = f.label.match(/((?:19|20)\d{2})/)
    if (labelMatch) {
      const year = parseInt(labelMatch[1], 10)
      if (year > 1900 && year < 2200) {
        return { year, source: 'label:regex' }
      }
    }
  }

  // 优先级 4: 从 type 抓
  if (f.type) {
    const typeMatch = f.type.match(/((?:19|20)\d{2})/)
    if (typeMatch) {
      const year = parseInt(typeMatch[1], 10)
      if (year > 1900 && year < 2200) {
        return { year, source: 'type:regex' }
      }
    }
  }

  // natal scope: 没有年份
  if (f.scope === 'natal') {
    return { year: null, source: 'natal:no_year' }
  }

  return { year: null, source: 'unknown:no_year' }
}

// ============================================================
// selectFactsStrict: 严格按 time_scope 过滤（禁止 fallback 到其他年份）
// ============================================================

interface SelectFactsResult {
  usedFacts: UsedFact[]
  selectionTrace: FactSelectionTrace
  availableCount: number
  debugYearHistogram: Record<number, number>
  extractedYearNullCount: number
  sampleExtractedYears: Array<{ fact_id: string; scope: string; extracted_year: number | null; year_source: string }>
}

function selectFactsStrict(
  facts: Record<string, unknown>,
  findings: { facts?: EngineFact[]; hints?: unknown[]; links?: unknown[] } | undefined,
  routerResult: RouterResult,
): SelectFactsResult {
  const { time_scope, focus } = routerResult.trace
  const currentYear = new Date().getFullYear()
  const steps: SelectionStep[] = []

  // 确定 allowed_years
  let allowedYears: number[] = []
  let allowNatal = false

  if (time_scope.type === 'year' && time_scope.year) {
    // year scope: 只允许该年
    allowedYears = [time_scope.year]
    allowNatal = true // 允许 natal 作为背景
  } else if (time_scope.type === 'range' && time_scope.years) {
    // range scope: 最近 N 年
    const n = time_scope.years
    for (let i = 0; i < n; i++) {
      allowedYears.push(currentYear - i)
      allowedYears.push(currentYear + i)
    }
    allowedYears = [...new Set(allowedYears)].sort((a, b) => a - b)
    allowNatal = true
  } else {
    // 默认: 最近 5 年
    for (let i = 0; i < 5; i++) {
      allowedYears.push(currentYear - i)
      allowedYears.push(currentYear + i)
    }
    allowedYears = [...new Set(allowedYears)].sort((a, b) => a - b)
    allowNatal = true
  }

  // ============================================================
  // Step 1: 加载并标准化 facts
  // ============================================================
  let allFacts: NormalizedFact[] = []

  if (findings?.facts && Array.isArray(findings.facts) && findings.facts.length > 0) {
    allFacts = normalizeFacts(findings.facts)
    steps.push({
      step: '1_load_findings',
      filter: 'findings.facts + normalize',
      before_count: 0,
      after_count: allFacts.length,
      reason: `从 engine 加载 ${allFacts.length} 条 facts，已标准化 fact_year`,
    })
  } else {
    // Fallback: 从 facts.luck 中提取
    const rawFacts = extractFactsFromLuck(facts)
    allFacts = normalizeFacts(rawFacts)
    steps.push({
      step: '1_load_luck_fallback',
      filter: 'facts.luck + normalize',
      before_count: 0,
      after_count: allFacts.length,
      reason: `findings.facts 为空，从 facts.luck 提取 ${allFacts.length} 条事件`,
    })
  }

  const availableCount = allFacts.length

  // ============================================================
  // 构建诊断字段
  // ============================================================
  const buildDiagnostics = (normalizedFacts: NormalizedFact[]) => {
    // year histogram
    const yearHistogram: Record<number, number> = {}
    let nullCount = 0
    
    for (const f of normalizedFacts) {
      if (f.fact_year !== null) {
        yearHistogram[f.fact_year] = (yearHistogram[f.fact_year] || 0) + 1
      } else {
        nullCount++
      }
    }
    
    // sample extracted years (前10条)
    const sampleYears = normalizedFacts.slice(0, 10).map(f => ({
      fact_id: f.fact_id,
      scope: f.scope,
      extracted_year: f.fact_year,
      year_source: f.year_source,
    }))
    
    return { yearHistogram, nullCount, sampleYears }
  }

  if (allFacts.length === 0) {
    return {
      usedFacts: [],
      selectionTrace: {
        time_scope,
        focus,
        allowed_years: allowedYears,
        steps,
        fallback_triggered: false,
        fallback_reason: 'No facts available from engine',
        final_count: 0,
      },
      availableCount: 0,
      debugYearHistogram: {},
      extractedYearNullCount: 0,
      sampleExtractedYears: [],
    }
  }

  const diagnostics = buildDiagnostics(allFacts)

  // ============================================================
  // Step 2: 按 allowed_years 严格过滤（禁止 fallback 到其他年份）
  // ============================================================
  let filtered: NormalizedFact[] = []

  // 分离 liunian facts 和 natal/other facts
  const liunianFacts = allFacts.filter(f => f.scope?.startsWith('liunian'))
  const natalFacts = allFacts.filter(f => f.scope === 'natal')
  const otherFacts = allFacts.filter(f => !f.scope?.startsWith('liunian') && f.scope !== 'natal')

  steps.push({
    step: '2_categorize',
    filter: 'by scope type',
    before_count: allFacts.length,
    after_count: allFacts.length,
    reason: `liunian: ${liunianFacts.length}, natal: ${natalFacts.length}, other: ${otherFacts.length}`,
  })

  // 严格过滤 liunian facts
  const matchedLiunian = liunianFacts.filter(f => {
    return f.fact_year !== null && allowedYears.includes(f.fact_year)
  })

  steps.push({
    step: '3_filter_liunian_by_year',
    filter: `fact_year in [${allowedYears.slice(0, 5).join(',')}${allowedYears.length > 5 ? '...' : ''}]`,
    before_count: liunianFacts.length,
    after_count: matchedLiunian.length,
    reason: matchedLiunian.length > 0 
      ? `${matchedLiunian.length} 条 liunian facts 匹配 allowed_years`
      : `无 liunian facts 匹配 allowed_years`,
  })

  filtered = matchedLiunian

  // ============================================================
  // Step 3b: 如果 liunian facts 为空，尝试从 facts.luck 生成 synthetic fact
  // ============================================================
  if (filtered.length === 0 && time_scope.type === 'year' && time_scope.year) {
    const syntheticFacts = generateSyntheticFactsFromLuck(facts, time_scope.year)
    if (syntheticFacts.length > 0) {
      filtered = syntheticFacts
      steps.push({
        step: '3b_synthetic_from_luck',
        filter: `facts.luck.liunian[year=${time_scope.year}]`,
        before_count: 0,
        after_count: syntheticFacts.length,
        reason: `无特殊事件，从 facts.luck 生成 ${syntheticFacts.length} 条年度基础信息`,
      })
    } else {
      steps.push({
        step: '3b_no_synthetic',
        filter: `facts.luck.liunian[year=${time_scope.year}]`,
        before_count: 0,
        after_count: 0,
        reason: `该年在 facts.luck 中也无数据`,
      })
    }
  }

  // 如果 liunian 为空且允许 natal，补充 natal 作为背景
  let fallbackTriggered = false
  let fallbackReason = ''

  if (filtered.length === 0 && allowNatal && natalFacts.length > 0) {
    fallbackTriggered = true
    fallbackReason = `无 liunian facts 匹配 ${allowedYears.join(',')}，补充 ${Math.min(natalFacts.length, FACTS_TOP_K)} 条 natal 作为背景`
    filtered = natalFacts.slice(0, FACTS_TOP_K)

    steps.push({
      step: '4_natal_fallback',
      filter: 'natal only',
      before_count: natalFacts.length,
      after_count: filtered.length,
      reason: fallbackReason,
    })
  }

  // ============================================================
  // Step 3: 取 topK
  // ============================================================
  const selected = filtered.slice(0, FACTS_TOP_K)

  steps.push({
    step: '5_take_topK',
    filter: `topK=${FACTS_TOP_K}`,
    before_count: filtered.length,
    after_count: selected.length,
    reason: `取前 ${FACTS_TOP_K} 条`,
  })

  // 转换为 UsedFact 格式（带 reason）
  const usedFacts: UsedFact[] = selected.map(f => toUsedFact(f, allowedYears))

  return {
    usedFacts,
    selectionTrace: {
      time_scope,
      focus,
      allowed_years: allowedYears,
      steps,
      fallback_triggered: fallbackTriggered,
      fallback_reason: fallbackReason,
      final_count: usedFacts.length,
    },
    availableCount,
    debugYearHistogram: diagnostics.yearHistogram,
    extractedYearNullCount: diagnostics.nullCount,
    sampleExtractedYears: diagnostics.sampleYears,
  }
}

function extractFactsFromLuck(facts: Record<string, unknown>): EngineFact[] {
  const result: EngineFact[] = []

  if (!facts.luck) return result

  const luck = facts.luck as {
    groups?: Array<{
      liunian?: Array<{
        year?: number
        all_events?: Array<Record<string, unknown>>
      }>
    }>
  }

  const groups = luck.groups || []
  let eventIdx = 0

  for (const group of groups) {
    const liunianList = group.liunian || []
    for (const liunian of liunianList) {
      const year = liunian.year
      const allEvents = liunian.all_events || []

      for (const event of allEvents) {
        const eventType = (event.type as string) || 'event'
        const label = (event.label as string) || eventType

        result.push({
          fact_id: `evt_${year}_${eventType}_${eventIdx++}`,
          type: eventType,
          kind: (event.kind as string) || eventType,
          scope: `liunian_${year}`,
          label,
          flow_year: year,
          risk_percent: event.risk_percent as number,
          ...event,
        })
      }
    }
  }

  return result
}

/**
 * 从 facts.luck 中为指定年份生成 synthetic facts（当没有特殊事件时）
 */
function generateSyntheticFactsFromLuck(facts: Record<string, unknown>, targetYear: number): NormalizedFact[] {
  if (!facts.luck) return []

  const luck = facts.luck as {
    groups?: Array<{
      liunian?: Array<{
        year?: number
        total_risk_percent?: number
        half1_label?: string
        half2_label?: string
        risk_from_gan?: number
        risk_from_zhi?: number
        liunian_gan?: string
        liunian_zhi?: string
        all_events?: Array<unknown>
      }>
    }>
  }

  const groups = luck.groups || []

  for (const group of groups) {
    const liunianList = group.liunian || []
    for (const liunian of liunianList) {
      if (liunian.year === targetYear) {
        const result: NormalizedFact[] = []

        // 生成年度概览 fact
        const totalRisk = liunian.total_risk_percent ?? 0
        const half1 = liunian.half1_label || ''
        const half2 = liunian.half2_label || ''
        const liunianGan = liunian.liunian_gan || ''
        const liunianZhi = liunian.liunian_zhi || ''

        // 只有当有实际数据时才生成
        if (totalRisk > 0 || half1 || half2 || liunianGan || liunianZhi) {
          result.push({
            fact_id: `syn_${targetYear}_overview`,
            type: 'year_overview',
            kind: 'synthetic',
            scope: `liunian_${targetYear}`,
            label: `${targetYear}年概览`,
            flow_year: targetYear,
            risk_percent: totalRisk,
            fact_year: targetYear,
            year_source: 'synthetic:facts.luck',
            half1_label: half1,
            half2_label: half2,
            liunian_gan: liunianGan,
            liunian_zhi: liunianZhi,
          })
        }

        // 如果有上半年信息
        if (half1) {
          result.push({
            fact_id: `syn_${targetYear}_half1`,
            type: 'half_year',
            kind: 'synthetic',
            scope: `liunian_${targetYear}`,
            label: `${targetYear}年上半年：${half1}`,
            flow_year: targetYear,
            risk_percent: liunian.risk_from_gan ?? 0,
            fact_year: targetYear,
            year_source: 'synthetic:half1_label',
          })
        }

        // 如果有下半年信息
        if (half2) {
          result.push({
            fact_id: `syn_${targetYear}_half2`,
            type: 'half_year',
            kind: 'synthetic',
            scope: `liunian_${targetYear}`,
            label: `${targetYear}年下半年：${half2}`,
            flow_year: targetYear,
            risk_percent: liunian.risk_from_zhi ?? 0,
            fact_year: targetYear,
            year_source: 'synthetic:half2_label',
          })
        }

        // 如果完全没有数据，生成一条"无特殊事件"的 fact
        if (result.length === 0) {
          result.push({
            fact_id: `syn_${targetYear}_no_events`,
            type: 'no_special_events',
            kind: 'synthetic',
            scope: `liunian_${targetYear}`,
            label: `${targetYear}年无特殊命理事件，整体平稳`,
            flow_year: targetYear,
            risk_percent: 0,
            fact_year: targetYear,
            year_source: 'synthetic:no_events',
          })
        }

        return result
      }
    }
  }

  return []
}

function toUsedFact(f: NormalizedFact, allowedYears: number[]): UsedFact {
  // 构建 text_preview（限制 200 字符）
  const previewParts: string[] = []
  previewParts.push(f.label || f.type)
  if (f.risk_percent !== undefined) {
    previewParts.push(`风险${f.risk_percent}%`)
  }
  if (f.kind && f.kind !== f.type) {
    previewParts.push(`[${f.kind}]`)
  }

  const textPreview = previewParts.join(' | ').slice(0, 200)

  // 构建 reason
  let reason = ''
  if (f.fact_year !== null) {
    reason = `fact_year=${f.fact_year} (from ${f.year_source}) in allowed_years=[${allowedYears.slice(0, 3).join(',')}...]`
  } else if (f.scope === 'natal') {
    reason = 'natal fact as background (no liunian match)'
  } else {
    reason = `included: ${f.year_source}`
  }

  return {
    fact_id: f.fact_id,
    type: f.type,
    scope: f.scope,
    fact_year: f.fact_year,
    year_source: f.year_source,
    label: f.label,
    text_preview: textPreview,
    reason,
  }
}

// ============================================================
// LLM Response Parser
// ============================================================

function parseLLMResponse(
  rawContent: string,
  availableFactIds: string[]
): { text: string; usedFactIds: string[] } {
  const usedFactIds: string[] = []

  for (const factId of availableFactIds) {
    if (rawContent.includes(factId)) {
      usedFactIds.push(factId)
    }
  }

  if (usedFactIds.length === 0 && availableFactIds.length > 0 && rawContent.length > 100) {
    usedFactIds.push(...availableFactIds.slice(0, Math.min(3, availableFactIds.length)))
  }

  return {
    text: rawContent,
    usedFactIds,
  }
}

// ============================================================
// LLM Context Builder
// ============================================================

function getSystemPrompt(
  flags: { need_dayun_mention: boolean; dayun_grade_public: '好' | '一般' },
  factIds: string[]
): string {
  let prompt = `你是一位专业的命理分析师，基于用户的八字信息提供运势解读。

规则：
1. 使用温和、积极的语气，即使运势不佳也要给出建议
2. 回答要简洁明了，控制在200-300字
3. 结合用户的具体问题进行回答
4. 不要透露技术细节或提及"index"、"trace"等术语
5. 用自然的中文回答`

  if (factIds.length > 0) {
    prompt += `

【重要】FACTS 部分包含 ${factIds.length} 条具体命理事实：
- 你必须在回答中引用这些事实来支撑你的分析
- 每个 fact 都有 fact_id
- 你的分析必须基于这些 facts 中描述的具体内容
- 如果无法基于 facts 得出结论，请明确说明"根据目前信息..."`
  } else {
    prompt += `

注意：当前时间范围内没有具体的命理事件记录，请基于 INDEX 中的统计数据进行概括性分析，并说明这是整体趋势而非具体事件。`
  }

  if (flags.need_dayun_mention) {
    prompt += `
- 需要提及大运情况，大运评级为"${flags.dayun_grade_public}"`
  }

  return prompt
}

/**
 * 年请求专用 System Prompt（严格顺序 + gate 规则）
 */
function getYearDetailSystemPrompt(targetYear: number): string {
  return `你是一位专业的命理分析师。用户询问的是 ${targetYear} 年的具体运势。

【输出顺序必须严格遵循】

1. 【大运背景】（单独一段，1-2句）
   - 只说当前大运名称和年份范围
   - 等级只用"好"或"一般"（不要用"不好/差/坏"）

2. 【上下半年】（第一屏必须出现）
   - 使用固定四类枚举：好运 / 一般 / 凶 / 变动
   - 如果是"变动"：只写"会变动"，不加解释

3. 【流年结构】（天干→地支）
   - 天干行：天干 X｜十神 XX｜用神 是/否｜标签：...
   - 若危险系数=0：写"不易出现意外和风险"（不写0%）
   - 若危险系数>0：写"危险系数：XX%"
   - 地支行同理

4. 【提示汇总】（最重要的 gate 规则）
   - 只允许依据【提示汇总】内容讲"今年会出现什么问题/引动/推进"
   - 如果【提示汇总】为空：写"今年暂无额外提示汇总"，不要自己推断
   - 【关键禁止】：如果只有冲/克/害/刑信息但【提示汇总】没写，绝对不能讲

【严格禁止】
- 不要输出 ${targetYear} 以外的任何年份数字
- 不要输出"建议从事..."等C口吻（保持分析师风格）
- 不要从冲克害刑自己推断，必须以【提示汇总】为准
- 术语保留中文：十神/用神/天干/地支 不翻译

【格式要求】
- 回答200-300字
- 使用温和积极的语气`
}

/**
 * 年请求专用 Context 构建
 */
function buildYearDetailContext(
  query: string,
  yearDetail: YearDetail,
  indexSlices: Record<string, unknown>,
  birth_date: string,
  birth_time: string,
  is_male: boolean
): string {
  const parts: string[] = []

  parts.push(`【用户问题】${query}`)
  parts.push(`【用户信息】${is_male ? '男性' : '女性'}，出生于 ${birth_date} ${birth_time}`)
  parts.push(`【目标年份】${yearDetail.year}年`)
  parts.push('')

  // DAYUN_BRIEF_BLOCK
  if (yearDetail.dayun_brief) {
    const db = yearDetail.dayun_brief
    parts.push('=== DAYUN_BRIEF_BLOCK（大运背景）===')
    parts.push(`大运：${db.name}（${db.start_age}-${db.end_age}岁）`)
    parts.push(`等级：${db.grade}`)
    parts.push('')
  }

  // YEAR_DETAIL_BLOCK
  parts.push('=== YEAR_DETAIL_BLOCK（年度详情）===')
  
  // 上下半年
  parts.push(`【上下半年】上半年：${yearDetail.half_year_grade.first}，下半年：${yearDetail.half_year_grade.second}`)
  
  // 天干
  const gan = yearDetail.gan_block
  const ganRiskStr = gan.risk_pct > 0 ? `危险系数：${gan.risk_pct.toFixed(1)}%` : '不易出现意外和风险'
  const ganTagsStr = gan.tags.length > 0 ? gan.tags.join('/') : ''
  parts.push(`【天干】${gan.gan}｜十神 ${gan.shishen}｜用神 ${gan.yongshen_yesno}｜标签：${ganTagsStr}｜${ganRiskStr}`)
  
  // 地支
  const zhi = yearDetail.zhi_block
  const zhiRiskStr = zhi.risk_pct > 0 ? `危险系数：${zhi.risk_pct.toFixed(1)}%` : '不易出现意外和风险'
  const zhiTagsStr = zhi.tags.length > 0 ? zhi.tags.join('/') : ''
  parts.push(`【地支】${zhi.zhi}｜十神 ${zhi.shishen}｜用神 ${zhi.yongshen_yesno}｜标签：${zhiTagsStr}｜${zhiRiskStr}`)
  
  // 提示汇总
  if (yearDetail.hint_summary_lines.length > 0) {
    parts.push('【提示汇总】')
    for (const hint of yearDetail.hint_summary_lines) {
      parts.push(`  - ${hint}`)
    }
  } else {
    parts.push('【提示汇总】今年暂无额外提示汇总')
  }

  return parts.join('\n')
}

/**
 * 年请求专用 Stub Response
 */
function generateYearDetailStubResponse(yearDetail: YearDetail): string {
  const parts: string[] = []
  
  // 大运背景
  if (yearDetail.dayun_brief) {
    const db = yearDetail.dayun_brief
    parts.push(`【大运背景】当前处于${db.name}大运（${db.start_age}-${db.end_age}岁），整体运势${db.grade}。`)
    parts.push('')
  }
  
  // 上下半年
  parts.push(`【上下半年】${yearDetail.year}年上半年${yearDetail.half_year_grade.first}，下半年${yearDetail.half_year_grade.second}。`)
  parts.push('')
  
  // 流年结构
  const gan = yearDetail.gan_block
  const ganRiskStr = gan.risk_pct > 0 ? `危险系数${gan.risk_pct.toFixed(1)}%` : '不易出现意外和风险'
  parts.push(`【流年结构】天干${gan.gan}（${gan.shishen}），${gan.yongshen_yesno === '是' ? '用神得力' : '非用神'}，${ganRiskStr}。`)
  
  const zhi = yearDetail.zhi_block
  const zhiRiskStr = zhi.risk_pct > 0 ? `危险系数${zhi.risk_pct.toFixed(1)}%` : '不易出现意外和风险'
  parts.push(`地支${zhi.zhi}（${zhi.shishen}），${zhi.yongshen_yesno === '是' ? '用神得力' : '非用神'}，${zhiRiskStr}。`)
  parts.push('')
  
  // 提示汇总
  if (yearDetail.hint_summary_lines.length > 0) {
    parts.push('【提示汇总】')
    for (const hint of yearDetail.hint_summary_lines) {
      parts.push(`• ${hint}`)
    }
  } else {
    parts.push('【提示汇总】今年暂无额外提示汇总。')
  }
  
  return parts.join('\n')
}

/**
 * 构建 Evidence Trace（证据块回放）
 */
function buildEvidenceTrace(
  isYearScope: boolean,
  targetYear: number | undefined,
  yearDetail: YearDetail | null | undefined,
  dayunBrief: { name: string; start_age: number; end_age: number; grade: string } | null | undefined,
  indexSlices: Record<string, unknown>,
  usedFacts: UsedFact[],
): EvidenceTrace {
  const usedBlocks: EvidenceBlock[] = []
  const llmContextOrder: string[] = []

  if (isYearScope && targetYear) {
    // 年请求模式

    // 1. DAYUN_BRIEF
    if (dayunBrief) {
      const dayunText = `大运：${dayunBrief.name}（${dayunBrief.start_age}-${dayunBrief.end_age}岁），等级：${dayunBrief.grade}`
      usedBlocks.push({
        block_id: 'dayun_brief_current',
        block_type: 'DAYUN_BRIEF',
        source: 'index',
        scope: 'year',
        year: targetYear,
        used: true,
        reason: 'year_scope_requires_dayun_brief',
        preview: dayunText.slice(0, 300),
        length_chars: dayunText.length,
        full_text: dayunText,
      })
      llmContextOrder.push('DAYUN_BRIEF')
    } else {
      usedBlocks.push({
        block_id: 'dayun_brief_current',
        block_type: 'DAYUN_BRIEF',
        source: 'index',
        scope: 'year',
        year: targetYear,
        used: false,
        reason: 'dayun_brief_not_available',
        preview: '',
        length_chars: 0,
      })
    }

    // 2. YEAR_DETAIL_TEXT
    if (yearDetail) {
      const rawText = yearDetail.raw_text || ''
      usedBlocks.push({
        block_id: `year_detail_text_${targetYear}`,
        block_type: 'YEAR_DETAIL_TEXT',
        source: 'engine',
        scope: 'year',
        year: targetYear,
        used: true,
        reason: 'year_scope_requires_year_detail',
        preview: rawText.slice(0, 300),
        length_chars: rawText.length,
        full_text: rawText,
      })
      llmContextOrder.push('YEAR_DETAIL_TEXT')
    } else {
      usedBlocks.push({
        block_id: `year_detail_text_${targetYear}`,
        block_type: 'YEAR_DETAIL_TEXT',
        source: 'engine',
        scope: 'year',
        year: targetYear,
        used: false,
        reason: 'year_detail_parse_failed',
        preview: '',
        length_chars: 0,
      })
    }

  } else {
    // 非年请求模式（range/general）

    // 1. FACTS
    if (usedFacts.length > 0) {
      const factsText = usedFacts.map(f => `[${f.fact_id}] ${f.label}`).join('\n')
      usedBlocks.push({
        block_id: 'facts_selected',
        block_type: 'FACTS_BLOCK',
        source: 'engine',
        scope: 'range',
        used: true,
        reason: 'facts_selected_for_context',
        preview: factsText.slice(0, 300),
        length_chars: factsText.length,
        full_text: factsText,
      })
      llmContextOrder.push('FACTS_BLOCK')
    }

    // 2. Index slices
    for (const [sliceName, sliceData] of Object.entries(indexSlices)) {
      const sliceText = JSON.stringify(sliceData, null, 2)
      usedBlocks.push({
        block_id: `index_${sliceName}`,
        block_type: `INDEX_${sliceName.toUpperCase()}`,
        source: 'index',
        scope: 'range',
        used: true,
        reason: 'index_slice_for_context',
        preview: sliceText.slice(0, 300),
        length_chars: sliceText.length,
        full_text: sliceText,
      })
      llmContextOrder.push(`INDEX_${sliceName.toUpperCase()}`)
    }
  }

  return {
    used_blocks: usedBlocks,
    llm_context_order: llmContextOrder,
  }
}

function buildLLMContext(
  query: string,
  routerResult: RouterResult,
  usedFacts: UsedFact[],
  indexSlices: Record<string, unknown>,
  birth_date: string,
  birth_time: string,
  is_male: boolean
): string {
  const parts: string[] = []

  parts.push(`【用户问题】${query}`)
  parts.push(`【用户信息】${is_male ? '男性' : '女性'}，出生于 ${birth_date} ${birth_time}`)

  const { time_scope, focus } = routerResult.trace
  if (time_scope.type === 'year' && time_scope.year) {
    parts.push(`【时间范围】${time_scope.year}年`)
  } else if (time_scope.type === 'range' && time_scope.years) {
    parts.push(`【时间范围】最近${time_scope.years}年`)
  }
  parts.push(`【关注领域】${focus}`)

  parts.push('')
  parts.push('=== FACTS（具体命理事实）===')
  if (usedFacts.length > 0) {
    for (const fact of usedFacts) {
      parts.push(`• [${fact.fact_id}] ${fact.scope} (year=${fact.fact_year ?? 'N/A'}) | ${fact.label} | ${fact.text_preview}`)
    }
  } else {
    parts.push('（当前时间范围内没有匹配的具体事件记录）')
  }

  parts.push('')
  parts.push('=== INDEX（运势统计数据）===')
  parts.push(JSON.stringify(indexSlices, null, 2))

  return parts.join('\n')
}

// ============================================================
// Modules Trace
// ============================================================

function buildModulesTrace(
  slices: string[], 
  hasFactsUsed: boolean,
  isYearScope: boolean = false,
  hasYearDetail: boolean = false,
  targetYear?: number
): ModuleTrace[] {
  const modules: ModuleTrace[] = []

  if (isYearScope) {
    // 年请求专用模块
    modules.push({
      module: 'DAYUN_BRIEF_BLOCK',
      source: 'index',
      used: true,
      produced_blocks: ['dayun_brief_current'],
    })
    modules.push({
      module: 'YEAR_DETAIL_BLOCK',
      source: 'engine',
      used: hasYearDetail,
      produced_blocks: hasYearDetail && targetYear ? [`year_detail_text_${targetYear}`] : [],
    })
    modules.push({
      module: 'FACTS_BLOCK',
      source: 'engine',
      used: false,
      reason: 'disabled_for_year_detail',
      produced_blocks: [],
    })
  } else {
    // 普通请求
    modules.push({
      module: 'FACTS_BLOCK',
      source: 'engine',
      used: hasFactsUsed,
      produced_blocks: hasFactsUsed ? ['facts_selected'] : [],
    })

    for (const slice of slices) {
      modules.push({
        module: `${slice.toUpperCase()}_BLOCK`,
        source: 'index',
        used: true,
        produced_blocks: [`index_${slice}`],
      })
    }
  }

  return modules
}

// ============================================================
// Stub Data & Response
// ============================================================

function getStubEngineData(birth_date: string, birth_time: string, is_male: boolean) {
  const currentYear = new Date().getFullYear()
  return {
    index: {
      meta: { base_year: currentYear },
      dayun: {
        current_dayun_ref: { label: '壬午', start_year: 2020, end_year: 2029, fortune_label: '一般' },
        fortune_label: '一般',
        yongshen_swap: { has_swap: false, items: [], hint: '' },
      },
      year_grade: {
        last5: [
          { year: currentYear, Y: 12.0, year_label: '上半年 一般，下半年 好运' },
        ],
        future3: [
          { year: currentYear, Y: 12.0, year_label: '上半年 一般，下半年 好运' },
        ],
      },
      relationship: { hit: false, years_hit: [] },
      turning_points: { all: [], nearby: [], should_mention: false },
      good_year_search: { has_good_in_future3: true, next_good_year: currentYear },
      personality: { axis_summaries: [] },
    },
    facts: {
      _stub: true,
      luck: {
        groups: [{
          liunian: [{
            year: currentYear,
            all_events: [
              { type: 'pattern', label: '食神生财', risk_percent: 5.0 },
            ],
          }],
        }],
      },
    },
    findings: {
      facts: [
        { fact_id: 'stub_f1', type: 'pattern', kind: 'pattern', scope: `liunian_${currentYear}`, label: '食神生财', flow_year: currentYear, risk_percent: 5.0 },
      ],
      hints: [],
      links: [],
    },
  }
}

function generateStubResponse(
  routerResult: RouterResult,
  indexSlices: Record<string, unknown>,
  usedFacts: UsedFact[]
): string {
  const { focus, time_scope, flags } = routerResult.trace

  let factsSection = ''
  if (usedFacts.length > 0) {
    const factDescriptions = usedFacts.map(f => f.label).filter(Boolean)
    if (factDescriptions.length > 0) {
      factsSection = `根据您的命盘，今年有${factDescriptions.slice(0, 3).join('、')}等特征。`
    }
  }

  if (focus === 'relationship') {
    return `根据您的八字分析，${factsSection || '最近几年感情运势较为平稳。'}建议保持积极开放的心态。`
  }

  if (time_scope.type === 'year' && time_scope.year) {
    if (usedFacts.length === 0) {
      return `根据您的八字分析，${time_scope.year}年整体运势平稳，没有特别突出的命理事件。${flags.dayun_grade_public === '好' ? '大运较好，可稳步发展。' : '大运一般，建议稳中求进。'}`
    }

    const yearGrade = indexSlices.year_grade as { last5?: Array<{ year: number; Y: number; year_label: string }> } | undefined
    const yearData = yearGrade?.last5?.find(y => y.year === time_scope.year)

    if (yearData) {
      return `根据您的八字分析，${time_scope.year}年：${factsSection}

${yearData.year_label}

总体风险指数 ${yearData.Y}%。${flags.dayun_grade_public === '好' ? '大运较好。' : '大运一般。'}`
    }
  }

  return `根据您的八字分析，${factsSection || '最近几年整体运势保持平稳。'}${flags.dayun_grade_public === '好' ? '大运较好。' : '大运一般。'}`
}
