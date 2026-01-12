import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { route } from '@/lib/router'
import type { ChatResponse, Profile } from '@/lib/types'
import OpenAI from 'openai'

// 检查 OpenAI API Key
const OPENAI_API_KEY = process.env.OPENAI_API_KEY
if (!OPENAI_API_KEY) {
  console.error('❌ OPENAI_API_KEY is not set')
}

const openai = OPENAI_API_KEY ? new OpenAI({ apiKey: OPENAI_API_KEY }) : null

// Python Engine URL
const PYTHON_ENGINE_URL = process.env.PYTHON_ENGINE_URL || 'http://localhost:5000'

/**
 * POST /api/chat
 * 处理聊天请求
 */
export async function POST(request: NextRequest) {
  const startTime = Date.now()
  const timings = { router: 0, engine: 0, llm: 0 }

  try {
    // 1. 验证用户登录
    const supabase = await createClient()
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // 2. 解析请求
    const body = await request.json()
    const { session_id, message } = body

    if (!session_id || !message) {
      return NextResponse.json({ error: 'Missing session_id or message' }, { status: 400 })
    }

    // 3. 获取 Session 和 Profile
    const { data: session, error: sessionError } = await supabase
      .from('sessions')
      .select('*, profiles(*)')
      .eq('id', session_id)
      .single()

    if (sessionError || !session) {
      return NextResponse.json({ error: 'Session not found' }, { status: 404 })
    }

    const profile = session.profiles as Profile

    // 4. 保存用户消息
    const { data: userMessage, error: userMsgError } = await supabase
      .from('messages')
      .insert({
        session_id,
        role: 'user',
        content: message,
      })
      .select()
      .single()

    if (userMsgError) {
      console.error('Error saving user message:', userMsgError)
    }

    // 5. 调用 Python Engine 获取 index/facts
    const routerStart = Date.now()
    
    let engineData: { index: Record<string, unknown>; facts: Record<string, unknown> } | null = null
    
    try {
      const engineResponse = await fetch(`${PYTHON_ENGINE_URL}/v1/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          birth_date: profile.birth_date,
          birth_time: profile.birth_time,
          is_male: profile.is_male,
          base_year: new Date().getFullYear(),
        }),
      })

      if (engineResponse.ok) {
        engineData = await engineResponse.json()
      }
    } catch (err) {
      console.warn('Python engine not available, using stub data:', err)
    }

    // 如果 engine 不可用，使用 stub 数据
    if (!engineData) {
      engineData = getStubEngineData()
    }

    timings.engine = Date.now() - routerStart

    // 6. 运行 Router
    const routerStartTime = Date.now()
    const dayunGrade = (engineData.index as { dayun?: { fortune_label?: string } })?.dayun?.fortune_label as '好运' | '一般' | '坏运' || '一般'
    const routerResult = route(message, dayunGrade)
    timings.router = Date.now() - routerStartTime

    // 7. 提取 index slices
    const indexSlices: Record<string, unknown> = {}
    for (const slice of routerResult.slices) {
      if (slice in (engineData.index as Record<string, unknown>)) {
        indexSlices[slice] = (engineData.index as Record<string, unknown>)[slice]
      }
    }

    // 8. 提取 facts（简化版，取 topK）
    const factsUsed: unknown[] = []
    const factsAvailableCount = Object.keys(engineData.facts || {}).length

    // 9. 构建 LLM Context
    const llmContext = buildLLMContext(message, routerResult, indexSlices, profile)

    // 10. 调用 LLM
    let assistantText = ''
    const llmStart = Date.now()

    if (openai) {
      try {
        const completion = await openai.chat.completions.create({
          model: 'gpt-4o-mini',
          messages: [
            {
              role: 'system',
              content: getSystemPrompt(routerResult.trace.flags),
            },
            {
              role: 'user',
              content: llmContext,
            },
          ],
          temperature: 0.7,
          max_tokens: 1000,
        })

        assistantText = completion.choices[0]?.message?.content || '抱歉，我无法生成回复。'
      } catch (llmError) {
        console.error('LLM error:', llmError)
        assistantText = '抱歉，AI 服务暂时不可用，请稍后再试。'
      }
    } else {
      // 无 OpenAI Key，使用 stub 回复
      assistantText = generateStubResponse(routerResult, indexSlices)
    }

    timings.llm = Date.now() - llmStart

    // 11. 保存 assistant 消息
    const { data: assistantMessage, error: assistantMsgError } = await supabase
      .from('messages')
      .insert({
        session_id,
        role: 'assistant',
        content: assistantText,
      })
      .select()
      .single()

    // 12. 保存 Run（debug 信息）
    if (assistantMessage) {
      const { error: runError } = await supabase
        .from('runs')
        .insert({
          message_id: assistantMessage.id,
          router_trace: routerResult.trace,
          modules_trace: buildModulesTrace(routerResult.slices),
          index_trace: {
            slices_used: routerResult.slices,
            slices_payload: indexSlices,
          },
          facts_trace: {
            facts_used: factsUsed,
            facts_available_count: factsAvailableCount,
            facts_source: 'engine_facts',
          },
          llm_meta: {
            model: 'gpt-4o-mini',
            tokens: 0, // TODO: 从 completion 获取
            latency_ms: timings.llm,
          },
        })

      if (runError) {
        console.error('Error saving run:', runError)
      }
    }

    // 13. 构建响应
    const response: ChatResponse = {
      assistant_text: assistantText,
      router_trace: routerResult.trace,
      modules_trace: buildModulesTrace(routerResult.slices),
      index_trace: {
        slices_used: routerResult.slices,
        slices_payload: indexSlices,
      },
      facts_trace: {
        facts_used: factsUsed,
        facts_available_count: factsAvailableCount,
        facts_source: 'engine_facts',
      },
      run_meta: {
        git_sha: process.env.VERCEL_GIT_COMMIT_SHA || 'local',
        timing_ms: timings,
      },
    }

    return NextResponse.json(response)

  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
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

function buildLLMContext(
  query: string,
  routerResult: { trace: { time_scope: { type: string; year?: number; years?: number }; focus: string } },
  indexSlices: Record<string, unknown>,
  profile: Profile
): string {
  let context = `用户问题：${query}\n\n`
  context += `用户信息：${profile.is_male ? '男性' : '女性'}，出生于 ${profile.birth_date} ${profile.birth_time}\n\n`

  const { time_scope, focus } = routerResult.trace

  if (time_scope.type === 'year' && time_scope.year) {
    context += `时间范围：${time_scope.year}年\n`
  } else if (time_scope.type === 'range' && time_scope.years) {
    context += `时间范围：最近${time_scope.years}年\n`
  }

  context += `关注领域：${focus}\n\n`
  context += `参考数据：\n${JSON.stringify(indexSlices, null, 2)}`

  return context
}

function buildModulesTrace(slices: string[]): unknown[] {
  return slices.map(slice => ({
    module: `${slice.toUpperCase()}_BLOCK`,
    source: 'index',
    used: true,
  }))
}

function getStubEngineData() {
  return {
    index: {
      meta: { base_year: new Date().getFullYear() },
      dayun: {
        current_dayun_ref: { label: '壬午', fortune_label: '一般' },
        fortune_label: '一般',
      },
      year_grade: {
        last5: [
          { year: 2025, Y: 15.0, year_label: '上半年 一般，下半年 好运' },
          { year: 2024, Y: 8.0, year_label: '上半年 好运，下半年 一般' },
        ],
      },
      relationship: {
        hit: true,
        years_hit: [2024, 2025],
      },
      turning_points: { nearby: [], should_mention: false },
      good_year_search: { has_good_in_future3: true, future3_good_years: [2025] },
    },
    facts: {},
  }
}

function generateStubResponse(
  routerResult: { trace: { focus: string; time_scope: { type: string; year?: number } } },
  indexSlices: Record<string, unknown>
): string {
  const { focus, time_scope } = routerResult.trace

  if (focus === 'relationship') {
    return '根据您的八字分析，最近几年在感情方面会有一些变化。建议保持开放的心态，注意与伴侣的沟通。感情运势整体平稳，适合稳步发展关系。'
  }

  if (time_scope.type === 'year' && time_scope.year) {
    return `根据您的八字分析，${time_scope.year}年整体运势平稳。上半年可能会有一些小的波动，但下半年会趋于稳定。建议保持积极的心态，抓住机遇。`
  }

  return '根据您的八字分析，最近几年整体运势保持平稳。大运整体评级为一般，建议稳扎稳打，把握好眼前的机会。在事业和生活中保持平和心态，会有不错的发展。'
}

