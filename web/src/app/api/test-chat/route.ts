import { NextRequest, NextResponse } from 'next/server'
import { route, RouterResult } from '@/lib/router'
import OpenAI from 'openai'
import { selectFromFacts } from '@/lib/router/select_facts'

// OpenAI client
const OPENAI_API_KEY = process.env.OPENAI_API_KEY
const openai = OPENAI_API_KEY ? new OpenAI({ apiKey: OPENAI_API_KEY }) : null

// Python Engine URL
const PYTHON_ENGINE_URL = process.env.PYTHON_ENGINE_URL || 'http://localhost:5000'

// preview_max_chars（统一为 600 字符）
const PREVIEW_MAX_CHARS = 600

// ============================================================
// Types（新统一结构）
// ============================================================

// Context Block（LLM 上下文单个块）
interface ContextBlock {
  kind: 'facts' | 'index' | 'other'
  block_type: string
  block_id: string
  used: boolean
  source: 'engine' | 'index' | 'stub'
  chars_total: number
  preview: string         // 前 PREVIEW_MAX_CHARS 字符
  full_text?: string      // 可选：完整打印层渲染文本（不是 engine 原始 JSON）
  year?: number
  reason?: string
}

// Router 元数据（给前端展示）
interface RouterMeta {
  router_id: string
  intent: string
  mode: 'year' | 'range' | 'general'
  reason: string
  child_router?: RouterMeta | null
}

// Context Trace（权威的 LLM 上下文回放）
interface ContextTrace {
  router: RouterMeta
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
    timing_ms: { router: number; engine: number; llm: number }
    llm_input_preview?: string
  }
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

// ============================================================
// 十神标签词库（从 Python bazi/shishen.py 复制）
// ============================================================
const SHISHEN_LABEL_MAP: Record<string, Record<string, string>> = {
  // 官杀
  "正官": {
    "true": "认可/升迁/名誉",
    "false": "规章压力/束缚/被考核/开销大",
  },
  "七杀": {
    "true": "领导赏识/扛事机会/突破",
    "false": "工作压力/对抗强/紧张感/开销大",
  },
  // 印
  "正印": {
    "true": "贵人/支持/学习证书",
    "false": "胡思乱想/思前顾后/效率低",
  },
  "偏印": {
    "true": "偏门技术/思想突破/学习研究/灵感",
    "false": "多想/孤立/节奏乱",
  },
  // 食伤
  "食神": {
    "true": "产出/表现/生活舒适/技术突破",
    "false": "贪舒服/拖延/松散",
  },
  "伤官": {
    "true": "表达/创新/技术突破/灵感",
    "false": "顶撞权威/口舌/冲突/贪玩",
  },
  // 财
  "正财": {
    "true": "努力得回报/方向更清晰/稳步积累(生活&工作)",
    "false": "现实压力/精神压力大/想不开",
  },
  "偏财": {
    "true": "机会钱/副业/人脉/意外之财",
    "false": "开销大/现实压力/精神压力大",
  },
  // 比劫
  "比肩": {
    "true": "自信独立/同辈助力/合伙资源/行动力",
    "false": "竞争争夺/冲动分心/投机或赌博破财/购置不动产化解",
  },
  "劫财": {
    "true": "自信独立/同辈助力/合伙资源/行动力",
    "false": "竞争争夺/冲动分心/投机或赌博破财/购置不动产化解",
  },
}

function getShishenLabel(shishenName: string | undefined, isYongshen: boolean): string {
  if (!shishenName) return ''
  const labels = SHISHEN_LABEL_MAP[shishenName]
  if (!labels) return ''
  return labels[String(isYongshen)] || ''
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

    // 运行 Router（使用 index 做 Decide；但 Select 只能从 facts 取内容）
    const routerStart = Date.now()
    let routerResult = route(message, {}, '一般')
    timings.router = Date.now() - routerStart
    const preTimeScope = routerResult.trace.time_scope

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
          target_year: preTimeScope.type === 'year' ? preTimeScope.year : undefined,
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

    // 用实际的 index + dayunGrade 重新运行 Router（Decide only）
    const dayunGrade = (engineData.index as { dayun?: { fortune_label?: string } })?.dayun?.fortune_label as '好运' | '一般' | '坏运' || '一般'
    routerResult = route(message, engineData.index, dayunGrade)
    const isYearScope = routerResult.trace.time_scope.type === 'year'
    const targetYear = isYearScope ? routerResult.trace.time_scope.year : undefined

    // Select：只从 facts 中选内容（selected_facts_paths 可复现）
    const baseYear = new Date().getFullYear()
    const selectedFactsResult = selectFromFacts(engineData.facts, routerResult.trace, baseYear)

    // ============================================================
    // 构建 LLM 上下文：只用"打印层渲染文本"，不喂 engine 原始 JSON
    // ============================================================
    const usedBlocks: ContextBlock[] = []
    const contextOrder: string[] = []
    const llmContextParts: string[] = []
    const selectedFactIds: string[] = []

    llmContextParts.push(`【用户问题】${message}`)

    if (isYearScope && targetYear) {
      // === 年请求模式 ===
      // 1. DAYUN_BRIEF（从 facts 中选出的大运信息，渲染为文本）
      const dayunData = (selectedFactsResult.selected_facts as any)?.dayun
      if (dayunData) {
        const dayunText = renderDayunBrief(dayunData)
        usedBlocks.push({
          kind: 'facts',
          block_type: 'DAYUN_BRIEF',
          block_id: 'dayun_brief_current',
          used: true,
          source: 'engine',
          chars_total: dayunText.length,
          preview: dayunText.slice(0, PREVIEW_MAX_CHARS),
          full_text: dayunText,
          year: targetYear,
          reason: 'year_scope_requires_dayun_brief',
        })
        contextOrder.push('DAYUN_BRIEF')
        llmContextParts.push('')
        llmContextParts.push('=== 大运背景 ===')
        llmContextParts.push(dayunText)
      }

      // 2. YEAR_DETAIL_TEXT（从 facts 中选出的流年详情，渲染为文本）
      const liunianData = (selectedFactsResult.selected_facts as any)?.liunian
      if (liunianData) {
        const yearDetailText = renderYearDetail(liunianData, targetYear)
        usedBlocks.push({
          kind: 'facts',
          block_type: 'YEAR_DETAIL_TEXT',
          block_id: `year_detail_${targetYear}`,
          used: true,
          source: 'engine',
          chars_total: yearDetailText.length,
          preview: yearDetailText.slice(0, PREVIEW_MAX_CHARS),
          full_text: yearDetailText,
          year: targetYear,
          reason: 'year_scope_requires_year_detail',
        })
        contextOrder.push('YEAR_DETAIL_TEXT')
        llmContextParts.push('')
        llmContextParts.push(`=== ${targetYear}年流年详情 ===`)
        llmContextParts.push(yearDetailText)
      }

      llmContextParts.push('')
      llmContextParts.push('【重要】只允许根据上述信息中的"提示汇总"讲解今年运势。如果提示汇总为空：写"今年暂无额外提示汇总"。')

    } else {
      // === 范围请求模式：固定 last5（当年+往前4年，旧->新）===
      const last5Years = getFixedLast5Years(baseYear) // [base-4, ..., base] 升序
      const { linesText, liuniansUsed } = renderFactsLast5Compact(engineData.facts, last5Years)
      
      if (linesText) {
        usedBlocks.push({
          kind: 'facts',
          block_type: 'FACTS_LAST5_COMPACT_BLOCK',
          block_id: 'facts_last5_compact',
          used: true,
          source: 'engine',
          chars_total: linesText.length,
          preview: linesText.slice(0, PREVIEW_MAX_CHARS),
          full_text: linesText,
          reason: 'range_scope_last5_fixed',
        })
        contextOrder.push('FACTS_LAST5_COMPACT_BLOCK')
        llmContextParts.push('')
        llmContextParts.push('=== 最近5年运势概览（旧→新） ===')
        llmContextParts.push(linesText)
      }

      // 下钻：year_category 为 凶/有变动（或半年含“凶/变动”）的全部追加 YEAR_DETAIL_TEXT
      for (const ln of liuniansUsed) {
        if (isRiskyYear(ln)) {
          const yd = renderYearDetail(ln, ln.year)
          usedBlocks.push({
            kind: 'facts',
            block_type: 'YEAR_DETAIL_TEXT',
            block_id: `year_detail_${ln.year}`,
            used: true,
            source: 'engine',
            chars_total: yd.length,
            preview: yd.slice(0, PREVIEW_MAX_CHARS),
            full_text: yd,
            year: ln.year,
            reason: 'risky_year_auto_drill',
          })
          contextOrder.push(`YEAR_DETAIL_TEXT_${ln.year}`)
          llmContextParts.push('')
          llmContextParts.push(`=== ${ln.year}年流年详情 ===`)
          llmContextParts.push(yd)
        }
      }
    }

    // 添加 index 使用的 blocks（仅用于 decide/定位，不作为事实正文）
    const usedIndexBlockIds: string[] = []
    for (const slice of routerResult.slices) {
      if (slice in (engineData.index as Record<string, unknown>)) {
        usedIndexBlockIds.push(`index_${slice}`)
        // 不把 index 内容喂给 LLM，只记录使用了哪些
        usedBlocks.push({
          kind: 'index',
          block_type: `INDEX_${slice.toUpperCase()}`,
          block_id: `index_${slice}`,
          used: true,
          source: 'index',
          chars_total: 0, // index 不作为正文
          preview: '(index slice used for routing decision only)',
          reason: 'index_used_for_decide_not_content',
        })
      }
    }

    const llmContext = llmContextParts.join('\n')
    const llmInputPreview = llmContext.slice(0, 4000)

    // 构建 router_meta
    const routerMeta: RouterMeta = {
      router_id: 'main_router_v1',
      intent: routerResult.trace.intent,
      mode: isYearScope ? 'year' : 'range',
      reason: routerResult.trace.rules_matched.join(', '),
      child_router: null, // 暂无 child_router
    }

    // 构建 context_trace（权威）
    const contextTrace: ContextTrace = {
      router: routerMeta,
      used_blocks: usedBlocks,
      context_order: contextOrder,
      facts_selection: {
        selected_facts_paths: selectedFactsResult.selected_facts_paths,
        selected_fact_ids: selectedFactIds,
      },
      index_usage: {
        index_hits: routerResult.trace.index_hits || [],
        used_index_block_ids: usedIndexBlockIds,
      },
      run_meta: {
        timing_ms: timings,
        llm_input_preview: llmInputPreview,
      },
    }

    // 调用 LLM
    let assistantText = ''
    const llmStart = Date.now()

    const systemPrompt = isYearScope
      ? getYearDetailSystemPrompt(targetYear || baseYear)
      : getSystemPrompt(routerResult.trace.flags)

    if (openai) {
      try {
        const completion = await openai.chat.completions.create({
          model: 'gpt-4o-mini',
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: llmContext },
          ],
          temperature: 0.7,
          max_tokens: 1200,
        })

        assistantText = completion.choices[0]?.message?.content || '抱歉，我无法生成回复。'
      } catch (llmError) {
        console.error('LLM error:', llmError)
        assistantText = generateStubResponse(routerResult, isYearScope, targetYear)
      }
    } else {
      assistantText = generateStubResponse(routerResult, isYearScope, targetYear)
    }

    timings.llm = Date.now() - llmStart
    contextTrace.run_meta.timing_ms = timings

    // 构建响应（新统一壳）
    return NextResponse.json({
      // ===== 核心字段（前端只读这些）=====
      llm_answer: assistantText,
      context_trace: contextTrace,

      // ===== 兼容旧字段（标记 deprecated，前端禁止读取）=====
      assistant_text: assistantText,
      router_trace: routerResult.trace,
      index: engineData.index,
      facts: engineData.facts,
      
      // facts_trace 标记 deprecated
      facts_trace: {
        deprecated: true,
        _note: '请改用 context_trace.used_blocks.filter(b=>b.kind==="facts")',
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
// 打印层渲染函数（核心：只能用这些函数生成 LLM 上下文）
// ============================================================

/**
 * 渲染大运背景为可读文本
 */
function renderDayunBrief(dayunData: any): string {
  if (!dayunData) return '（暂无大运信息）'
  
  const parts: string[] = []
  
  if (dayunData.current_dayun_ref) {
    const d = dayunData.current_dayun_ref
    parts.push(`当前大运：${d.label || d.name || '未知'}`)
    if (d.start_age !== undefined && d.end_age !== undefined) {
      parts.push(`（${d.start_age}-${d.end_age}岁）`)
    }
    if (d.fortune_label || d.grade) {
      parts.push(`，等级：${d.fortune_label || d.grade}`)
    }
  } else if (dayunData.fortune_label) {
    parts.push(`大运整体评级：${dayunData.fortune_label}`)
  }
  
  return parts.join('') || '（暂无大运信息）'
}

/**
 * 渲染年度详情为可读文本（4段式：总评/为什么/具体表现/建议）
 * 此函数仅在"凶/有变动"年调用，必须说清楚"怎么坏/为什么坏"
 */
function renderYearDetail(liunianData: any, targetYear: number): string {
  if (!liunianData) return `（${targetYear}年暂无详细信息）`
  
  const parts: string[] = []
  
  // === (1) 总评段：凶/有变动 + 是否可克服 ===
  const totalRisk = normalizeRiskPercent(liunianData.total_risk_percent || liunianData.risk_from_gan + liunianData.risk_from_zhi || 0)
  const firstHalf = liunianData.first_half_label || '一般'
  const secondHalf = liunianData.second_half_label || '一般'
  
  let overallCategory = '一般'
  if (totalRisk >= 40) {
    overallCategory = '凶（棘手/意外）'
  } else if (totalRisk >= 25) {
    overallCategory = '明显变动（可克服）'
  } else if (firstHalf === '凶' || secondHalf === '凶') {
    overallCategory = '有凶险'
  } else if (firstHalf.includes('变动') || secondHalf.includes('变动')) {
    overallCategory = '有变动'
  }
  
  parts.push(`【${targetYear}年总评】`)
  parts.push(`流年干支：${liunianData.gan || '?'}${liunianData.zhi || '?'}`)
  parts.push(`整体评估：${overallCategory}`)
  parts.push(`上半年：${firstHalf}，下半年：${secondHalf}`)
  
  // === (2) 为什么段：风险来源 + 关键触发结构 ===
  parts.push('')
  parts.push(`【为什么会这样？】`)
  
  // 风险来源
  const ganRisk = normalizeRiskPercent(liunianData.risk_from_gan)
  const zhiRisk = normalizeRiskPercent(liunianData.risk_from_zhi)
  parts.push(`主要风险来源：天干 ${ganRisk}% / 地支 ${zhiRisk}% / 总体 ${totalRisk}%`)
  
  // 十神角度
  const ganShishen = liunianData.gan_shishen || ''
  const zhiShishen = liunianData.zhi_shishen || ''
  const isGanYongshen = !!liunianData.is_gan_yongshen
  const isZhiYongshen = !!liunianData.is_zhi_yongshen
  const ganLabel = getShishenLabel(ganShishen, isGanYongshen) || ''
  const zhiLabel = getShishenLabel(zhiShishen, isZhiYongshen) || ''
  
  if (ganShishen) {
    parts.push(`天干 ${liunianData.gan}（${ganShishen}）：${isGanYongshen ? '用神得力' : '非用神'}${ganLabel ? '，' + ganLabel : ''}`)
  }
  if (zhiShishen) {
    parts.push(`地支 ${liunianData.zhi}（${zhiShishen}）：${isZhiYongshen ? '用神得力' : '非用神'}${zhiLabel ? '，' + zhiLabel : ''}`)
  }
  
  // 关键触发结构（从 all_events 中挑选冲/刑/害/合会等）
  const keyTriggers: string[] = []
  const allEvents = liunianData.all_events as any[] || []
  const clashesNatal = liunianData.clashes_natal as any[] || []
  const punishmentsNatal = liunianData.punishments_natal as any[] || []
  const patternsLiunian = liunianData.patterns_liunian as any[] || []
  const staticActivation = liunianData.patterns_static_activation as any[] || []
  
  // 冲
  for (const clash of clashesNatal.slice(0, 2)) {
    const from = clash.from_pillar || clash.source_pillar || '流年'
    const target = clash.to_pillar || clash.target_pillar || '命局'
    const branches = clash.branches || [clash.from_branch, clash.to_branch].filter(Boolean)
    keyTriggers.push(`【冲】${branches.join('冲')}（${from}冲${target}）`)
  }
  
  // 刑
  for (const punish of punishmentsNatal.slice(0, 2)) {
    const ptype = punish.type || punish.subtype || '刑'
    const branches = punish.branches || punish.matched_branches || []
    if (branches.length > 0) {
      keyTriggers.push(`【刑】${branches.join('')}${ptype}`)
    }
  }
  
  // 模式（枭神夺食、伤官见官等）
  for (const pat of patternsLiunian.slice(0, 2)) {
    const patType = pat.type || pat.pattern_type || ''
    const label = pat.label || patType
    if (label) {
      keyTriggers.push(`【模式】${label}`)
    }
  }
  
  // 静态激活
  for (const act of staticActivation.slice(0, 2)) {
    const label = act.label || act.type || ''
    if (label) {
      keyTriggers.push(`【激活】${label}`)
    }
  }
  
  // 三合三会逢冲
  const sanheClashBonus = allEvents.find((e: any) => e.type === 'sanhe_sanhui_clash_bonus')
  if (sanheClashBonus) {
    keyTriggers.push(`【三合/三会逢冲】${sanheClashBonus.group_name || ''}额外增${sanheClashBonus.risk_percent || 0}%风险`)
  }
  
  if (keyTriggers.length > 0) {
    parts.push('')
    parts.push('关键触发结构：')
    for (const trigger of keyTriggers.slice(0, 4)) {
      parts.push(`• ${trigger}`)
    }
  } else {
    parts.push('关键触发结构：无显著冲刑害结构，风险主要来自十神非用神或时运波动')
  }
  
  // === (3) 具体表现段：hints/events ===
  parts.push('')
  parts.push(`【具体表现与提示】`)
  
  const hints = liunianData.hints as any[] || []
  const eventsToShow: string[] = []
  
  // 优先显示 hints
  for (const hint of hints) {
    const hintText = typeof hint === 'string' ? hint : (hint.label || hint.text || '')
    if (hintText) {
      eventsToShow.push(hintText)
    }
  }
  
  // 补充 all_events 中有意义的
  for (const evt of allEvents) {
    if (eventsToShow.length >= 5) break
    const evtLabel = evt.label || ''
    const evtType = evt.type || ''
    if (evtLabel && !eventsToShow.includes(evtLabel)) {
      eventsToShow.push(evtLabel)
    } else if (evtType && !eventsToShow.some(e => e.includes(evtType))) {
      // 生成可读描述
      if (evtType === 'clash') {
        eventsToShow.push(`流年与命局发生冲克，易有变动或冲突`)
      } else if (evtType === 'punishment') {
        eventsToShow.push(`刑罚结构出现，注意口舌是非或身体`)
      } else if (evtType.includes('pattern')) {
        eventsToShow.push(`特殊格局触发：${evtType}`)
      }
    }
  }
  
  if (eventsToShow.length > 0) {
    for (const evt of eventsToShow.slice(0, 5)) {
      parts.push(`• ${evt}`)
    }
  } else {
    parts.push('• 今年暂无特定事件提示')
  }
  
  // === (4) 建议段（B口吻，避免命令式） ===
  parts.push('')
  parts.push(`【总体提示】`)
  
  if (totalRisk >= 40) {
    parts.push('今年整体运势较为棘手，容易遇到意外或挑战。建议保持谨慎，稳扎稳打，避免冲动决策。重大事项宜多方考量。')
  } else if (totalRisk >= 25) {
    parts.push('今年有明显变动迹象，但多数情况下可以克服。保持平常心，灵活应对变化，变动未必是坏事。')
  } else if (firstHalf === '凶' || secondHalf === '凶') {
    parts.push(`今年${firstHalf === '凶' ? '上半年' : '下半年'}需要特别注意，其他时段相对平稳。做好准备，平稳过渡。`)
  } else {
    parts.push('今年虽有波动，但整体尚可应对。保持积极心态，关注上述提示点即可。')
  }
  
  return parts.join('\n')
}

/**
 * 渲染最近5年紧凑版 facts 文本
 * 格式：每年两行（天干行 + 地支行），包含：十神/用神/标签/风险%
 * 必须输出十神标签（从 SHISHEN_LABEL_MAP 获取）
 */
function renderFactsLast5Compact(facts: Record<string, unknown>, years: number[]): { linesText: string; liuniansUsed: any[] } {
  const luck = facts?.luck as { groups?: any[] } | undefined
  if (!luck?.groups) return { linesText: '', liuniansUsed: [] }
  
  const lines: string[] = []
  const liuniansUsed: any[] = []
  
  for (const year of years) {
    // 在所有 groups 中找到该年的 liunian
    let liunianData: any = null
    for (const group of luck.groups) {
      const liunianList = group?.liunian as any[] | undefined
      if (liunianList) {
        liunianData = liunianList.find((ln: any) => ln.year === year)
        if (liunianData) break
      }
    }
    
    if (!liunianData) continue
    liuniansUsed.push(liunianData)
    
    // 风险百分比规范化
    const ganRisk = normalizeRiskPercent(liunianData.risk_from_gan)
    const zhiRisk = normalizeRiskPercent(liunianData.risk_from_zhi)
    
    // 获取十神标签（从词库映射）
    const ganShishen = liunianData.gan_shishen || ''
    const zhiShishen = liunianData.zhi_shishen || ''
    const isGanYongshen = !!liunianData.is_gan_yongshen
    const isZhiYongshen = !!liunianData.is_zhi_yongshen
    const ganLabel = getShishenLabel(ganShishen, isGanYongshen) || ganShishen || '未知'
    const zhiLabel = getShishenLabel(zhiShishen, isZhiYongshen) || zhiShishen || '未知'
    
    // 天干行
    const ganLine = `${year}年：天干 ${liunianData.gan || '?'}｜十神 ${ganShishen || '未知'}｜用神 ${isGanYongshen ? '是' : '否'}｜标签：${ganLabel}｜上半年危险系数：${ganRisk}%`
    
    // 地支行
    const zhiLine = `        地支 ${liunianData.zhi || '?'}｜十神 ${zhiShishen || '未知'}｜用神 ${isZhiYongshen ? '是' : '否'}｜标签：${zhiLabel}｜下半年危险系数：${zhiRisk}%`
    
    lines.push(ganLine)
    lines.push(zhiLine)
  }
  
  return { linesText: lines.join('\n'), liuniansUsed }
}

function getFixedLast5Years(baseYear: number): number[] {
  const start = baseYear - 4
  const years: number[] = []
  for (let y = start; y <= baseYear; y++) {
    years.push(y)
  }
  return years // 升序（旧->新）
}

function normalizeRiskPercent(val: any): number {
  const num = typeof val === 'number' ? val : 0
  // 如果是小数概率，乘100；如果本身>1，按百分比处理
  const pct = num > 1 ? num : num * 100
  const clamped = Math.max(0, Math.min(100, pct))
  return Number.isFinite(clamped) ? Math.round(clamped) : 0
}

/**
 * 判断年份是否为"凶/有变动"需要下钻
 * 检查逻辑：
 * 1. year_category/first_half_label/second_half_label 字段
 * 2. 如果字段不存在，根据风险百分比判断：总风险 >= 25 视为"有变动"，>= 40 视为"凶"
 */
function isRiskyYear(liunian: any): boolean {
  // 1. 检查明确的分类标签
  const cats = new Set<string>()
  if (liunian.year_category) cats.add(liunian.year_category)
  if (liunian.first_half_label) cats.add(liunian.first_half_label)
  if (liunian.second_half_label) cats.add(liunian.second_half_label)
  
  if (['凶', '有变动', '变动'].some(c => cats.has(c))) {
    return true
  }
  
  // 2. 如果没有明确标签，根据风险百分比判断
  const ganRisk = typeof liunian.risk_from_gan === 'number' ? liunian.risk_from_gan : 0
  const zhiRisk = typeof liunian.risk_from_zhi === 'number' ? liunian.risk_from_zhi : 0
  const totalRisk = ganRisk + zhiRisk
  
  // 总风险 >= 25 视为"有变动"，需要下钻
  if (totalRisk >= 25) {
    return true
  }
  
  return false
}

// ============================================================
// Helper Functions
// ============================================================

function getSystemPrompt(flags: { need_dayun_mention: boolean; dayun_grade_public: '好' | '一般' }): string {
  let prompt = `你是一位专业的命理分析师，基于用户的八字信息提供运势解读。

规则：
1. 使用温和、积极的语气，即使运势不佳也要给出建议
2. 回答要简洁明了，控制在200-300字
3. 结合用户的具体问题进行回答
4. 不要透露技术细节或提及"index"、"trace"等术语`

  if (flags.need_dayun_mention) {
    prompt += `
5. 需要提及大运情况，大运评级为"${flags.dayun_grade_public}"`
  }

  return prompt
}

function getYearDetailSystemPrompt(targetYear: number): string {
  return `你是一位专业的命理分析师，基于用户的八字信息提供${targetYear}年的运势解读。

规则：
1. 使用温和、积极的语气
2. 回答要简洁明了，控制在200-300字
3. 严格按照提供的年度详情信息回答
4. 如果"提示汇总"为空，写"今年暂无额外提示汇总"
5. 不要透露技术细节或提及"index"、"trace"等术语
6. 危险系数为0时，写"不易出现意外和风险"`
}

function generateStubResponse(routerResult: RouterResult, isYearScope: boolean, targetYear?: number): string {
  if (isYearScope && targetYear) {
    return `根据您的八字分析，${targetYear}年整体运势平稳。建议保持积极的心态，抓住机遇。今年暂无额外提示汇总。`
  }
  
  return '根据您的八字分析，最近几年整体运势保持平稳。建议稳扎稳打，把握好眼前的机会。'
}

function getStubEngineData(birth_date: string, birth_time: string, is_male: boolean) {
  return {
    index: {
      meta: { base_year: new Date().getFullYear() },
      dayun: {
        current_dayun_ref: { label: '壬午', fortune_label: '一般' },
        fortune_label: '一般',
      },
      year_grade: {
        last5: [
          { year: 2026, Y: 10.0, year_label: '上半年 一般，下半年 一般' },
          { year: 2025, Y: 15.0, year_label: '上半年 一般，下半年 好运' },
        ],
      },
      relationship: { hit: false, years_hit: [] },
      turning_points: { nearby: [], should_mention: false },
      good_year_search: { has_good_in_future3: false, future3_good_years: [] },
    },
    facts: {
      luck: {
        groups: [
          {
            dayun: { label: '壬午', start_year: 2020, end_year: 2030 },
            liunian: [
              { year: 2026, gan: '丙', zhi: '午', first_half_label: '一般', second_half_label: '一般' },
              { year: 2025, gan: '乙', zhi: '巳', first_half_label: '一般', second_half_label: '好运' },
            ],
          },
        ],
      },
    },
    findings: { facts: [], hints: [], links: [] },
  }
}
