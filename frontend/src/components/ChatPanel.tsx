'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Brain, Sparkles, User } from 'lucide-react'
import { api } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  memories_used?: string[]
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="glass rounded-2xl rounded-bl-md px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <div key={i} className="w-1.5 h-1.5 rounded-full bg-blue-400 typing-dot" />
            ))}
          </div>
          <span className="text-[10px] text-gray-500 ml-1">Genesis is thinking...</span>
        </div>
      </div>
    </div>
  )
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hello! I'm Genesis, your self-evolving AI. I remember everything we've discussed and I get smarter with every conversation. What can I help you with?",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMsg: Message = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const data = await api.chat.send(input)

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response || "I've processed your request and stored it in my memory.",
          memories_used: data.memories_used,
        },
      ])
      setLoading(false)
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '⚠️ Connection error — Could not reach the backend. Please check that the server is running and try again.',
          memories_used: [],
        },
      ])
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-3 space-y-3 scrollbar-thin">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex gap-2 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${
                msg.role === 'user'
                  ? 'bg-gradient-to-br from-blue-500 to-purple-500'
                  : 'glass-strong'
              }`}>
                {msg.role === 'user' ? (
                  <User className="w-3.5 h-3.5 text-white" />
                ) : (
                  <Brain className="w-3.5 h-3.5 text-blue-400" />
                )}
              </div>
              <div>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-tr-md'
                      : 'glass rounded-tl-md'
                  }`}
                >
                  {msg.content}
                </div>
                {msg.memories_used && msg.memories_used.length > 0 && (
                  <div className="flex items-center gap-1 mt-1 ml-1">
                    <Sparkles className="w-3 h-3 text-amber-400" />
                    <span className="text-[10px] text-gray-600">{msg.memories_used.length} memories recalled</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 border-t border-white/5">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Type a message..."
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500/40 focus:bg-white/[0.06] transition-all placeholder:text-gray-600"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="w-9 h-9 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center disabled:opacity-40 hover:scale-105 active:scale-95 transition-all flex-shrink-0"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>
    </div>
  )
}
