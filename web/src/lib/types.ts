/**
 * Database types for Supabase tables
 */

export interface Profile {
  id: string
  user_id: string
  display_name: string
  birth_date: string // YYYY-MM-DD
  birth_time: string // HH:mm
  timezone: string
  location: string | null
  is_male: boolean
  created_at: string
}

export interface Session {
  id: string
  profile_id: string
  title: string | null
  created_at: string
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Run {
  id: string
  message_id: string
  router_trace: Record<string, unknown>
  modules_trace: unknown[]
  index_trace: {
    slices_used: string[]
    slices_payload: Record<string, unknown>
  }
  facts_trace: {
    deprecated?: boolean
    facts_used?: unknown[]
    facts_available_count?: number
    facts_source?: string
  }
  llm_meta: {
    model: string
    tokens: number
    latency_ms: number
    context_trace?: ContextTrace
  }
  created_at: string
}

/**
 * Context Trace Types（权威的 LLM 上下文回放）
 */

export interface ContextBlock {
  kind: 'facts' | 'index' | 'other'
  block_type: string
  block_id: string
  used: boolean
  source: 'engine' | 'index' | 'stub'
  chars_total: number
  preview: string
  full_text?: string
  year?: number
  reason?: string
}

export interface RouterMeta {
  router_id: string
  intent: string
  mode: 'year' | 'range' | 'general'
  reason: string
  child_router?: RouterMeta | null
}

export interface ContextTrace {
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

/**
 * API types
 */

export interface ChatRequest {
  session_id: string
  message: string
}

export interface ChatResponse {
  // 新统一壳（前端只读这些）
  llm_answer: string
  context_trace: ContextTrace

  // 兼容旧字段（deprecated，前端禁止读取展示）
  assistant_text?: string
  router_trace?: Record<string, unknown>
  modules_trace?: unknown[]
  index_trace?: {
    slices_used: string[]
    slices_payload: Record<string, unknown>
  }
  facts_trace?: {
    deprecated?: boolean
  }
  run_meta?: {
    git_sha: string
    timing_ms: {
      router: number
      engine: number
      llm: number
    }
  }
}

/**
 * Python Engine types
 */

export interface EngineRequest {
  birth_date: string // YYYY-MM-DD
  birth_time: string // HH:mm
  is_male: boolean
  base_year: number
}

export interface EngineResponse {
  index: Record<string, unknown>
  facts: Record<string, unknown>
  findings?: Record<string, unknown>
  error?: string
}
