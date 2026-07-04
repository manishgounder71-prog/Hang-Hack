'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Brain, BookOpen, FolderOpen, Star, Clock, Target, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'

interface TimelineEvent {
  id: string
  content: string
  content_type: string
  importance_score: number
  tags: string[]
  created_at: string
}

const typeConfig: Record<string, { icon: typeof Brain; gradient: string; color: string }> = {
  'file:': { icon: FolderOpen, gradient: 'from-blue-500/20 to-blue-600/10', color: 'text-blue-400' },
  'chat_message': { icon: BookOpen, gradient: 'from-purple-500/20 to-purple-600/10', color: 'text-purple-400' },
  'chat_response': { icon: Brain, gradient: 'from-teal-500/20 to-teal-600/10', color: 'text-teal-400' },
  'reflection': { icon: Brain, gradient: 'from-purple-500/20 to-purple-600/10', color: 'text-purple-400' },
  'prediction': { icon: Target, gradient: 'from-amber-500/20 to-amber-600/10', color: 'text-amber-400' },
  'skill': { icon: Star, gradient: 'from-green-500/20 to-green-600/10', color: 'text-green-400' },
  'default': { icon: BookOpen, gradient: 'from-blue-500/20 to-blue-600/10', color: 'text-blue-400' },
}

export default function TimelinePage() {
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchEvents = async () => {
    try {
      setError('')
      const data = await api.memories.list('', 50)
      setEvents(data.memories || [])
    } catch {
      setError('Could not load timeline')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchEvents() }, [])

  return (
    <div className="max-w-3xl mx-auto p-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-4 h-4 text-purple-400" />
            <span className="text-[10px] text-purple-400 tracking-widest uppercase font-medium">History</span>
          </div>
          <h1 className="text-2xl font-bold mb-1">Your Evolution Story</h1>
          <p className="text-sm text-gray-500 mb-6">Every important moment that shaped your journey</p>
        </motion.div>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs mb-4">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </motion.div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-20">
            <BookOpen className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 text-sm">No memories yet. Start chatting to build your timeline.</p>
          </div>
        ) : (
          <div className="relative">
            <div className="absolute left-7 top-0 bottom-0 w-px bg-gradient-to-b from-blue-500/40 via-purple-500/30 to-teal-500/20" />
            <div className="space-y-5">
              {events.map((event, i) => {
                const typeKey = Object.keys(typeConfig).find(k => event.content_type?.startsWith(k)) || event.content_type || 'default'
                const config = typeConfig[typeKey] || typeConfig.default
                const Icon = config.icon
                return (
                  <motion.div
                    key={event.id || i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03, duration: 0.3 }}
                    className="relative pl-16"
                  >
                    <div className="absolute left-4 top-2 w-6 h-6 rounded-full bg-gradient-to-b from-blue-600 to-purple-600 z-10 flex items-center justify-center border-2 border-[rgb(5,5,25)]">
                      <div className="w-1.5 h-1.5 rounded-full bg-white" />
                    </div>
                    <motion.div
                      whileHover={{ scale: 1.01, x: 2 }}
                      className="glass rounded-2xl p-5 hover:glass-hover transition-all duration-300 card-shine"
                    >
                      <div className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${config.gradient} flex items-center justify-center flex-shrink-0`}>
                          <Icon className={`w-5 h-5 ${config.color}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <h3 className="font-semibold text-sm">{event.content?.slice(0, 80)}</h3>
                              <p className="text-xs text-gray-500 mt-1 leading-relaxed">{event.content?.slice(0, 200)}</p>
                            </div>
                            <span className="text-[10px] text-gray-600 whitespace-nowrap flex-shrink-0">
                              {event.created_at ? new Date(event.created_at).toLocaleDateString() : ''}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 mt-3">
                            <span className={`text-[9px] px-2 py-0.5 rounded-full border text-gray-400 border-white/10 bg-white/5`}>
                              {event.content_type || 'memory'}
                            </span>
                            {event.importance_score && (
                              <span className="text-[9px] text-gray-600">Importance: {Math.round(event.importance_score * 100)}%</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  </motion.div>
                )
              })}
            </div>
          </div>
        )}
    </div>
  )
}
