/**
 * facts selection helpers
 *
 * Contract:
 * - facts is the ONLY truth source for factual content.
 * - index can be used for decide/navigation, but NOT as fact content.
 * - selection must return reproducible paths into facts.
 */

export type SelectedFactsResult = {
  selected_facts: Record<string, unknown>
  selected_facts_paths: string[]
  selected_facts_previews: Array<{
    path: string
    preview: string
    length_chars: number
  }>
}

function previewText(value: unknown, maxChars: number = 300): { preview: string; length_chars: number } {
  const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
  return { preview: text.slice(0, maxChars), length_chars: text.length }
}

/**
 * Select year detail facts: dayun (parent group) + liunian(year)
 */
export function selectFactsForYear(facts: Record<string, unknown>, year: number): SelectedFactsResult {
  const selected: Record<string, unknown> = {}
  const paths: string[] = []
  const previews: SelectedFactsResult['selected_facts_previews'] = []

  const luck = (facts as any)?.luck
  const groups: any[] = luck?.groups || []

  for (let gi = 0; gi < groups.length; gi++) {
    const g = groups[gi]
    const liunianList: any[] = g?.liunian || []
    for (let li = 0; li < liunianList.length; li++) {
      const ln = liunianList[li]
      if (ln?.year === year) {
        // dayun
        const dayunPath = `facts.luck.groups[${gi}].dayun`
        selected.dayun = g?.dayun ?? null
        paths.push(dayunPath)
        previews.push({ path: dayunPath, ...previewText(selected.dayun) })

        // liunian
        const liunianPath = `facts.luck.groups[${gi}].liunian[${li}] (year=${year})`
        selected.liunian = ln
        paths.push(liunianPath)
        previews.push({ path: liunianPath, ...previewText(selected.liunian) })

        return { selected_facts: selected, selected_facts_paths: paths, selected_facts_previews: previews }
      }
    }
  }

  // not found
  const missPath = `facts.luck.groups[*].liunian[*] (year=${year})`
  paths.push(missPath)
  previews.push({ path: missPath, preview: '', length_chars: 0 })
  selected.liunian = null
  selected.dayun = null
  return { selected_facts: selected, selected_facts_paths: paths, selected_facts_previews: previews }
}

/**
 * Select range facts: liunian entries within last N years (relative to baseYear)
 */
export function selectFactsForRange(
  facts: Record<string, unknown>,
  years: number,
  baseYear: number
): SelectedFactsResult {
  const selected: Record<string, unknown> = { liunian: [] as any[] }
  const paths: string[] = []
  const previews: SelectedFactsResult['selected_facts_previews'] = []

  const allowedYears = new Set<number>()
  for (let i = 0; i < years; i++) allowedYears.add(baseYear - i)

  const luck = (facts as any)?.luck
  const groups: any[] = luck?.groups || []

  for (let gi = 0; gi < groups.length; gi++) {
    const g = groups[gi]
    const liunianList: any[] = g?.liunian || []
    for (let li = 0; li < liunianList.length; li++) {
      const ln = liunianList[li]
      const y = ln?.year
      if (typeof y === 'number' && allowedYears.has(y)) {
        ;(selected.liunian as any[]).push(ln)
        const p = `facts.luck.groups[${gi}].liunian[${li}] (year=${y})`
        paths.push(p)
      }
    }
  }

  previews.push({
    path: `facts.luck.groups[*].liunian[*] (years=${years}, baseYear=${baseYear})`,
    ...previewText(selected.liunian),
  })

  return { selected_facts: selected, selected_facts_paths: paths, selected_facts_previews: previews }
}


