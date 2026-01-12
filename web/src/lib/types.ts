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
    facts_used: unknown[]
    facts_available_count: number
    facts_source: string
  }
  llm_meta: {
    model: string
    tokens: number
    latency_ms: number
  }
  created_at: string
}

/**
 * API types
 */

export interface ChatRequest {
  session_id: string
  message: string
}

export interface ChatResponse {
  assistant_text: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  router_trace: any
  modules_trace: unknown[]
  index_trace: {
    slices_used: string[]
    slices_payload: Record<string, unknown>
  }
  facts_trace: {
    facts_used: unknown[]
    facts_available_count: number
    facts_source: string
  }
  run_meta: {
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

