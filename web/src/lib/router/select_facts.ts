/**
 * Router Select stage (facts-only)
 *
 * Contract:
 * - decide() uses (user_query + index) only.
 * - select() uses (facts + decide_result) only.
 */

import type { RouterTrace } from './router'
import { selectFactsForRange, selectFactsForYear } from '@/lib/facts/select'

export function selectFromFacts(
  facts: Record<string, unknown>,
  trace: RouterTrace,
  baseYear: number
): {
  selected_facts: Record<string, unknown>
  selected_facts_paths: string[]
  selected_facts_previews: Array<{ path: string; preview: string; length_chars: number }>
} {
  if (trace.time_scope.type === 'year') {
    return selectFactsForYear(facts, trace.time_scope.year)
  }
  if (trace.time_scope.type === 'range') {
    return selectFactsForRange(facts, trace.time_scope.years, baseYear)
  }
  // fallback (shouldn't happen)
  return { selected_facts: {}, selected_facts_paths: [], selected_facts_previews: [] }
}


