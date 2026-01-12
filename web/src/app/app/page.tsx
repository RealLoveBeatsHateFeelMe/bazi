'use client'

import { useEffect, useState, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'
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
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useRouter } from 'next/navigation'
import type { Profile, Session, Message, ChatResponse } from '@/lib/types'

export default function AppPage() {
  const router = useRouter()
  const supabase = createClient()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // State
  const [user, setUser] = useState<{ id: string; email?: string } | null>(null)
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [debugData, setDebugData] = useState<Record<string, ChatResponse>>({})

  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null)
  const [selectedSession, setSelectedSession] = useState<Session | null>(null)
  
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  // New profile form
  const [showNewProfile, setShowNewProfile] = useState(false)
  const [newProfileForm, setNewProfileForm] = useState({
    display_name: '',
    birth_date: '',
    birth_time: '',
    is_male: true,
  })

  // Initialize
  useEffect(() => {
    const init = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        router.push('/login')
        return
      }
      setUser(user)
      await loadProfiles(user.id)
    }
    init()
  }, [])

  // Load profiles
  const loadProfiles = async (userId: string) => {
    const { data } = await supabase
      .from('profiles')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
    
    if (data) {
      setProfiles(data)
      if (data.length > 0 && !selectedProfile) {
        setSelectedProfile(data[0])
      }
    }
  }

  // Load sessions for profile
  useEffect(() => {
    if (selectedProfile) {
      loadSessions(selectedProfile.id)
    }
  }, [selectedProfile])

  const loadSessions = async (profileId: string) => {
    const { data } = await supabase
      .from('sessions')
      .select('*')
      .eq('profile_id', profileId)
      .order('created_at', { ascending: false })
    
    if (data) {
      setSessions(data)
      if (data.length > 0) {
        setSelectedSession(data[0])
      } else {
        setSelectedSession(null)
        setMessages([])
      }
    }
  }

  // Load messages for session
  useEffect(() => {
    if (selectedSession) {
      loadMessages(selectedSession.id)
    }
  }, [selectedSession])

  const loadMessages = async (sessionId: string) => {
    const { data } = await supabase
      .from('messages')
      .select('*')
      .eq('session_id', sessionId)
      .order('created_at', { ascending: true })
    
    if (data) {
      setMessages(data)
    }
  }

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Create profile
  const createProfile = async () => {
    if (!user || !newProfileForm.display_name || !newProfileForm.birth_date || !newProfileForm.birth_time) {
      return
    }

    const { data, error } = await supabase
      .from('profiles')
      .insert({
        user_id: user.id,
        display_name: newProfileForm.display_name,
        birth_date: newProfileForm.birth_date,
        birth_time: newProfileForm.birth_time,
        is_male: newProfileForm.is_male,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      })
      .select()
      .single()

    if (data) {
      setProfiles([data, ...profiles])
      setSelectedProfile(data)
      setShowNewProfile(false)
      setNewProfileForm({ display_name: '', birth_date: '', birth_time: '', is_male: true })
    }

    if (error) {
      console.error('Error creating profile:', error)
    }
  }

  // Create session
  const createSession = async () => {
    if (!selectedProfile) return

    const { data, error } = await supabase
      .from('sessions')
      .insert({
        profile_id: selectedProfile.id,
        title: `对话 ${new Date().toLocaleDateString()}`,
      })
      .select()
      .single()

    if (data) {
      setSessions([data, ...sessions])
      setSelectedSession(data)
      setMessages([])
    }

    if (error) {
      console.error('Error creating session:', error)
    }
  }

  // Send message
  const sendMessage = async () => {
    if (!selectedSession || !inputMessage.trim() || isLoading) return

    const messageText = inputMessage.trim()
    setInputMessage('')
    setIsLoading(true)

    // Optimistic update
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      session_id: selectedSession.id,
      role: 'user',
      content: messageText,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempUserMessage])

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: selectedSession.id,
          message: messageText,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const data: ChatResponse = await response.json()

      // Reload messages
      await loadMessages(selectedSession.id)

      // Store debug data
      const lastMessage = messages[messages.length - 1]
      if (lastMessage) {
        setDebugData(prev => ({
          ...prev,
          [lastMessage.id]: data,
        }))
      }
    } catch (error) {
      console.error('Error sending message:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Logout
  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white flex">
      {/* Sidebar */}
      <div className="w-72 bg-slate-800 border-r border-slate-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-slate-700">
          <h1 className="text-xl font-bold">🔮 Hayyy 八字</h1>
          <p className="text-xs text-slate-400 mt-1">{user?.email}</p>
        </div>

        {/* Profiles */}
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-400">档案</span>
            <Dialog open={showNewProfile} onOpenChange={setShowNewProfile}>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm" className="h-6 text-xs">+ 新建</Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-800 border-slate-700">
                <DialogHeader>
                  <DialogTitle className="text-white">新建档案</DialogTitle>
                  <DialogDescription className="text-slate-400">
                    输入出生信息来创建档案
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <Input
                    placeholder="名称"
                    value={newProfileForm.display_name}
                    onChange={e => setNewProfileForm({ ...newProfileForm, display_name: e.target.value })}
                    className="bg-slate-700 border-slate-600"
                  />
                  <Input
                    type="date"
                    value={newProfileForm.birth_date}
                    onChange={e => setNewProfileForm({ ...newProfileForm, birth_date: e.target.value })}
                    className="bg-slate-700 border-slate-600"
                  />
                  <Input
                    type="time"
                    value={newProfileForm.birth_time}
                    onChange={e => setNewProfileForm({ ...newProfileForm, birth_time: e.target.value })}
                    className="bg-slate-700 border-slate-600"
                  />
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
                  <Button onClick={createProfile} className="w-full">创建</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          <div className="space-y-1">
            {profiles.map(profile => (
              <button
                key={profile.id}
                onClick={() => setSelectedProfile(profile)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedProfile?.id === profile.id
                    ? 'bg-purple-600 text-white'
                    : 'hover:bg-slate-700 text-slate-300'
                }`}
              >
                {profile.display_name}
              </button>
            ))}
          </div>
        </div>

        {/* Sessions */}
        <div className="flex-1 p-4 overflow-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-400">对话</span>
            <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={createSession}>
              + 新建
            </Button>
          </div>
          <div className="space-y-1">
            {sessions.map(session => (
              <button
                key={session.id}
                onClick={() => setSelectedSession(session)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedSession?.id === session.id
                    ? 'bg-slate-700 text-white'
                    : 'hover:bg-slate-700/50 text-slate-400'
                }`}
              >
                {session.title || '未命名对话'}
              </button>
            ))}
          </div>
        </div>

        {/* Logout */}
        <div className="p-4 border-t border-slate-700">
          <Button variant="ghost" onClick={handleLogout} className="w-full">
            退出登录
          </Button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedSession ? (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-auto p-6 space-y-4">
              {messages.map((msg, index) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  debugData={debugData[msg.id]}
                  isLast={index === messages.length - 1}
                />
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
            <div className="p-4 border-t border-slate-700">
              <div className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={e => setInputMessage(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && sendMessage()}
                  placeholder="输入问题，例如：今年运势怎么样？"
                  className="flex-1 bg-slate-800 border-slate-600"
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
            {selectedProfile ? (
              <div className="text-center">
                <p className="mb-4">还没有对话</p>
                <Button onClick={createSession}>开始新对话</Button>
              </div>
            ) : (
              <p>请先创建一个档案</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Message Bubble Component
function MessageBubble({ 
  message, 
  debugData,
  isLast 
}: { 
  message: Message
  debugData?: ChatResponse
  isLast: boolean 
}) {
  const isUser = message.role === 'user'
  const [showDebug, setShowDebug] = useState(false)

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[70%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`rounded-lg px-4 py-3 ${
            isUser
              ? 'bg-purple-600 text-white'
              : 'bg-slate-700 text-slate-100'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        
        {/* Debug Button for Assistant Messages */}
        {!isUser && debugData && (
          <div className="mt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDebug(!showDebug)}
              className="text-xs text-slate-400 hover:text-white"
            >
              {showDebug ? '隐藏 Debug' : '🔍 Debug'}
            </Button>
            
            {showDebug && (
              <DebugPanel data={debugData} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Debug Panel Component
function DebugPanel({ data }: { data: ChatResponse }) {
  return (
    <Card className="mt-2 bg-slate-800 border-slate-600">
      <CardContent className="p-4">
        <Tabs defaultValue="router" className="w-full">
          <TabsList className="bg-slate-700">
            <TabsTrigger value="router">Router</TabsTrigger>
            <TabsTrigger value="modules">Modules</TabsTrigger>
            <TabsTrigger value="index">Index</TabsTrigger>
            <TabsTrigger value="facts">Facts</TabsTrigger>
          </TabsList>
          
          <TabsContent value="router" className="mt-4">
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="trace" className="border-slate-600">
                <AccordionTrigger className="text-sm">Router Trace</AccordionTrigger>
                <AccordionContent>
                  <pre className="text-xs bg-slate-900 p-3 rounded overflow-auto max-h-60">
                    {JSON.stringify(data.router_trace, null, 2)}
                  </pre>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </TabsContent>
          
          <TabsContent value="modules" className="mt-4">
            <pre className="text-xs bg-slate-900 p-3 rounded overflow-auto max-h-60">
              {JSON.stringify(data.modules_trace, null, 2)}
            </pre>
          </TabsContent>
          
          <TabsContent value="index" className="mt-4">
            <div className="space-y-2">
              <div className="text-sm text-slate-400">
                Slices used: {data.index_trace.slices_used.join(', ')}
              </div>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="payload" className="border-slate-600">
                  <AccordionTrigger className="text-sm">Slices Payload</AccordionTrigger>
                  <AccordionContent>
                    <pre className="text-xs bg-slate-900 p-3 rounded overflow-auto max-h-60">
                      {JSON.stringify(data.index_trace.slices_payload, null, 2)}
                    </pre>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>
          </TabsContent>
          
          <TabsContent value="facts" className="mt-4">
            <div className="space-y-2 text-sm">
              <div className="text-slate-400">
                Source: {data.facts_trace.facts_source}
              </div>
              <div className="text-slate-400">
                Available: {data.facts_trace.facts_available_count}
              </div>
              <div className="text-slate-400">
                Used: {data.facts_trace.facts_used.length}
              </div>
            </div>
          </TabsContent>
        </Tabs>
        
        {/* Timing */}
        <div className="mt-4 text-xs text-slate-500 flex gap-4">
          <span>Router: {data.run_meta.timing_ms.router}ms</span>
          <span>Engine: {data.run_meta.timing_ms.engine}ms</span>
          <span>LLM: {data.run_meta.timing_ms.llm}ms</span>
        </div>
      </CardContent>
    </Card>
  )
}

