'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

// ============================================================
// Types（新统一结构 - 只用 context_trace）
// ============================================================

interface Profile {
  id: string
  name: string
  birth_date: string
  birth_time: string
  is_male: boolean
  created_at: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  debug?: DebugData
  created_at: string
}

// Context Block（LLM 吃到的单个块）
interface ContextBlock {
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

// Router 元数据
interface RouterMeta {
  router_id: string
  intent: string
  mode: 'year' | 'range' | 'general'
  reason: string
  child_router?: RouterMeta | null
}

// LLM Context Full（完整 LLM 输入追溯）
interface LLMContextPart {
  part_id: number
  role: 'system' | 'separator' | 'facts' | 'user' | 'other'
  block_id?: string
  block_type?: string
  year?: number
  reason?: string
  start_char: number
  end_char: number
  chars_total: number
  preview: string
}

interface LLMContextFull {
  full_text: string
  full_text_preview: string
  full_text_sha256: string
  parts: LLMContextPart[]
  token_est: number
  was_truncated: boolean
  drilldown_summary?: {
    risky_years_detected: number[]
    year_detail_blocks_added: string[]
    drilldown_triggered: boolean
  }
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
  context?: LLMContextFull  // 完整 LLM 输入
}

// Debug Data（前端只读 context_trace）
interface DebugData {
  context_trace: ContextTrace
  // 兼容字段（deprecated，禁止读取展示）
  router_trace?: Record<string, unknown>
  index?: Record<string, unknown>
  facts?: Record<string, unknown>
}

interface ChatHistory {
  profile_id: string
  messages: Message[]
}

// ============================================================
// LocalStorage helpers
// ============================================================

const PROFILES_KEY = 'hayyy_profiles'
const CHATS_KEY = 'hayyy_chats'

function loadProfiles(): Profile[] {
  if (typeof window === 'undefined') return []
  const data = localStorage.getItem(PROFILES_KEY)
  return data ? JSON.parse(data) : []
}

function saveProfiles(profiles: Profile[]) {
  localStorage.setItem(PROFILES_KEY, JSON.stringify(profiles))
}

function loadChats(): Record<string, Message[]> {
  if (typeof window === 'undefined') return {}
  const data = localStorage.getItem(CHATS_KEY)
  return data ? JSON.parse(data) : {}
}

function saveChats(chats: Record<string, Message[]>) {
  localStorage.setItem(CHATS_KEY, JSON.stringify(chats))
}

// ============================================================
// Main Component
// ============================================================

export default function TestPage() {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // State
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null)
  const [chats, setChats] = useState<Record<string, Message[]>>({})
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // New profile form
  const [showNewProfile, setShowNewProfile] = useState(false)
  const [newProfileForm, setNewProfileForm] = useState({
    name: '',
    birth_date: '',
    birth_time: '',
    is_male: true,
  })

  // Load from localStorage on mount
  useEffect(() => {
    setProfiles(loadProfiles())
    setChats(loadChats())
  }, [])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chats, selectedProfile])

  // Get current messages
  const currentMessages = selectedProfile ? (chats[selectedProfile.id] || []) : []

  // Create new profile
  const handleCreateProfile = () => {
    if (!newProfileForm.name || !newProfileForm.birth_date || !newProfileForm.birth_time) {
      alert('请填写完整信息')
      return
    }

    const newProfile: Profile = {
      id: `profile_${Date.now()}`,
      name: newProfileForm.name,
      birth_date: newProfileForm.birth_date,
      birth_time: newProfileForm.birth_time,
      is_male: newProfileForm.is_male,
      created_at: new Date().toISOString(),
    }

    const updatedProfiles = [...profiles, newProfile]
    setProfiles(updatedProfiles)
    saveProfiles(updatedProfiles)
    setSelectedProfile(newProfile)
    setShowNewProfile(false)
    setNewProfileForm({ name: '', birth_date: '', birth_time: '', is_male: true })
  }

  // Delete profile
  const handleDeleteProfile = (profileId: string) => {
    const updatedProfiles = profiles.filter(p => p.id !== profileId)
    setProfiles(updatedProfiles)
    saveProfiles(updatedProfiles)

    const updatedChats = { ...chats }
    delete updatedChats[profileId]
    setChats(updatedChats)
    saveChats(updatedChats)

    if (selectedProfile?.id === profileId) {
      setSelectedProfile(null)
    }
  }

  // Send message
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedProfile || isLoading) return

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      created_at: new Date().toISOString(),
    }

    // Add user message immediately
    const updatedMessages = [...currentMessages, userMessage]
    const updatedChats = { ...chats, [selectedProfile.id]: updatedMessages }
    setChats(updatedChats)
    saveChats(updatedChats)
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/test-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          birth_date: selectedProfile.birth_date,
          birth_time: selectedProfile.birth_time,
          is_male: selectedProfile.is_male,
        }),
      })

      const data = await response.json()

      const assistantMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: data.llm_answer || data.assistant_text || '抱歉，无法获取回复。',
        debug: data.context_trace ? { 
          context_trace: data.context_trace,
          router_trace: data.router_trace,
          index: data.index,
          facts: data.facts,
        } : undefined,
        created_at: new Date().toISOString(),
      }

      const finalMessages = [...updatedMessages, assistantMessage]
      const finalChats = { ...chats, [selectedProfile.id]: finalMessages }
      setChats(finalChats)
      saveChats(finalChats)

    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: '抱歉，发生了错误，请稍后再试。',
        created_at: new Date().toISOString(),
      }
      const finalMessages = [...updatedMessages, errorMessage]
      const finalChats = { ...chats, [selectedProfile.id]: finalMessages }
      setChats(finalChats)
      saveChats(finalChats)
    } finally {
      setIsLoading(false)
    }
  }

  // Clear chat
  const handleClearChat = () => {
    if (!selectedProfile) return
    const updatedChats = { ...chats, [selectedProfile.id]: [] }
    setChats(updatedChats)
    saveChats(updatedChats)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="container mx-auto p-4 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
            八字运势测试
          </h1>
          <p className="text-slate-400 text-sm mt-1">无需登录，本地存储聊天记录</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Left Sidebar: Profiles */}
          <div className="lg:col-span-1">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg text-slate-200 flex justify-between items-center">
                  档案列表
                  <Dialog open={showNewProfile} onOpenChange={setShowNewProfile}>
                    <DialogTrigger asChild>
                      <Button size="sm" variant="outline" className="h-7 text-xs">
                        + 新增
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-800 border-slate-700 text-white">
                      <DialogHeader>
                        <DialogTitle>新增档案</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4 mt-4">
                        <div>
                          <label className="text-sm text-slate-400">名称</label>
                          <Input
                            value={newProfileForm.name}
                            onChange={e => setNewProfileForm({ ...newProfileForm, name: e.target.value })}
                            placeholder="例：小明"
                            className="mt-1 bg-slate-700 border-slate-600"
                          />
                        </div>
                        <div>
                          <label className="text-sm text-slate-400">出生日期</label>
                          <Input
                            type="date"
                            value={newProfileForm.birth_date}
                            onChange={e => setNewProfileForm({ ...newProfileForm, birth_date: e.target.value })}
                            className="mt-1 bg-slate-700 border-slate-600"
                          />
                        </div>
                        <div>
                          <label className="text-sm text-slate-400">出生时间</label>
                          <Input
                            type="time"
                            value={newProfileForm.birth_time}
                            onChange={e => setNewProfileForm({ ...newProfileForm, birth_time: e.target.value })}
                            className="mt-1 bg-slate-700 border-slate-600"
                          />
                        </div>
                        <div className="flex items-center gap-4">
                          <label className="text-sm text-slate-400">性别</label>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant={newProfileForm.is_male ? 'default' : 'outline'}
                              onClick={() => setNewProfileForm({ ...newProfileForm, is_male: true })}
                            >
                              男
                            </Button>
                            <Button
                              size="sm"
                              variant={!newProfileForm.is_male ? 'default' : 'outline'}
                              onClick={() => setNewProfileForm({ ...newProfileForm, is_male: false })}
                            >
                              女
                            </Button>
                          </div>
                        </div>
                        <Button onClick={handleCreateProfile} className="w-full">
                          创建
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {profiles.length === 0 ? (
                  <p className="text-slate-500 text-sm text-center py-4">暂无档案，请点击新增</p>
                ) : (
                  profiles.map(profile => (
                    <div
                      key={profile.id}
                      className={`p-3 rounded-lg cursor-pointer transition-all ${
                        selectedProfile?.id === profile.id
                          ? 'bg-amber-600/30 border border-amber-500/50'
                          : 'bg-slate-700/50 hover:bg-slate-700'
                      }`}
                      onClick={() => setSelectedProfile(profile)}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium text-slate-200">{profile.name}</div>
                          <div className="text-xs text-slate-400">
                            {profile.birth_date} {profile.birth_time}
                          </div>
                          <div className="text-xs text-slate-500">
                            {profile.is_male ? '男' : '女'}
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0 text-red-400 hover:text-red-300 hover:bg-red-900/30"
                          onClick={(e) => {
                            e.stopPropagation()
                            if (confirm('确定删除此档案？')) {
                              handleDeleteProfile(profile.id)
                            }
                          }}
                        >
                          ×
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Main Chat Area */}
          <div className="lg:col-span-3">
            <Card className="bg-slate-800/50 border-slate-700 h-[calc(100vh-200px)] flex flex-col">
              <CardHeader className="pb-2 border-b border-slate-700">
                <div className="flex justify-between items-center">
                  <CardTitle className="text-lg text-slate-200">
                    {selectedProfile ? `与 ${selectedProfile.name} 的对话` : '请选择档案开始对话'}
                  </CardTitle>
                  {selectedProfile && currentMessages.length > 0 && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs text-red-400 border-red-400/50 hover:bg-red-900/30"
                      onClick={handleClearChat}
                    >
                      清空对话
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-auto p-4 space-y-4">
                {!selectedProfile ? (
                  <div className="flex items-center justify-center h-full text-slate-500">
                    ← 请先选择或新增一个档案
                  </div>
                ) : currentMessages.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-slate-500">
                    开始你的第一个问题吧！试试"我今年运势怎么样？"
                  </div>
                ) : (
                  currentMessages.map(msg => (
                    <div key={msg.id}>
                      <div
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg px-4 py-2 ${
                            msg.role === 'user'
                              ? 'bg-amber-600 text-white'
                              : 'bg-slate-700 text-slate-200'
                          }`}
                        >
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                        </div>
                      </div>
                      {msg.debug && <DebugPanel data={msg.debug} />}
                    </div>
                  ))
                )}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-slate-700 text-slate-400 rounded-lg px-4 py-2">
                      正在思考...
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </CardContent>

              {/* Input Area */}
              {selectedProfile && (
                <div className="p-4 border-t border-slate-700">
                  <div className="flex gap-2">
                    <Input
                      value={inputMessage}
                      onChange={e => setInputMessage(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSendMessage()
                        }
                      }}
                      placeholder="输入问题，例如：我今年运势怎么样？最近5年财运如何？"
                      className="flex-1 bg-slate-700 border-slate-600"
                      disabled={isLoading}
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={isLoading || !inputMessage.trim()}
                      className="bg-amber-600 hover:bg-amber-500"
                    >
                      发送
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================================
// Debug Panel Component（只读 context_trace，3 个 Tab：Router / Facts / Index）
// ============================================================

function DebugPanel({ data }: { data: DebugData }) {
  const ct = data.context_trace
  if (!ct) {
    return (
      <Card className="mt-2 bg-slate-800 border-slate-600 text-sm">
        <CardContent className="p-3 text-slate-500">
          (无调试数据)
        </CardContent>
      </Card>
    )
  }

  // 按 kind 分组 blocks
  const factsBlocks = ct.used_blocks.filter(b => b.kind === 'facts' && b.used)
  const indexBlocks = ct.used_blocks.filter(b => b.kind === 'index' && b.used)

  return (
    <Card className="mt-2 bg-slate-800 border-slate-600 text-sm">
      <CardContent className="p-3">
        <Tabs defaultValue="llm-input" className="w-full">
          <TabsList className="bg-slate-700 h-8">
            <TabsTrigger value="llm-input" className="text-xs h-6">LLM Input</TabsTrigger>
            <TabsTrigger value="router" className="text-xs h-6">Router</TabsTrigger>
            <TabsTrigger value="facts" className="text-xs h-6">Facts</TabsTrigger>
            <TabsTrigger value="index" className="text-xs h-6">Index</TabsTrigger>
          </TabsList>

          {/* ===== LLM Input Tab（完整 LLM 输入文案）===== */}
          <TabsContent value="llm-input" className="mt-3 space-y-3">
            {ct.context ? (
              <>
                {/* Summary Stats */}
                <div className="grid grid-cols-4 gap-2 text-xs">
                  <div className="bg-slate-900 p-2 rounded text-center">
                    <div className="text-slate-500">Total Chars</div>
                    <div className="text-cyan-400 font-mono">{ct.context.full_text?.length || 0}</div>
                  </div>
                  <div className="bg-slate-900 p-2 rounded text-center">
                    <div className="text-slate-500">Token Est</div>
                    <div className="text-yellow-400 font-mono">{ct.context.token_est || 0}</div>
                  </div>
                  <div className="bg-slate-900 p-2 rounded text-center">
                    <div className="text-slate-500">Parts</div>
                    <div className="text-green-400 font-mono">{ct.context.parts?.length || 0}</div>
                  </div>
                  <div className="bg-slate-900 p-2 rounded text-center">
                    <div className="text-slate-500">Truncated</div>
                    <div className={`font-mono ${ct.context.was_truncated ? 'text-red-400' : 'text-green-400'}`}>
                      {ct.context.was_truncated ? 'YES' : 'NO'}
                    </div>
                  </div>
                </div>

                {/* Drilldown Summary */}
                {ct.context.drilldown_summary && (
                  <div className="bg-slate-900 p-3 rounded">
                    <div className="text-xs text-slate-500 mb-2">下钻诊断 (Drilldown Summary)</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-500">触发下钻:</span>{' '}
                        <span className={ct.context.drilldown_summary.drilldown_triggered ? 'text-green-400' : 'text-slate-400'}>
                          {ct.context.drilldown_summary.drilldown_triggered ? 'YES' : 'NO'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">凶/变动年份:</span>{' '}
                        <span className="text-yellow-400 font-mono">
                          [{ct.context.drilldown_summary.risky_years_detected.join(', ')}]
                        </span>
                      </div>
                    </div>
                    {ct.context.drilldown_summary.year_detail_blocks_added.length > 0 && (
                      <div className="mt-2 text-xs">
                        <span className="text-slate-500">下钻 Blocks:</span>{' '}
                        <span className="text-cyan-400 font-mono">
                          {ct.context.drilldown_summary.year_detail_blocks_added.join(', ')}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Parts List */}
                {ct.context.parts && ct.context.parts.length > 0 && (
                  <div className="bg-slate-900 p-3 rounded">
                    <div className="text-xs text-slate-500 mb-2">LLM 输入段落分解 (Parts)</div>
                    <div className="space-y-1 max-h-32 overflow-auto">
                      {ct.context.parts.map((part, i) => (
                        <div key={i} className="flex items-center gap-2 text-xs">
                          <span className="text-slate-600 w-4">{part.part_id}</span>
                          <span className={`px-1 rounded text-xs ${
                            part.role === 'system' ? 'bg-purple-900/50 text-purple-300' :
                            part.role === 'user' ? 'bg-blue-900/50 text-blue-300' :
                            part.role === 'facts' ? 'bg-green-900/50 text-green-300' :
                            part.role === 'separator' ? 'bg-slate-700 text-slate-400' :
                            'bg-slate-800 text-slate-300'
                          }`}>
                            {part.role}
                          </span>
                          {part.block_type && (
                            <span className="text-cyan-400 font-mono text-xs">{part.block_type}</span>
                          )}
                          {part.year && (
                            <span className="text-yellow-400 text-xs">{part.year}年</span>
                          )}
                          <span className="text-slate-500 ml-auto">{part.chars_total} chars</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Full Text */}
                <div className="bg-slate-900 p-3 rounded">
                  <div className="text-xs text-slate-500 mb-2">
                    完整 LLM 输入 (Full Text) - {ct.context.full_text?.length || 0} chars
                  </div>
                  <pre className="text-xs bg-slate-950 p-3 rounded text-slate-300 whitespace-pre-wrap break-words max-h-96 overflow-auto font-mono leading-relaxed">
                    {ct.context.full_text || ct.context.full_text_preview || '(无数据)'}
                  </pre>
                </div>

                {/* SHA256 */}
                {ct.context.full_text_sha256 && (
                  <div className="text-xs text-slate-600">
                    SHA256: <span className="font-mono">{ct.context.full_text_sha256}</span>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-slate-900 p-3 rounded text-center text-slate-500 text-xs">
                本次请求无 LLM Context 数据（context_trace.context 为空）
              </div>
            )}
          </TabsContent>

          {/* ===== Router Tab ===== */}
          <TabsContent value="router" className="mt-3 space-y-3">
            {/* Router Meta */}
            <div className="bg-slate-900 p-3 rounded">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-500">Router ID:</span>{' '}
                  <span className="text-cyan-400 font-mono">{ct.router.router_id}</span>
                </div>
                <div>
                  <span className="text-slate-500">Intent:</span>{' '}
                  <span className="text-yellow-400 font-mono">{ct.router.intent}</span>
                </div>
                <div>
                  <span className="text-slate-500">Mode:</span>{' '}
                  <span className="text-green-400">{ct.router.mode}</span>
                </div>
                <div>
                  <span className="text-slate-500">Reason:</span>{' '}
                  <span className="text-slate-300">{ct.router.reason}</span>
                </div>
              </div>
              {ct.router.child_router && (
                <div className="mt-2 pt-2 border-t border-slate-700 text-xs">
                  <span className="text-purple-400">Child Router:</span>
                  <span className="text-slate-300 ml-2">{ct.router.child_router.router_id}</span>
                </div>
              )}
            </div>

            {/* Context Order */}
            <div className="bg-slate-900 p-2 rounded">
              <div className="text-slate-500 text-xs mb-1">LLM Context Order:</div>
              <div className="flex gap-2 flex-wrap">
                {ct.context_order.map((block, i) => (
                  <span key={i} className="bg-cyan-900/50 text-cyan-300 px-2 py-0.5 rounded text-xs">
                    {i + 1}. {block}
                  </span>
                ))}
                {ct.context_order.length === 0 && (
                  <span className="text-slate-500 text-xs">(empty)</span>
                )}
              </div>
            </div>

            {/* Used Blocks Summary */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-slate-900 p-2 rounded text-center">
                <div className="text-slate-500">Facts Blocks</div>
                <div className="text-green-400 font-mono text-lg">{factsBlocks.length}</div>
              </div>
              <div className="bg-slate-900 p-2 rounded text-center">
                <div className="text-slate-500">Index Blocks</div>
                <div className="text-blue-400 font-mono text-lg">{indexBlocks.length}</div>
              </div>
            </div>

            {/* Index Hits */}
            {ct.index_usage.index_hits.length > 0 && (
              <div className="bg-slate-900 p-2 rounded">
                <div className="text-slate-500 text-xs mb-1">Index Hits:</div>
                <div className="text-xs font-mono text-blue-300">
                  [{ct.index_usage.index_hits.join(', ')}]
                </div>
              </div>
            )}

            {/* Selected Facts Paths */}
            {ct.facts_selection.selected_facts_paths.length > 0 && (
              <div className="bg-slate-900 p-2 rounded">
                <div className="text-slate-500 text-xs mb-1">Selected Facts Paths:</div>
                <div className="text-xs font-mono text-cyan-300 space-y-1 max-h-24 overflow-auto">
                  {ct.facts_selection.selected_facts_paths.slice(0, 10).map((p, i) => (
                    <div key={i}>{p}</div>
                  ))}
                  {ct.facts_selection.selected_facts_paths.length > 10 && (
                    <div className="text-slate-500">... ({ct.facts_selection.selected_facts_paths.length} total)</div>
                  )}
                </div>
              </div>
            )}
          </TabsContent>

          {/* ===== Facts Tab（只展示 kind==="facts" 的 blocks）===== */}
          <TabsContent value="facts" className="mt-3 space-y-3">
            {/* Summary */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-slate-900 p-2 rounded text-center">
                <div className="text-slate-500">Facts Blocks Used</div>
                <div className={`font-mono text-lg ${factsBlocks.length > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {factsBlocks.length}
                </div>
              </div>
              <div className="bg-slate-900 p-2 rounded text-center">
                <div className="text-slate-500">Total Chars</div>
                <div className="text-slate-300 font-mono">
                  {factsBlocks.reduce((sum, b) => sum + b.chars_total, 0)}
                </div>
              </div>
            </div>

            {factsBlocks.length === 0 ? (
              <div className="bg-slate-900 p-3 rounded text-center text-slate-500 text-xs">
                本次请求未使用 Facts Blocks
              </div>
            ) : (
              factsBlocks.map((block, i) => (
                <Accordion key={i} type="single" collapsible className="w-full">
                  <AccordionItem value={block.block_id} className="border-slate-600">
                    <AccordionTrigger className="text-xs py-2">
                      <div className="flex items-center gap-2 text-left w-full">
                        <span className="text-green-400">✓</span>
                        <span className="text-cyan-400 font-mono">{block.block_type}</span>
                        <span className="text-slate-500">|</span>
                        <span className="text-slate-400">{block.source}</span>
                        {block.year && (
                          <>
                            <span className="text-slate-500">|</span>
                            <span className="text-yellow-400">{block.year}年</span>
                          </>
                        )}
                        <span className="text-slate-500 ml-auto">{block.chars_total} chars</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-2">
                        <div className="text-xs text-slate-500">
                          <span className="text-slate-600">ID:</span> {block.block_id}
                        </div>
                        {block.reason && (
                          <div className="text-xs text-slate-500">
                            <span className="text-slate-600">Reason:</span> {block.reason}
                          </div>
                        )}
                        <div className="bg-slate-950 p-2 rounded">
                          <div className="text-xs text-slate-500 mb-1">Preview (600 chars max):</div>
                          <pre className="text-xs text-slate-300 whitespace-pre-wrap break-words">
                            {block.preview || '(empty)'}
                          </pre>
                        </div>
                        {block.full_text && block.full_text.length > (block.preview?.length || 0) && (
                          <details className="text-xs">
                            <summary className="text-cyan-400 cursor-pointer hover:underline">
                              展开全文 ({block.chars_total} chars)
                            </summary>
                            <pre className="mt-2 bg-slate-950 p-2 rounded text-slate-300 whitespace-pre-wrap break-words max-h-64 overflow-auto">
                              {block.full_text}
                            </pre>
                          </details>
                        )}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              ))
            )}
          </TabsContent>

          {/* ===== Index Tab（used index blocks + full index）===== */}
          <TabsContent value="index" className="mt-3 space-y-3">
            {/* Used Index Blocks */}
            <div className="text-xs text-slate-400 mb-2">
              Used Index Blocks: {indexBlocks.length}
            </div>
            
            {indexBlocks.length > 0 && (
              <div className="space-y-2">
                {indexBlocks.map((block, i) => (
                  <div key={i} className="bg-slate-900 p-2 rounded text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-blue-400">✓</span>
                      <span className="text-cyan-400 font-mono">{block.block_type}</span>
                      <span className="text-slate-500 ml-auto">{block.source}</span>
                    </div>
                    {block.reason && (
                      <div className="text-slate-500 mt-1 text-xs italic">{block.reason}</div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Full Index（折叠显示）*/}
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="full-index" className="border-slate-600">
                <AccordionTrigger className="text-xs py-2">
                  Full Index (raw)
                </AccordionTrigger>
                <AccordionContent>
                  <pre className="text-xs bg-slate-900 p-2 rounded overflow-auto max-h-48 text-slate-300">
                    {data.index ? JSON.stringify(data.index, null, 2) : '(no index data)'}
                  </pre>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </TabsContent>
        </Tabs>

        {/* Timing */}
        <div className="mt-3 pt-2 border-t border-slate-700 text-xs text-slate-500 flex gap-3">
          <span>Router: {ct.run_meta.timing_ms.router}ms</span>
          <span>Engine: {ct.run_meta.timing_ms.engine}ms</span>
          <span>LLM: {ct.run_meta.timing_ms.llm}ms</span>
        </div>
      </CardContent>
    </Card>
  )
}
