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
// Types
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

interface UsedFact {
  fact_id: string
  type: string
  scope: string
  fact_year: number | null
  year_source: string
  label: string
  text_preview: string
  reason: string
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

interface YearDetailTrace {
  year: number
  parse_status: 'success' | 'failed'
  raw_text_preview: string
  year_detail: {
    year: number
    half_year_grade: { first: string; second: string }
    gan_block: { gan: string; shishen: string; yongshen_yesno: string; tags: string[]; risk_pct: number }
    zhi_block: { zhi: string; shishen: string; yongshen_yesno: string; tags: string[]; risk_pct: number }
    hint_summary_lines: string[]
    dayun_brief: { name: string; start_age: number; end_age: number; grade: string } | null
    raw_text: string
  } | null
}

interface EvidenceBlock {
  block_id: string
  block_type: string
  source: 'engine' | 'index' | 'stub'
  scope: 'year' | 'range' | 'general'
  year?: number
  used: boolean
  reason: string
  preview: string
  length_chars: number
  full_text?: string
}

interface EvidenceTrace {
  used_blocks: EvidenceBlock[]
  llm_context_order: string[]
}

interface ModuleTrace {
  module: string
  source: string
  used: boolean
  reason?: string
  produced_blocks: string[]
}

interface DebugData {
  router_trace: Record<string, unknown>
  modules_trace: ModuleTrace[]
  index_trace: {
    slices_used: string[]
    slices_payload: Record<string, unknown>
  }
  facts_trace: {
    used_facts: UsedFact[]
    used_count: number
    available_count: number
    source: string
    selection_trace: FactSelectionTrace
    debug_year_histogram: Record<number, number>
    extracted_year_null_count: number
    sample_extracted_years: Array<{ fact_id: string; scope: string; extracted_year: number | null; year_source: string }>
    facts_policy?: string
  }
  evidence_trace?: EvidenceTrace  // 证据块回放
  year_detail_trace?: YearDetailTrace | null
  run_meta: {
    timing_ms: {
      router: number
      engine: number
      llm: number
    }
    llm_input_preview?: string
  }
  debug_used_fact_ids?: string[]
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
    const savedProfiles = loadProfiles()
    const savedChats = loadChats()
    setProfiles(savedProfiles)
    setChats(savedChats)
    if (savedProfiles.length > 0) {
      setSelectedProfile(savedProfiles[0])
    }
  }, [])

  // Scroll to bottom when messages change
  const currentMessages = selectedProfile ? (chats[selectedProfile.id] || []) : []
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentMessages])

  // Create profile
  const createProfile = () => {
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

    const updatedProfiles = [newProfile, ...profiles]
    setProfiles(updatedProfiles)
    saveProfiles(updatedProfiles)
    setSelectedProfile(newProfile)
    setShowNewProfile(false)
    setNewProfileForm({ name: '', birth_date: '', birth_time: '', is_male: true })
  }

  // Delete profile
  const deleteProfile = (profileId: string) => {
    const updatedProfiles = profiles.filter(p => p.id !== profileId)
    setProfiles(updatedProfiles)
    saveProfiles(updatedProfiles)

    // Remove chat history
    const updatedChats = { ...chats }
    delete updatedChats[profileId]
    setChats(updatedChats)
    saveChats(updatedChats)

    if (selectedProfile?.id === profileId) {
      setSelectedProfile(updatedProfiles[0] || null)
    }
  }

  // Send message
  const sendMessage = async () => {
    if (!selectedProfile || !inputMessage.trim() || isLoading) return

    const messageText = inputMessage.trim()
    setInputMessage('')
    setIsLoading(true)

    // Add user message
    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: messageText,
      created_at: new Date().toISOString(),
    }

    const currentProfileChats = chats[selectedProfile.id] || []
    const updatedChats = {
      ...chats,
      [selectedProfile.id]: [...currentProfileChats, userMessage],
    }
    setChats(updatedChats)
    saveChats(updatedChats)

    try {
      // Call API
      const response = await fetch('/api/test-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageText,
          birth_date: selectedProfile.birth_date,
          birth_time: selectedProfile.birth_time,
          is_male: selectedProfile.is_male,
        }),
      })

      const data = await response.json()

      // Add assistant message
      const assistantMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: data.assistant_text || '抱歉，发生错误',
        debug: {
          router_trace: data.router_trace || {},
          modules_trace: data.modules_trace || [],
          index_trace: data.index_trace || { slices_used: [], slices_payload: {} },
          evidence_trace: data.evidence_trace || { used_blocks: [], llm_context_order: [] },
          facts_trace: data.facts_trace || {
            used_facts: [],
            used_count: 0,
            available_count: 0,
            source: '',
            selection_trace: {
              time_scope: { type: 'unknown' },
              focus: 'general',
              allowed_years: [],
              steps: [],
              fallback_triggered: false,
              fallback_reason: '',
              final_count: 0,
            },
            debug_year_histogram: {},
            extracted_year_null_count: 0,
            sample_extracted_years: [],
          },
          run_meta: data.run_meta || { timing_ms: { router: 0, engine: 0, llm: 0 } },
          debug_used_fact_ids: data.debug_used_fact_ids || [],
        },
        created_at: new Date().toISOString(),
      }

      const finalChats = {
        ...updatedChats,
        [selectedProfile.id]: [...updatedChats[selectedProfile.id], assistantMessage],
      }
      setChats(finalChats)
      saveChats(finalChats)

    } catch (error) {
      console.error('Error:', error)
      // Add error message
      const errorMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: '❌ 发送失败，请检查服务是否运行',
        created_at: new Date().toISOString(),
      }
      const finalChats = {
        ...updatedChats,
        [selectedProfile.id]: [...updatedChats[selectedProfile.id], errorMessage],
      }
      setChats(finalChats)
      saveChats(finalChats)
    } finally {
      setIsLoading(false)
    }
  }

  // Clear chat
  const clearChat = () => {
    if (!selectedProfile) return
    const updatedChats = { ...chats, [selectedProfile.id]: [] }
    setChats(updatedChats)
    saveChats(updatedChats)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white flex">
      {/* Sidebar */}
      <div className="w-72 bg-slate-800/80 border-r border-slate-700 flex flex-col backdrop-blur-sm">
        {/* Header */}
        <div className="p-4 border-b border-slate-700">
          <h1 className="text-xl font-bold">🔮 Hayyy 八字</h1>
          <p className="text-xs text-slate-400 mt-1">AI 命理分析测试版</p>
        </div>

        {/* Profiles */}
        <div className="flex-1 p-4 overflow-auto">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-slate-400">档案列表</span>
            <Dialog open={showNewProfile} onOpenChange={setShowNewProfile}>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm" className="h-7 text-xs">+ 新建</Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-800 border-slate-700 text-white">
                <DialogHeader>
                  <DialogTitle>新建档案</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <Input
                    placeholder="名称（如：小明）"
                    value={newProfileForm.name}
                    onChange={e => setNewProfileForm({ ...newProfileForm, name: e.target.value })}
                    className="bg-slate-700 border-slate-600"
                  />
                  <div>
                    <label className="text-sm text-slate-400 block mb-1">出生日期</label>
                    <Input
                      type="date"
                      value={newProfileForm.birth_date}
                      onChange={e => setNewProfileForm({ ...newProfileForm, birth_date: e.target.value })}
                      className="bg-slate-700 border-slate-600"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-slate-400 block mb-1">出生时间</label>
                    <Input
                      type="time"
                      value={newProfileForm.birth_time}
                      onChange={e => setNewProfileForm({ ...newProfileForm, birth_time: e.target.value })}
                      className="bg-slate-700 border-slate-600"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant={newProfileForm.is_male ? 'default' : 'outline'}
                      onClick={() => setNewProfileForm({ ...newProfileForm, is_male: true })}
                      className="flex-1"
                    >
                      男
                    </Button>
                    <Button
                      variant={!newProfileForm.is_male ? 'default' : 'outline'}
                      onClick={() => setNewProfileForm({ ...newProfileForm, is_male: false })}
                      className="flex-1"
                    >
                      女
                    </Button>
                  </div>
                  <Button onClick={createProfile} className="w-full">创建档案</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          <div className="space-y-2">
            {profiles.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">
                还没有档案，点击上方"新建"创建
              </p>
            ) : (
              profiles.map(profile => (
                <div
                  key={profile.id}
                  className={`group relative rounded-lg transition-colors ${
                    selectedProfile?.id === profile.id
                      ? 'bg-purple-600'
                      : 'hover:bg-slate-700'
                  }`}
                >
                  <button
                    onClick={() => setSelectedProfile(profile)}
                    className="w-full text-left px-3 py-3"
                  >
                    <div className="font-medium">{profile.name}</div>
                    <div className="text-xs text-slate-300 opacity-70">
                      {profile.birth_date} {profile.birth_time}
                      {profile.is_male ? ' 男' : ' 女'}
                    </div>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      if (confirm(`确定删除档案 "${profile.name}"？`)) {
                        deleteProfile(profile.id)
                      }
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-400 transition-opacity"
                  >
                    ✕
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-700 text-xs text-slate-500">
          数据保存在浏览器本地
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedProfile ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-slate-700 bg-slate-800/50 flex items-center justify-between">
              <div>
                <h2 className="font-bold">{selectedProfile.name}</h2>
                <p className="text-xs text-slate-400">
                  {selectedProfile.birth_date} {selectedProfile.birth_time} {selectedProfile.is_male ? '男' : '女'}
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={clearChat}>
                清空记录
              </Button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-auto p-6 space-y-4">
              {currentMessages.length === 0 && (
                <div className="text-center text-slate-500 py-20">
                  <p className="text-lg mb-2">开始对话</p>
                  <p className="text-sm">试试问：今年运势怎么样？</p>
                </div>
              )}
              {currentMessages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-slate-700 rounded-lg px-4 py-3">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-slate-700 bg-slate-800/50">
              <div className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={e => setInputMessage(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && sendMessage()}
                  placeholder="输入问题，例如：今年运势怎么样？最近感情如何？"
                  className="flex-1 bg-slate-700 border-slate-600"
                  disabled={isLoading}
                />
                <Button onClick={sendMessage} disabled={isLoading}>
                  发送
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400">
            <div className="text-center">
              <p className="text-xl mb-4">👈 请先创建一个档案</p>
              <p className="text-sm">点击左侧"新建"按钮</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================
// Message Bubble Component
// ============================================================

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  const [showDebug, setShowDebug] = useState(false)

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[75%]`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-purple-600 text-white rounded-br-sm'
              : 'bg-slate-700 text-slate-100 rounded-bl-sm'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Debug Button */}
        {!isUser && message.debug && (
          <div className="mt-1">
            <button
              onClick={() => setShowDebug(!showDebug)}
              className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              {showDebug ? '隐藏调试' : '🔍 查看调试'}
            </button>

            {showDebug && <DebugPanel data={message.debug} />}
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-xs text-slate-500 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {new Date(message.created_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

// ============================================================
// Debug Panel Component
// ============================================================

function DebugPanel({ data }: { data: DebugData }) {
  return (
    <Card className="mt-2 bg-slate-800 border-slate-600 text-sm">
      <CardContent className="p-3">
        <Tabs defaultValue="router" className="w-full">
          <TabsList className="bg-slate-700 h-8 flex-wrap">
            <TabsTrigger value="router" className="text-xs h-6">Router</TabsTrigger>
            <TabsTrigger value="modules" className="text-xs h-6">Modules</TabsTrigger>
            <TabsTrigger value="evidence" className="text-xs h-6 text-cyan-400">Evidence</TabsTrigger>
            <TabsTrigger value="index" className="text-xs h-6">Index</TabsTrigger>
            <TabsTrigger value="facts" className="text-xs h-6">Facts</TabsTrigger>
            {data.year_detail_trace && (
              <TabsTrigger value="year" className="text-xs h-6 text-yellow-400">Year</TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="router" className="mt-3">
            <pre className="text-xs bg-slate-900 p-2 rounded overflow-auto max-h-48 text-slate-300">
              {JSON.stringify(data.router_trace, null, 2)}
            </pre>
          </TabsContent>

          <TabsContent value="modules" className="mt-3 space-y-2">
            {data.modules_trace.map((mod, i) => (
              <div key={i} className="bg-slate-900 p-2 rounded text-xs">
                <div className="flex items-center gap-2">
                  <span className={`font-mono ${mod.used ? 'text-green-400' : 'text-slate-500'}`}>
                    {mod.used ? '✓' : '✗'}
                  </span>
                  <span className="text-slate-300 font-medium">{mod.module}</span>
                  <span className="text-slate-500">|</span>
                  <span className="text-slate-400">{mod.source}</span>
                </div>
                {mod.reason && (
                  <div className="text-slate-500 text-xs mt-1 ml-4">{mod.reason}</div>
                )}
                {mod.produced_blocks.length > 0 && (
                  <div className="text-cyan-400 text-xs mt-1 ml-4">
                    → {mod.produced_blocks.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </TabsContent>

          {/* Evidence Tab */}
          <TabsContent value="evidence" className="mt-3 space-y-3">
            {data.evidence_trace ? (
              <>
                {/* Context Order */}
                <div className="bg-slate-900 p-2 rounded">
                  <div className="text-slate-500 text-xs mb-1">LLM Context Order:</div>
                  <div className="flex gap-2 flex-wrap">
                    {data.evidence_trace.llm_context_order.map((block, i) => (
                      <span key={i} className="bg-cyan-900/50 text-cyan-300 px-2 py-0.5 rounded text-xs">
                        {i + 1}. {block}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Used Blocks */}
                <div className="text-slate-400 text-xs">
                  Used Blocks: {data.evidence_trace.used_blocks.filter(b => b.used).length} / {data.evidence_trace.used_blocks.length}
                </div>

                {data.evidence_trace.used_blocks.map((block, i) => (
                  <Accordion key={i} type="single" collapsible className="w-full">
                    <AccordionItem value={block.block_id} className="border-slate-600">
                      <AccordionTrigger className="text-xs py-2">
                        <div className="flex items-center gap-2 text-left w-full">
                          <span className={block.used ? 'text-green-400' : 'text-slate-500'}>
                            {block.used ? '✓' : '✗'}
                          </span>
                          <span className="text-cyan-400 font-mono">{block.block_type}</span>
                          <span className="text-slate-500">|</span>
                          <span className="text-slate-400">{block.source}</span>
                          {block.year && (
                            <>
                              <span className="text-slate-500">|</span>
                              <span className="text-yellow-400">{block.year}</span>
                            </>
                          )}
                          <span className="text-slate-500 ml-auto">{block.length_chars} chars</span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="space-y-2">
                          <div className="text-xs text-slate-500">
                            <span className="text-slate-600">ID:</span> {block.block_id}
                          </div>
                          <div className="text-xs text-slate-500">
                            <span className="text-slate-600">Reason:</span> {block.reason}
                          </div>
                          <div className="bg-slate-950 p-2 rounded">
                            <div className="text-xs text-slate-500 mb-1">Preview (300 chars):</div>
                            <pre className="text-xs text-slate-300 whitespace-pre-wrap break-words">
                              {block.preview || '(empty)'}
                            </pre>
                          </div>
                          {block.full_text && block.full_text.length > 300 && (
                            <details className="text-xs">
                              <summary className="text-cyan-400 cursor-pointer hover:underline">
                                展开全文 ({block.length_chars} chars)
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
                ))}
              </>
            ) : (
              <div className="text-slate-500 text-xs">No evidence trace available</div>
            )}
          </TabsContent>

          <TabsContent value="index" className="mt-3">
            <div className="text-xs text-slate-400 mb-2">
              Slices: {data.index_trace.slices_used.join(', ') || '(none)'}
            </div>
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="payload" className="border-slate-600">
                <AccordionTrigger className="text-xs py-2">Payload</AccordionTrigger>
                <AccordionContent>
                  <pre className="text-xs bg-slate-900 p-2 rounded overflow-auto max-h-48 text-slate-300">
                    {JSON.stringify(data.index_trace.slices_payload, null, 2)}
                  </pre>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </TabsContent>

          <TabsContent value="facts" className="mt-3 space-y-3">
            {/* Summary */}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="bg-slate-900 p-2 rounded text-center">
                <div className="text-slate-500">Source</div>
                <div className="text-slate-300 font-mono">{data.facts_trace.source}</div>
              </div>
              <div className="bg-slate-900 p-2 rounded text-center">
                <div className="text-slate-500">Available</div>
                <div className="text-slate-300 font-mono">{data.facts_trace.available_count}</div>
              </div>
              <div className="bg-slate-900 p-2 rounded text-center">
                <div className="text-slate-500">Used</div>
                <div className={`font-mono ${data.facts_trace.used_count > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {data.facts_trace.used_count}
                </div>
              </div>
            </div>

            {/* Used Facts */}
            {data.facts_trace.used_facts.length > 0 && (
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="used-facts" className="border-slate-600">
                  <AccordionTrigger className="text-xs py-2 text-green-400">
                    ✓ Used Facts ({data.facts_trace.used_facts.length})
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-2">
                      {data.facts_trace.used_facts.map((fact, i) => (
                        <div key={i} className="bg-slate-900 p-2 rounded text-xs">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-purple-400">{fact.fact_id}</span>
                            <span className="text-slate-500">|</span>
                            <span className="text-slate-400">{fact.type}</span>
                            <span className="text-slate-500">|</span>
                            <span className="text-slate-400">{fact.scope}</span>
                            <span className="text-slate-500">|</span>
                            <span className={fact.fact_year ? 'text-blue-400' : 'text-slate-600'}>
                              year={fact.fact_year ?? 'N/A'}
                            </span>
                          </div>
                          <div className="mt-1 text-slate-300">{fact.label}</div>
                          <div className="mt-1 text-slate-500">{fact.text_preview}</div>
                          <div className="mt-1 text-xs">
                            <span className="text-slate-600">year_source:</span>
                            <span className="text-slate-500 ml-1">{fact.year_source}</span>
                          </div>
                          <div className="mt-1 text-xs text-green-600 italic">
                            ✓ {fact.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            )}

            {/* Selection Trace */}
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="selection-trace" className="border-slate-600">
                <AccordionTrigger className="text-xs py-2">
                  Selection Trace
                  {data.facts_trace.selection_trace.fallback_triggered && (
                    <span className="ml-2 text-yellow-400">(fallback triggered)</span>
                  )}
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-2 text-xs">
                    {/* Header */}
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-slate-900 p-2 rounded">
                        <span className="text-slate-500">Time Scope:</span>{' '}
                        <span className="text-slate-300 font-mono">
                          {data.facts_trace.selection_trace.time_scope.type}
                          {data.facts_trace.selection_trace.time_scope.year && ` (${data.facts_trace.selection_trace.time_scope.year})`}
                        </span>
                      </div>
                      <div className="bg-slate-900 p-2 rounded">
                        <span className="text-slate-500">Focus:</span>{' '}
                        <span className="text-slate-300">{data.facts_trace.selection_trace.focus}</span>
                      </div>
                    </div>
                    
                    {/* Allowed Years */}
                    <div className="bg-slate-900 p-2 rounded">
                      <span className="text-slate-500">Allowed Years:</span>{' '}
                      <span className="text-blue-400 font-mono">
                        [{data.facts_trace.selection_trace.allowed_years.slice(0, 5).join(', ')}
                        {data.facts_trace.selection_trace.allowed_years.length > 5 ? '...' : ''}]
                      </span>
                    </div>

                    {/* Steps */}
                    {data.facts_trace.selection_trace.steps.map((step, i) => (
                      <div key={i} className="bg-slate-900 p-2 rounded">
                        <div className="flex items-center gap-2">
                          <span className="text-yellow-500 font-mono">{step.step}</span>
                          <span className="text-slate-600">|</span>
                          <span className="text-slate-400">{step.filter}</span>
                        </div>
                        <div className="text-slate-400 mt-1">
                          {step.before_count} → {step.after_count}
                        </div>
                        <div className="text-slate-500 italic mt-1">
                          {step.reason}
                        </div>
                      </div>
                    ))}

                    {/* Fallback */}
                    {data.facts_trace.selection_trace.fallback_triggered && (
                      <div className="bg-yellow-900/30 p-2 rounded border border-yellow-800">
                        <div className="text-yellow-400">⚠ Fallback Triggered</div>
                        <div className="text-slate-300 mt-1">
                          {data.facts_trace.selection_trace.fallback_reason}
                        </div>
                      </div>
                    )}

                    {/* Final */}
                    <div className={`p-2 rounded border ${
                      data.facts_trace.selection_trace.final_count > 0
                        ? 'bg-green-900/30 border-green-800'
                        : 'bg-red-900/30 border-red-800'
                    }`}>
                      <div className={data.facts_trace.selection_trace.final_count > 0 ? 'text-green-400' : 'text-red-400'}>
                        Final Count: {data.facts_trace.selection_trace.final_count}
                      </div>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>

            {/* Debug Fact IDs */}
            {data.debug_used_fact_ids && data.debug_used_fact_ids.length > 0 && (
              <div className="bg-slate-900 p-2 rounded text-xs">
                <div className="text-slate-500 mb-1">debug_used_fact_ids:</div>
                <div className="font-mono text-purple-400">
                  [{data.debug_used_fact_ids.join(', ')}]
                </div>
              </div>
            )}

            {/* Year Histogram Diagnostics */}
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="diagnostics" className="border-slate-600">
                <AccordionTrigger className="text-xs py-2 text-slate-400">
                  🔬 Year Diagnostics
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-2 text-xs">
                    <div className="bg-slate-900 p-2 rounded">
                      <div className="text-slate-500 mb-1">Year Histogram (top 10):</div>
                      <div className="font-mono text-slate-300">
                        {Object.entries(data.facts_trace.debug_year_histogram || {})
                          .slice(0, 10)
                          .map(([year, count]) => `${year}:${count}`)
                          .join(', ') || '(empty)'}
                      </div>
                    </div>
                    <div className="bg-slate-900 p-2 rounded">
                      <span className="text-slate-500">Null year count:</span>{' '}
                      <span className="text-slate-300">{data.facts_trace.extracted_year_null_count ?? 0}</span>
                    </div>
                    <div className="bg-slate-900 p-2 rounded">
                      <div className="text-slate-500 mb-1">Sample (first 5):</div>
                      {(data.facts_trace.sample_extracted_years || []).slice(0, 5).map((s, i) => (
                        <div key={i} className="text-slate-400 ml-2">
                          {s.scope}: year={s.extracted_year ?? 'null'} ({s.year_source})
                        </div>
                      ))}
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>

            {/* Facts Policy (年请求时显示) */}
            {data.facts_trace.facts_policy === 'disabled_for_year_detail' && (
              <div className="bg-yellow-900/30 border border-yellow-600 p-2 rounded text-xs text-yellow-400">
                ⚠️ Facts 已禁用：year_detail 模式下使用 YEAR_DETAIL_BLOCK
              </div>
            )}
          </TabsContent>

          {/* Year Detail Tab */}
          {data.year_detail_trace && (
            <TabsContent value="year" className="mt-3 space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-slate-900 p-2 rounded text-center">
                  <div className="text-slate-500">Year</div>
                  <div className="text-yellow-400 font-mono text-lg">{data.year_detail_trace.year}</div>
                </div>
                <div className="bg-slate-900 p-2 rounded text-center">
                  <div className="text-slate-500">Parse Status</div>
                  <div className={`font-mono ${data.year_detail_trace.parse_status === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                    {data.year_detail_trace.parse_status}
                  </div>
                </div>
              </div>

              {data.year_detail_trace.year_detail && (
                <>
                  {/* 上下半年 */}
                  <div className="bg-slate-900 p-3 rounded">
                    <div className="text-slate-500 text-xs mb-2">【上下半年】</div>
                    <div className="flex gap-4">
                      <div className="flex-1 text-center">
                        <div className="text-slate-400 text-xs">上半年</div>
                        <div className={`text-lg font-bold ${
                          data.year_detail_trace.year_detail.half_year_grade.first === '好运' ? 'text-green-400' :
                          data.year_detail_trace.year_detail.half_year_grade.first === '凶' ? 'text-red-400' :
                          data.year_detail_trace.year_detail.half_year_grade.first === '变动' ? 'text-yellow-400' :
                          'text-slate-300'
                        }`}>
                          {data.year_detail_trace.year_detail.half_year_grade.first}
                        </div>
                      </div>
                      <div className="flex-1 text-center">
                        <div className="text-slate-400 text-xs">下半年</div>
                        <div className={`text-lg font-bold ${
                          data.year_detail_trace.year_detail.half_year_grade.second === '好运' ? 'text-green-400' :
                          data.year_detail_trace.year_detail.half_year_grade.second === '凶' ? 'text-red-400' :
                          data.year_detail_trace.year_detail.half_year_grade.second === '变动' ? 'text-yellow-400' :
                          'text-slate-300'
                        }`}>
                          {data.year_detail_trace.year_detail.half_year_grade.second}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 天干 */}
                  <div className="bg-slate-900 p-3 rounded text-xs">
                    <div className="text-slate-500 mb-1">【天干】</div>
                    <div className="text-slate-300">
                      {data.year_detail_trace.year_detail.gan_block.gan}｜
                      十神 {data.year_detail_trace.year_detail.gan_block.shishen}｜
                      用神 {data.year_detail_trace.year_detail.gan_block.yongshen_yesno}｜
                      {data.year_detail_trace.year_detail.gan_block.tags.join('/')}
                    </div>
                    <div className={`mt-1 ${data.year_detail_trace.year_detail.gan_block.risk_pct > 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {data.year_detail_trace.year_detail.gan_block.risk_pct > 0 
                        ? `危险系数：${data.year_detail_trace.year_detail.gan_block.risk_pct.toFixed(1)}%`
                        : '不易出现意外和风险'}
                    </div>
                  </div>

                  {/* 地支 */}
                  <div className="bg-slate-900 p-3 rounded text-xs">
                    <div className="text-slate-500 mb-1">【地支】</div>
                    <div className="text-slate-300">
                      {data.year_detail_trace.year_detail.zhi_block.zhi}｜
                      十神 {data.year_detail_trace.year_detail.zhi_block.shishen}｜
                      用神 {data.year_detail_trace.year_detail.zhi_block.yongshen_yesno}｜
                      {data.year_detail_trace.year_detail.zhi_block.tags.join('/')}
                    </div>
                    <div className={`mt-1 ${data.year_detail_trace.year_detail.zhi_block.risk_pct > 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {data.year_detail_trace.year_detail.zhi_block.risk_pct > 0 
                        ? `危险系数：${data.year_detail_trace.year_detail.zhi_block.risk_pct.toFixed(1)}%`
                        : '不易出现意外和风险'}
                    </div>
                  </div>

                  {/* 提示汇总 */}
                  <div className="bg-slate-900 p-3 rounded text-xs">
                    <div className="text-slate-500 mb-1">【提示汇总】</div>
                    {data.year_detail_trace.year_detail.hint_summary_lines.length > 0 ? (
                      <ul className="text-slate-300 space-y-1">
                        {data.year_detail_trace.year_detail.hint_summary_lines.map((hint, i) => (
                          <li key={i}>• {hint}</li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-slate-500 italic">今年暂无额外提示汇总</div>
                    )}
                  </div>

                  {/* Raw Text Preview */}
                  <Accordion type="single" collapsible className="w-full">
                    <AccordionItem value="raw-text" className="border-slate-600">
                      <AccordionTrigger className="text-xs py-2 text-slate-400">
                        📄 Raw Text Preview
                      </AccordionTrigger>
                      <AccordionContent>
                        <pre className="text-xs bg-slate-900 p-2 rounded overflow-auto max-h-48 text-slate-300 whitespace-pre-wrap">
                          {data.year_detail_trace.raw_text_preview || data.year_detail_trace.year_detail.raw_text?.slice(0, 500)}
                        </pre>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </>
              )}
            </TabsContent>
          )}
        </Tabs>

        {/* Timing */}
        <div className="mt-3 pt-2 border-t border-slate-700 text-xs text-slate-500 flex gap-3">
          <span>Router: {data.run_meta.timing_ms.router}ms</span>
          <span>Engine: {data.run_meta.timing_ms.engine}ms</span>
          <span>LLM: {data.run_meta.timing_ms.llm}ms</span>
        </div>
      </CardContent>
    </Card>
  )
}

