import { useEffect, useMemo, useRef, useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

type Role = 'user' | 'assistant'

type ProfileInfo = {
  birth_date: string
  birth_time: string
  is_male: boolean
  timezone: string
}

type ChatMessage = {
  id: string
  role: Role
  content: string
  created_at: string
  debug?: {
    context_trace: ContextTrace
    index?: Record<string, unknown>
  }
}

type ChatSession = {
  id: string
  title: string
  created_at: string
  updated_at: string
  profile: ProfileInfo
  messages: ChatMessage[]
}

type ContextBlock = {
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

type RouterMeta = {
  router_id: string
  intent: string
  mode: 'year' | 'range' | 'general'
  reason: string
  child_router?: RouterMeta | null
}

type ContextTrace = {
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

const LS_SESSIONS_KEY = 'gpt_like_sessions'
const DEFAULT_TZ = 'America/Los_Angeles'

export default function Home() {
  // Sidebar & sessions
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [showNewModal, setShowNewModal] = useState(false)
  const [newProfile, setNewProfile] = useState<ProfileInfo>({
    birth_date: '',
    birth_time: '',
    is_male: true,
    timezone: DEFAULT_TZ,
  })
  const [newTitle, setNewTitle] = useState('')

  // Chat state
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Debug drawer
  const [debugOpen, setDebugOpen] = useState(false)
  const [debugTab, setDebugTab] = useState<'router' | 'facts' | 'index'>('router')

  // Load sessions from localStorage
  useEffect(() => {
    const raw = localStorage.getItem(LS_SESSIONS_KEY)
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as ChatSession[]
        setSessions(parsed)
        if (parsed.length > 0) setActiveId(parsed[0].id)
      } catch {
        // ignore parse errors
      }
    }
  }, [])

  // Auto-scroll on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [sessions, activeId, isSending])

  const activeSession = sessions.find(s => s.id === activeId) || null
  const messages = activeSession?.messages || []

  const groupedSessions = useMemo(() => groupSessions(sessions), [sessions])

  const handleCreateSession = () => {
    if (!newProfile.birth_date || !newProfile.birth_time) {
      alert('请填写出生日期和时间（可填“未知”）')
      return
    }
    const id = `sess_${Date.now()}`
    const now = new Date().toISOString()
    const title = newTitle.trim() || 'New chat'
    const session: ChatSession = {
      id,
      title,
      created_at: now,
      updated_at: now,
      profile: newProfile,
      messages: [],
    }
    const next = [session, ...sessions]
    setSessions(next)
    localStorage.setItem(LS_SESSIONS_KEY, JSON.stringify(next))
    setActiveId(id)
    setShowNewModal(false)
    setNewProfile({ birth_date: '', birth_time: '', is_male: true, timezone: DEFAULT_TZ })
    setNewTitle('')
  }

  const handleDeleteSession = (id: string) => {
    const next = sessions.filter(s => s.id !== id)
    setSessions(next)
    localStorage.setItem(LS_SESSIONS_KEY, JSON.stringify(next))
    if (activeId === id) {
      setActiveId(next.length ? next[0].id : null)
    }
  }

  const handleRenameSession = (id: string, title: string) => {
    const next = sessions.map(s => (s.id === id ? { ...s, title } : s))
    setSessions(next)
    localStorage.setItem(LS_SESSIONS_KEY, JSON.stringify(next))
  }

  const persistSessions = (next: ChatSession[]) => {
    setSessions(next)
    localStorage.setItem(LS_SESSIONS_KEY, JSON.stringify(next))
  }

  const handleSend = async () => {
    if (!activeSession || !input.trim() || isSending) return
    const userText = input.trim()
    setInput('')

    const userMsg: ChatMessage = {
      id: `m_${Date.now()}_u`,
      role: 'user',
      content: userText,
      created_at: new Date().toISOString(),
    }

    const updatedSession: ChatSession = {
      ...activeSession,
      messages: [...activeSession.messages, userMsg],
      updated_at: new Date().toISOString(),
      title: activeSession.messages.length === 0 ? autoTitleFromText(userText) : activeSession.title,
    }
    const nextSessions = sessions.map(s => (s.id === activeSession.id ? updatedSession : s))
    persistSessions(nextSessions)
    setIsSending(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userText,
          birth_date: activeSession.profile.birth_date,
          birth_time: activeSession.profile.birth_time,
          is_male: activeSession.profile.is_male,
          timezone: activeSession.profile.timezone,
        }),
      })
      const data = await res.json()

      const assistantMsg: ChatMessage = {
        id: `m_${Date.now()}_a`,
        role: 'assistant',
        content: data.llm_answer || '（无回答）',
        created_at: new Date().toISOString(),
        debug: data.context_trace
          ? { context_trace: data.context_trace, index: data.index }
          : undefined,
      }

      const updated: ChatSession = {
        ...updatedSession,
        messages: [...updatedSession.messages, assistantMsg],
        updated_at: new Date().toISOString(),
      }
      const finalSessions = sessions.map(s => (s.id === activeSession.id ? updated : s))
      persistSessions(finalSessions)
    } catch (err) {
      const errMsg: ChatMessage = {
        id: `m_${Date.now()}_e`,
        role: 'assistant',
        content: '抱歉，请稍后再试。',
        created_at: new Date().toISOString(),
      }
      const fallback: ChatSession = {
        ...updatedSession,
        messages: [...updatedSession.messages, errMsg],
      }
      const finalSessions = sessions.map(s => (s.id === activeSession.id ? fallback : s))
      persistSessions(finalSessions)
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0f172a] text-white flex">
      {/* Sidebar */}
      <aside className="w-72 border-r border-slate-800 bg-[#0b1224] flex flex-col">
        <div className="p-3 flex items-center gap-2 border-b border-slate-800">
          <Button className="w-full bg-emerald-600 hover:bg-emerald-500" onClick={() => setShowNewModal(true)}>
            + New chat
          </Button>
        </div>
        <div className="flex-1 overflow-auto">
          {['today', 'yesterday', 'prev7', 'older'].map(section => (
            <SessionSection
              key={section}
              label={sectionLabel(section)}
              sessions={groupedSessions[section as keyof typeof groupedSessions]}
              activeId={activeId}
              onSelect={setActiveId}
              onDelete={handleDeleteSession}
              onRename={handleRenameSession}
            />
          ))}
        </div>
        <div className="p-3 border-t border-slate-800 text-slate-500 text-xs">
          Settings (placeholder)
        </div>
      </aside>

      {/* Main panel */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <div className="h-14 px-4 border-b border-slate-800 flex items-center justify-between bg-[#0b1224]">
          <div>
            <div className="text-sm text-slate-400">Hayyy Bazi</div>
            <div className="text-lg font-semibold">{activeSession ? activeSession.title : '选择或创建会话'}</div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" className="h-8 text-xs" onClick={() => setDebugOpen(!debugOpen)}>
              {debugOpen ? 'Close Debug' : 'Debug'}
            </Button>
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 overflow-auto px-6 py-6 space-y-4">
            {!activeSession ? (
              <div className="text-slate-500 text-center mt-10">请在左侧创建或选择一个会话</div>
            ) : (
              <>
                {messages.map(msg => (
                  <MessageBubble key={msg.id} msg={msg} />
                ))}
                {isSending && (
                  <div className="flex justify-start">
                    <div className="max-w-[80%] bg-slate-700 text-slate-200 rounded-lg px-4 py-2">
                      正在生成...
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Debug Drawer */}
          {debugOpen && activeSession && (
            <DebugDrawer
              messages={messages}
              activeTab={debugTab}
              onTabChange={setDebugTab}
            />
          )}
        </div>

        {/* Input */}
        <div className="border-t border-slate-800 p-4 bg-[#0b1224]">
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              placeholder={activeSession ? '输入你的问题，Enter 发送，Shift+Enter 换行' : '请先创建会话'}
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm min-h-[60px] resize-none focus:outline-none focus:ring-2 focus:ring-emerald-600"
              disabled={!activeSession || isSending}
            />
            <Button
              onClick={handleSend}
              disabled={!activeSession || isSending || !input.trim()}
              className="bg-emerald-600 hover:bg-emerald-500 px-4"
            >
              发送
            </Button>
          </div>
          <div className="text-xs text-slate-500 mt-2">Enter 发送，Shift+Enter 换行</div>
        </div>
      </main>

      {/* New chat modal */}
      <Dialog open={showNewModal} onOpenChange={setShowNewModal}>
        <DialogContent className="bg-slate-900 border border-slate-700 text-white max-w-lg">
          <DialogHeader>
            <DialogTitle>新建对话</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Input
              value={newTitle}
              onChange={e => setNewTitle(e.target.value)}
              placeholder="会话标题（可留空自动生成）"
              className="bg-slate-800 border-slate-700"
            />
            <Input
              type="date"
              value={newProfile.birth_date}
              onChange={e => setNewProfile({ ...newProfile, birth_date: e.target.value })}
              className="bg-slate-800 border-slate-700"
            />
            <Input
              type="time"
              value={newProfile.birth_time}
              onChange={e => setNewProfile({ ...newProfile, birth_time: e.target.value || '未知' })}
              className="bg-slate-800 border-slate-700"
            />
            <div className="flex gap-2">
              <Button
                variant={newProfile.is_male ? 'default' : 'outline'}
                onClick={() => setNewProfile({ ...newProfile, is_male: true })}
              >
                男
              </Button>
              <Button
                variant={!newProfile.is_male ? 'default' : 'outline'}
                onClick={() => setNewProfile({ ...newProfile, is_male: false })}
              >
                女/其他
              </Button>
            </div>
            <Input
              value={newProfile.timezone}
              onChange={e => setNewProfile({ ...newProfile, timezone: e.target.value })}
              placeholder="时区，如 America/Los_Angeles"
              className="bg-slate-800 border-slate-700"
            />
            <Button className="w-full bg-emerald-600 hover:bg-emerald-500" onClick={handleCreateSession}>
              创建
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ================= Helpers & Components =================

function groupSessions(sessions: ChatSession[]) {
  const now = new Date()
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const oneDay = 24 * 60 * 60 * 1000
  const buckets = { today: [] as ChatSession[], yesterday: [] as ChatSession[], prev7: [] as ChatSession[], older: [] as ChatSession[] }
  for (const s of sessions) {
    const ts = new Date(s.updated_at || s.created_at).getTime()
    const diff = startOfToday - new Date(ts).setHours(0,0,0,0)
    if (diff <= 0) buckets.today.push(s)
    else if (diff <= oneDay) buckets.yesterday.push(s)
    else if (diff <= 7 * oneDay) buckets.prev7.push(s)
    else buckets.older.push(s)
  }
  const sortByTime = (arr: ChatSession[]) => arr.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
  return {
    today: sortByTime(buckets.today),
    yesterday: sortByTime(buckets.yesterday),
    prev7: sortByTime(buckets.prev7),
    older: sortByTime(buckets.older),
  }
}

function sectionLabel(key: string) {
  switch (key) {
    case 'today': return 'Today'
    case 'yesterday': return 'Yesterday'
    case 'prev7': return 'Previous 7 days'
    default: return 'Older'
  }
}

function SessionSection({
  label,
  sessions,
  activeId,
  onSelect,
  onDelete,
  onRename,
}: {
  label: string
  sessions: ChatSession[]
  activeId: string | null
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onRename: (id: string, title: string) => void
}) {
  if (!sessions || sessions.length === 0) return null
  return (
    <div className="px-2 py-2">
      <div className="text-xs text-slate-500 px-2 mb-1">{label}</div>
      {sessions.map(s => (
        <SessionItem key={s.id} session={s} active={s.id === activeId} onSelect={onSelect} onDelete={onDelete} onRename={onRename} />
      ))}
    </div>
  )
}

function SessionItem({
  session,
  active,
  onSelect,
  onDelete,
  onRename,
}: {
  session: ChatSession
  active: boolean
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onRename: (id: string, title: string) => void
}) {
  const [hover, setHover] = useState(false)
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(session.title)

  const save = () => {
    onRename(session.id, title.trim() || 'Untitled')
    setEditing(false)
  }

  return (
    <div
      className={`flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer ${active ? 'bg-slate-800' : 'hover:bg-slate-800/60'}`}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onClick={() => onSelect(session.id)}
    >
      {editing ? (
        <input
          autoFocus
          value={title}
          onChange={e => setTitle(e.target.value)}
          onBlur={save}
          onKeyDown={e => { if (e.key === 'Enter') save() }}
          className="bg-slate-900 text-sm px-2 py-1 rounded border border-slate-700 w-full"
        />
      ) : (
        <div className="flex-1 text-sm truncate">{session.title}</div>
      )}
      {hover && (
        <div className="flex gap-2 text-slate-400 text-xs">
          <button onClick={e => { e.stopPropagation(); setEditing(true) }}>✎</button>
          <button onClick={e => { e.stopPropagation(); onDelete(session.id) }}>🗑</button>
        </div>
      )}
    </div>
  )
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const align = msg.role === 'user' ? 'justify-end' : 'justify-start'
  const bubble = msg.role === 'user' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-100'
  const parts = parseMarkdownLike(msg.content)

  return (
    <div className={`flex ${align}`}>
      <div className={`max-w-[80%] rounded-lg px-4 py-2 whitespace-pre-wrap ${bubble}`}>
        {parts.map((p, i) =>
          p.type === 'code' ? (
            <CodeBlock key={i} code={p.text} lang={p.lang} />
          ) : (
            <span key={i}>{p.text}</span>
          )
        )}
      </div>
    </div>
  )
}

function CodeBlock({ code, lang }: { code: string; lang?: string }) {
  const copy = () => navigator.clipboard?.writeText(code)
  return (
    <div className="mt-2 bg-slate-950 border border-slate-800 rounded">
      <div className="flex items-center justify-between px-3 py-1 text-xs text-slate-400">
        <span>{lang || 'code'}</span>
        <button onClick={copy} className="text-cyan-400 hover:text-cyan-300">Copy</button>
      </div>
      <pre className="overflow-auto text-sm p-3 text-slate-100 whitespace-pre-wrap">{code}</pre>
    </div>
  )
}

function parseMarkdownLike(text: string): Array<{ type: 'text' | 'code'; text: string; lang?: string }> {
  const regex = /```(\w+)?\n([\s\S]*?)```/g
  const parts: Array<{ type: 'text' | 'code'; text: string; lang?: string }> = []
  let last = 0
  let m: RegExpExecArray | null
  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) {
      parts.push({ type: 'text', text: text.slice(last, m.index) })
    }
    parts.push({ type: 'code', text: m[2], lang: m[1] })
    last = regex.lastIndex
  }
  if (last < text.length) parts.push({ type: 'text', text: text.slice(last) })
  return parts
}

function DebugDrawer({
  messages,
  activeTab,
  onTabChange,
}: {
  messages: ChatMessage[]
  activeTab: 'router' | 'facts' | 'index'
  onTabChange: (v: 'router' | 'facts' | 'index') => void
}) {
  const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant' && m.debug?.context_trace)
  if (!lastAssistant?.debug?.context_trace) {
    return (
      <div className="w-96 border-l border-slate-800 bg-[#0b1224] text-slate-400 p-4">
        无调试数据
      </div>
    )
  }
  const ct = lastAssistant.debug.context_trace
  const indexData = lastAssistant.debug.index
  const factsBlocks = ct.used_blocks.filter(b => b.kind === 'facts' && b.used)
  const indexBlocks = ct.used_blocks.filter(b => b.kind === 'index' && b.used)

  return (
    <div className="w-96 border-l border-slate-800 bg-[#0b1224] text-sm flex flex-col">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="text-slate-300">Debug</div>
      </div>
      <div className="flex-1 overflow-auto">
        <Tabs value={activeTab} onValueChange={v => onTabChange(v as any)} className="w-full">
          <TabsList className="bg-slate-800 h-8">
            <TabsTrigger value="router" className="text-xs h-6">Router</TabsTrigger>
            <TabsTrigger value="facts" className="text-xs h-6">Facts</TabsTrigger>
            <TabsTrigger value="index" className="text-xs h-6">Index</TabsTrigger>
          </TabsList>

          <TabsContent value="router" className="p-3 space-y-3">
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-3 text-xs space-y-1">
                <div>Router ID: <span className="text-cyan-400 font-mono">{ct.router.router_id}</span></div>
                <div>Intent: <span className="text-yellow-400 font-mono">{ct.router.intent}</span></div>
                <div>Mode: <span className="text-green-400">{ct.router.mode}</span></div>
                <div>Reason: <span className="text-slate-300">{ct.router.reason}</span></div>
              </CardContent>
            </Card>

            <div className="bg-slate-900 p-3 rounded border border-slate-800">
              <div className="text-slate-500 text-xs mb-1">LLM Context Order</div>
              <div className="flex gap-2 flex-wrap">
                {ct.context_order.map((b, i) => (
                  <span key={i} className="bg-cyan-900/40 text-cyan-300 px-2 py-0.5 rounded text-xs">
                    {i + 1}. {b}
                  </span>
                ))}
              </div>
            </div>

            {ct.index_usage.index_hits.length > 0 && (
              <div className="bg-slate-900 p-3 rounded border border-slate-800">
                <div className="text-slate-500 text-xs mb-1">Index Hits</div>
                <div className="text-xs font-mono text-blue-300">
                  [{ct.index_usage.index_hits.join(', ')}]
                </div>
              </div>
            )}

            {ct.facts_selection.selected_facts_paths.length > 0 && (
              <div className="bg-slate-900 p-3 rounded border border-slate-800">
                <div className="text-slate-500 text-xs mb-1">Selected Facts Paths</div>
                <div className="text-xs font-mono text-cyan-300 space-y-1 max-h-32 overflow-auto">
                  {ct.facts_selection.selected_facts_paths.map((p, i) => (
                    <div key={i}>{p}</div>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="facts" className="p-3 space-y-3">
            <div className="bg-slate-900 p-2 rounded border border-slate-800 text-xs text-slate-400">
              Blocks: {factsBlocks.length}
            </div>
            {factsBlocks.length === 0 ? (
              <div className="text-slate-500 text-xs">本次无 Facts blocks</div>
            ) : (
              factsBlocks.map((b, i) => (
                <Accordion key={i} type="single" collapsible className="w-full">
                  <AccordionItem value={b.block_id} className="border-slate-800">
                    <AccordionTrigger className="text-xs py-2">
                      <div className="flex items-center gap-2 text-left w-full">
                        <span className="text-green-400">✓</span>
                        <span className="text-cyan-400 font-mono">{b.block_type}</span>
                        {b.year && <span className="text-yellow-400">{b.year}年</span>}
                        <span className="text-slate-500 ml-auto">{b.chars_total} chars</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-2 text-xs">
                        {b.reason && <div className="text-slate-500">Reason: {b.reason}</div>}
                        <div className="bg-slate-950 p-2 rounded">
                          <div className="text-slate-500 mb-1">Preview (<=600 chars)</div>
                          <pre className="text-slate-200 whitespace-pre-wrap break-words">{b.preview}</pre>
                        </div>
                        {b.full_text && b.full_text.length > b.preview.length && (
                          <details className="text-xs">
                            <summary className="text-cyan-400 cursor-pointer">展开全文 ({b.chars_total} chars)</summary>
                            <pre className="mt-2 bg-slate-950 p-2 rounded text-slate-200 whitespace-pre-wrap break-words max-h-64 overflow-auto">
                              {b.full_text}
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

          <TabsContent value="index" className="p-3 space-y-3">
            <div className="bg-slate-900 p-2 rounded border border-slate-800 text-xs text-slate-400">
              Used index blocks: {indexBlocks.length}
            </div>
            {indexBlocks.length > 0 && (
              <div className="space-y-2">
                {indexBlocks.map((b, i) => (
                  <div key={i} className="bg-slate-900 p-2 rounded border border-slate-800 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-blue-400">✓</span>
                      <span className="text-cyan-400 font-mono">{b.block_type}</span>
                      {b.reason && <span className="text-slate-500 italic ml-2">{b.reason}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="full-index" className="border-slate-800">
                <AccordionTrigger className="text-xs py-2">Full Index (raw)</AccordionTrigger>
                <AccordionContent>
                  <pre className="text-xs bg-slate-950 p-2 rounded overflow-auto max-h-48 text-slate-200">
                    {indexData ? JSON.stringify(indexData, null, 2) : '(no index data)'}
                  </pre>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

function autoTitleFromText(text: string) {
  const t = text.replace(/\\s+/g, ' ').trim()
  return t.slice(0, 30) || 'Untitled'
}
