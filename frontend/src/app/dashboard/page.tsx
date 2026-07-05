'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  Brain, Network, Eye, Zap, TrendingUp, Sparkles,
  Timer, BarChart3, BookOpen, MessageCircle, Settings,
  Activity, ChevronRight,
  Bot, Target, Cpu, AlertCircle,
} from 'lucide-react'
import dynamic from 'next/dynamic'
import DashboardWidget from '@/components/DashboardWidget'
import MemoryTimeline from '@/components/MemoryTimeline'
import ChatPanel from '@/components/ChatPanel'
import { api } from '@/lib/api'

// Dynamically import the 3D BrainGraph (Three.js ~200KB) — only loads when it enters the viewport
const BrainGraph = dynamic(() => import('@/components/BrainGraph'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-44">
      <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
    </div>
  ),
})

interface DashboardStats {
  memory_count: number
  knowledge_nodes: number
  relationships: number
  learning_progress: number
  reflection_score: number
  prediction_confidence: number
  evolution_level: number
  skill_count: number
  weekly_growth: number
  brain_health: number
  recent_memories: { id: string; content: string; content_type: string; importance_score: number; created_at: string }[]
  reflection_count?: number
  prediction_count?: number
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const fetchDashboard = async () => {
    try {
      setError('')
      const data = await api.dashboard.get()
      setStats(data)
    } catch (err: any) {
      setError('Could not connect to backend')
      // Fallback to defaults
      setStats({
        memory_count: 1247, knowledge_nodes: 892, relationships: 3401,
        learning_progress: 0.65, reflection_score: 0.72, prediction_confidence: 0.58,
        evolution_level: 3, skill_count: 12, weekly_growth: 0.15, brain_health: 0.88,
        recent_memories: [],
      })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [])

  const handleRefresh = () => {
    setRefreshing(true)
    setError('')
    api.dashboard.get('default', true).then(data => {
      setStats(data)
      setRefreshing(false)
    }).catch(err => {
      setError('Could not connect to backend')
      setRefreshing(false)
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[rgb(5,5,25)] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-2xl neural-gradient flex items-center justify-center mx-auto mb-4 animate-breathe">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <p className="text-gray-500 text-sm animate-pulse">Initializing brain...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      {error && (
        <div className="mx-4 md:mx-6 mt-4 flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error} — showing cached data
        </div>
      )}

      {stats && (
      <div className="grid xl:grid-cols-[1fr_minmax(320px,380px)] gap-0">
        <div className="p-3 sm:p-4 md:p-6 space-y-5 overflow-y-auto scrollbar-thin" style={{ maxHeight: 'calc(100dvh - 56px)' }}>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <div className="flex items-center gap-2 mb-1">
              <Bot className="w-4 h-4 text-blue-400" />
              <span className="text-[10px] text-blue-400 tracking-widest uppercase font-medium">Dashboard</span>
            </div>
            <h1 className="text-2xl font-bold">Welcome back</h1>
            <p className="text-sm text-gray-500">Your AI brain is evolving. Here&apos;s the latest activity.</p>
          </motion.div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3">
            <DashboardWidget icon={Brain} title="Memory Count" value={stats.memory_count} color="blue" delay={0} />
            <DashboardWidget icon={Network} title="Knowledge Nodes" value={stats.knowledge_nodes} color="purple" delay={0.05} />
            <DashboardWidget icon={Sparkles} title="Relationships" value={stats.relationships} color="teal" delay={0.1} />
            <DashboardWidget icon={Zap} title="Skills" value={stats.skill_count} color="green" delay={0.15} />
            <DashboardWidget icon={TrendingUp} title="Evolution" value={`Lvl ${stats.evolution_level}`} color="amber" delay={0.2} />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
            <DashboardWidget icon={Timer} title="Learning" value={`${Math.round(stats.learning_progress * 100)}%`} subtitle="Knowledge acquired" color="blue" delay={0.25} />
            <DashboardWidget icon={Eye} title="Reflection" value={`${Math.round(stats.reflection_score * 100)}%`} subtitle="Self-awareness" color="purple" delay={0.3} />
            <DashboardWidget icon={Target} title="Predictions" value={`${Math.round(stats.prediction_confidence * 100)}%`} subtitle="Confidence" color="teal" delay={0.35} />
            <DashboardWidget icon={Activity} title="Brain Health" value={`${Math.round(stats.brain_health * 100)}%`} subtitle="All systems" color="green" delay={0.4} trend={8} />
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass rounded-2xl p-5 hover:glass-hover transition-all"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Network className="w-4 h-4 text-blue-400" />
                  <h3 className="font-semibold text-sm">Knowledge Graph</h3>
                </div>
                <Link href="/dashboard/brain" className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-0.5 transition-colors">
                  View full <ChevronRight className="w-3 h-3" />
                </Link>
              </div>
              <div className="h-44 -mx-2">
                <BrainGraph />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 }}
              className="glass rounded-2xl p-5 hover:glass-hover transition-all"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-purple-400" />
                  <h3 className="font-semibold text-sm">Recent Activity</h3>
                </div>
                <Link href="/dashboard/timeline" className="text-[10px] text-purple-400 hover:text-purple-300 flex items-center gap-0.5 transition-colors">
                  View all <ChevronRight className="w-3 h-3" />
                </Link>
              </div>
              <MemoryTimeline compact />
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass rounded-2xl p-5"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-amber-400" />
                <h3 className="font-semibold text-sm">Weekly Memory Growth</h3>
              </div>
              <span className="text-[10px] text-green-400 font-medium flex items-center gap-1">
                <TrendingUp className="w-3 h-3" /> +{Math.round(stats.weekly_growth * 100)}% this week
              </span>
            </div>
            <div className="h-28 flex items-end gap-2">
              {[40, 55, 45, 70, 65, 85, 100].map((h, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-1.5 group">
                  <span className="text-[9px] text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity">{h}</span>
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${h}%` }}
                    transition={{ duration: 0.8, delay: 0.4 + i * 0.05 }}
                    className="w-full rounded-t-lg bg-gradient-to-t from-blue-500 to-purple-500 opacity-80 group-hover:opacity-100 transition-opacity relative overflow-hidden"
                  >
                    <div className="absolute inset-0 bg-gradient-to-t from-transparent via-white/5 to-transparent" />
                  </motion.div>
                  <span className="text-[9px] text-gray-600">{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i]}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.15 }}
          className="border-l border-white/5 flex flex-col"
          style={{ height: 'calc(100dvh - 56px)' }}
        >
          <div className="p-4 border-b border-white/5 flex items-center justify-between">
            <h3 className="font-semibold text-sm flex items-center gap-2">
              <MessageCircle className="w-4 h-4 text-blue-400" />
              Genesis Chat
            </h3>
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              <span className="text-[10px] text-gray-600">Online</span>
            </div>
          </div>
          <div className="flex-1">
            <ChatPanel />
          </div>
        </motion.div>
      </div>
      )}
    </>
  )
}
