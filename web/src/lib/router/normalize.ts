/**
 * Router v1 - Normalization utilities
 * 处理全角→半角、大小写统一、中英文年份解析等
 */

// 中文数字映射
const CHINESE_DIGITS: Record<string, string> = {
  '零': '0', '〇': '0', '一': '1', '二': '2', '三': '3',
  '四': '4', '五': '5', '六': '6', '七': '7', '八': '8', '九': '9',
  '十': '', '百': '', '千': '', '万': '',
}

// 全角→半角映射
const FULLWIDTH_TO_HALFWIDTH: Record<string, string> = {
  '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
  '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
  'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E',
  'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J',
  // ... 可以继续添加
}

/**
 * 基础文本规范化
 * - 全角→半角
 * - 大小写统一（小写）
 * - 去掉多余空白
 */
export function normalize(text: string): string {
  let result = text

  // 全角→半角
  result = result.split('').map(char => FULLWIDTH_TO_HALFWIDTH[char] || char).join('')

  // 小写
  result = result.toLowerCase()

  // 去掉多余空白
  result = result.replace(/\s+/g, ' ').trim()

  return result
}

/**
 * 将中文年份转换为数字年份
 * 例如：二零二六 → 2026，二〇二六 → 2026
 */
export function parseChineseYear(text: string): number | null {
  // 匹配四位中文数字年份：二零二六/二〇二六
  const fourDigitPattern = /([零〇一二三四五六七八九]{4})/g
  const match = text.match(fourDigitPattern)
  if (match) {
    const digits = match[0].split('').map(c => CHINESE_DIGITS[c] || c).join('')
    const year = parseInt(digits, 10)
    if (year >= 1900 && year <= 2100) return year
  }

  // 匹配两位中文数字：二六年 → 26 → 2026
  const twoDigitPattern = /([零〇一二三四五六七八九]{2})年/
  const twoMatch = text.match(twoDigitPattern)
  if (twoMatch) {
    const digits = twoMatch[1].split('').map(c => CHINESE_DIGITS[c] || c).join('')
    const shortYear = parseInt(digits, 10)
    if (shortYear >= 0 && shortYear <= 99) {
      return shortYear >= 50 ? 1900 + shortYear : 2000 + shortYear
    }
  }

  return null
}

/**
 * 解析年份（支持多种格式）
 * - 2026, 2026年
 * - 26年, 26
 * - 二零二六, 二〇二六
 * - 二六年
 */
export function parseYear(text: string): number | null {
  const currentYear = new Date().getFullYear()

  // 1. 相对年份
  if (/今年|this\s*year|current\s*year/i.test(text)) return currentYear
  if (/明年|next\s*year/i.test(text)) return currentYear + 1
  if (/去年|last\s*year/i.test(text)) return currentYear - 1
  if (/前年/i.test(text)) return currentYear - 2
  if (/后年|大后年/i.test(text)) return currentYear + 2

  // 2. 四位数字年份：2026, 2026年
  const fourDigitMatch = text.match(/\b(19\d{2}|20\d{2})\b年?/)
  if (fourDigitMatch) return parseInt(fourDigitMatch[1], 10)

  // 3. 两位数字年份：26年
  const twoDigitMatch = text.match(/\b(\d{2})年/)
  if (twoDigitMatch) {
    const shortYear = parseInt(twoDigitMatch[1], 10)
    return shortYear >= 50 ? 1900 + shortYear : 2000 + shortYear
  }

  // 4. 中文年份
  const chineseYear = parseChineseYear(text)
  if (chineseYear) return chineseYear

  return null
}

/**
 * 解析范围年份数量
 * 例如：最近五年 → 5，近三年 → 3
 */
export function parseRangeYears(text: string): number | null {
  // 中文数字
  const chineseRangeMap: Record<string, number> = {
    '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
  }

  // 匹配：最近/近/过去 + 数字 + 年
  const patterns = [
    /(?:最近|近|过去|这|last|past|recent)\s*([一二两三四五六七八九十\d]+)\s*年/i,
    /([一二两三四五六七八九十\d]+)\s*年(?:内|来|以来)/i,
  ]

  for (const pattern of patterns) {
    const match = text.match(pattern)
    if (match) {
      const numStr = match[1]
      // 尝试解析中文数字
      if (chineseRangeMap[numStr]) return chineseRangeMap[numStr]
      // 尝试解析阿拉伯数字
      const num = parseInt(numStr, 10)
      if (!isNaN(num) && num >= 1 && num <= 20) return num
    }
  }

  // 英文匹配：last few years, past 5 years
  const englishMatch = text.match(/(?:last|past|recent)\s*(\d+)?\s*(?:few)?\s*years?/i)
  if (englishMatch) {
    if (englishMatch[1]) return parseInt(englishMatch[1], 10)
    return 5 // "few years" 默认 5
  }

  return null
}

