/**
 * Router v1 - 主路由逻辑
 * if/else 规则路由 + normalization
 */

import { normalize, parseYear, parseRangeYears } from './normalize'

// ============================================================
// Types
// ============================================================

export type TimeScope = 
  | { type: 'year'; year: number }
  | { type: 'range'; years: number }

export type Focus = 'relationship' | 'wealth' | 'career' | 'general'

export type Intent = 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G'
// A: 整体概述（范围）
// B: 范围查询（特定领域）
// C: 点名年份
// D: 感情相关
// E: 财运相关
// F: 事业相关
// G: 其他

export interface RouterFlags {
  need_dayun_mention: boolean
  dayun_grade_public: '好' | '一般'
}

export interface RouterTrace {
  routers_called: string[]
  intent: Intent
  time_scope: TimeScope
  focus: Focus
  rules_matched: string[]
  flags: RouterFlags
  degrade: string[]
  index_slices_used: string[]
  normalized_query: string
}

export interface RouterResult {
  trace: RouterTrace
  slices: string[]
}

// ============================================================
// Focus Detection (多语言词表)
// ============================================================

const RELATIONSHIP_KEYWORDS = [
  // 中文
  '感情', '恋爱', '婚姻', '对象', '桃花', '分手', '复合', '结婚',
  '老婆', '老公', '男朋友', '女朋友', '另一半', '伴侣', '恋情',
  '脱单', '单身', '暧昧', '相亲', '约会', '爱情',
  // 英文
  'relationship', 'dating', 'marriage', 'love', 'partner', 'boyfriend', 
  'girlfriend', 'spouse', 'wedding', 'romance', 'romantic',
]

const WEALTH_KEYWORDS = [
  // 中文
  '财运', '钱', '财富', '挣钱', '收入', '破财', '投资', '理财',
  '赚钱', '发财', '财务', '工资', '薪水', '存款', '股票', '基金',
  // 英文
  'money', 'wealth', 'income', 'invest', 'investment', 'finance', 
  'financial', 'salary', 'rich', 'fortune',
]

const CAREER_KEYWORDS = [
  // 中文
  '事业', '工作', '学业', '考试', 'offer', '实习', '升学', '升职',
  '跳槽', '离职', '创业', '公司', '职业', '职场', '面试', '考研',
  '高考', '学习', '读书', '毕业', '就业',
  // 英文
  'job', 'career', 'study', 'school', 'exam', 'work', 'business',
  'promotion', 'interview', 'graduation', 'employment',
]

const RANGE_KEYWORDS = [
  // 中文
  '最近', '这几年', '近几年', '过去', '近五年', '近三年', '几年',
  '这段时间', '近期', '未来', '之后', '以后',
  // 英文
  'recent', 'lately', 'last few years', 'past years', 'future',
]

/**
 * 提取用户关注的领域
 */
export function extractFocus(text: string): Focus {
  const normalized = normalize(text)

  // 优先级：relationship > wealth > career > general
  for (const keyword of RELATIONSHIP_KEYWORDS) {
    if (normalized.includes(keyword.toLowerCase())) {
      return 'relationship'
    }
  }

  for (const keyword of WEALTH_KEYWORDS) {
    if (normalized.includes(keyword.toLowerCase())) {
      return 'wealth'
    }
  }

  for (const keyword of CAREER_KEYWORDS) {
    if (normalized.includes(keyword.toLowerCase())) {
      return 'career'
    }
  }

  return 'general'
}

/**
 * 提取时间范围
 */
export function extractTimeScope(text: string): TimeScope {
  const normalized = normalize(text)

  // 1. 尝试解析具体年份
  const year = parseYear(normalized)
  if (year !== null) {
    return { type: 'year', year }
  }

  // 2. 尝试解析范围
  const rangeYears = parseRangeYears(normalized)
  if (rangeYears !== null) {
    return { type: 'range', years: rangeYears }
  }

  // 3. 检查是否有范围关键词
  for (const keyword of RANGE_KEYWORDS) {
    if (normalized.includes(keyword.toLowerCase())) {
      return { type: 'range', years: 5 }
    }
  }

  // 4. 默认：范围5年
  return { type: 'range', years: 5 }
}

// ============================================================
// 主路由决策
// ============================================================

/**
 * Router v1 主函数
 * @param query 用户原话
 * @param dayunGrade 大运评级（从 index 获取）
 */
export function route(
  query: string,
  dayunGrade: '好运' | '一般' | '坏运' = '一般'
): RouterResult {
  const normalizedQuery = normalize(query)
  const timeScope = extractTimeScope(query)
  const focus = extractFocus(query)

  const rulesMatched: string[] = []
  const degrade: string[] = []
  let slices: string[] = []
  let intent: Intent = 'A'

  // 大运对外展示：不佳统一映射成"一般"
  const dayunGradePublic: '好' | '一般' = dayunGrade === '好运' ? '好' : '一般'

  // ============================================================
  // 硬规则判定
  // ============================================================

  if (timeScope.type === 'year') {
    // 硬规则 1：点名某一年
    rulesMatched.push('rule1_year_scope')
    intent = 'C'

    // 必须包含 year_grade
    slices.push('year_grade')

    if (focus === 'relationship') {
      // 感情：只带 relationship
      rulesMatched.push('rule4_relationship_no_dayun')
      slices.push('relationship')
    } else {
      // 非感情：带 dayun + turning_points + good_year_search
      slices.push('dayun')
      slices.push('turning_points')
      slices.push('good_year_search')
    }
  } else {
    // 硬规则 2/3：范围（默认5年）
    rulesMatched.push('rule2_range_scope')
    intent = 'B'

    if (focus === 'relationship') {
      // 硬规则 4：感情不看大运
      rulesMatched.push('rule4_relationship_no_dayun')
      slices.push('relationship')
      intent = 'D'
    } else {
      // general/career/wealth：返回所有
      slices.push('year_grade')
      slices.push('good_year_search')
      slices.push('dayun')
      slices.push('turning_points')

      // 根据 focus 设置 intent
      if (focus === 'wealth') intent = 'E'
      else if (focus === 'career') intent = 'F'
      else intent = 'A'
    }
  }

  // 确定是否需要提到大运
  const needDayunMention = slices.includes('dayun')

  // 构建 trace
  const trace: RouterTrace = {
    routers_called: ['main_router_v1'],
    intent,
    time_scope: timeScope,
    focus,
    rules_matched: rulesMatched,
    flags: {
      need_dayun_mention: needDayunMention,
      dayun_grade_public: dayunGradePublic,
    },
    degrade,
    index_slices_used: slices,
    normalized_query: normalizedQuery,
  }

  return { trace, slices }
}

