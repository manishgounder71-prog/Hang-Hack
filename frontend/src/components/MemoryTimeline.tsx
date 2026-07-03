'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Brain, 
  BookOpen, 
  FolderOpen,
  Star,
  Zap,
} from 'lucide-react'
import { api } from '@/lib/api'

interface MemoryEvent {
  id: string
  content: string
  content_type: string
  importance_score: number
  tags: string[]
  created_at: string
}

const iconMap: Record<string,any> = {
  project: FolderOpen,
  learning: BookOpen,
  achievement: Star,
  skill: Star,
  research: Brain,
  milestone: Zap,
  chat_message: BookOpen,
  chat_response: Brain,
  default: Brain,
}

function getTimeAgo(dateStr: string): string {
  if (!dateStr) return 'recently'
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = now - then
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'yesterday'
  if (days < 30) return `${days}d ago`
  return new Date(dateStr).toLocaleDateString()
}

export default function MemoryTimeline({ compact = false }: { compact?: boolean }) {
  const [events, setEvents] = useState<MemoryEvent[]>([])

  useEffect(() => {
    api.memories.list('', compact ? 4 : 20).then(data => {
      if (data?.memories) setEvents(data.memories)
    }).catch(() => {
      // Fallback to empty on error
    })
  }, [compact])

  if (events.length === 0) {
    return (
      <div className="text-center py-6">
        <Brain className="w-8 h-8 text-gray-600 mx-auto mb-2" />
        <p className="text-xs text-gray-600">No memories yet. Start chatting to build your timeline.</p>
      </div>
    )
  }

  return (
    <div className="relative">
      <div className="absolute left-5 top-0 bottom-0 w-px bg-gradient-to-b from-blue-500/50 via-purple-500/50 to-transparent" />

      <div className="space-y-4">
        {events.map((event, i) => {
          const Icon = iconMap[event.content_type] || iconMap.default
          return (
            <motion.div
              key={event.id || i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="relative pl-12"
            >
              <div className="absolute left-3.5 top-1 w-3 h-3 rounded-full neural-gradient z-10" />

              <div className="glass rounded-xl p-3 hover:glass-hover transition-all">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg neural-gradient flex items-center justify-center flex-shrink-0">
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{event.content?.slice(0, 60) || 'Memory'}</p>
                    <p className="text-xs text-gray-500">{getTimeAgo(event.created_at)}</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
