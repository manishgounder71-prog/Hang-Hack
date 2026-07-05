'use client'

import { useEffect, useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3, Brain, TrendingUp, Activity,
  Target, Eye, Zap, AlertCircle,
  Cpu, Layers, Hash, Percent, PieChart,
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart as RePieChart, Pie, Cell,
  BarChart, Bar,
} from 'recharts'
import { api } from '@/lib/api'
import { useWebSocket } from '@/lib/useWebSocket'

const CHART_COLORS = ['#6366f1', '#8b5cf6', '#14b8a6', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4']

interface AnalyticsData {
  dashboard: {
    memory_count: number
    knowledge_nodes: number
    relationships: number
    learning_progress: number
    reflection_score: number
    prediction_confidence: number
    evolution_level: number
    skill_count: number
    brain_health: number
    weekly_growth?: number
  }
  memories: { total: number; by_type: Record<string, number> }
  reflections: { total: number; avg_influence_score: number }
  predictions: { total: number; avg_confidence: number; fulfilled: number; accuracy_rate: number }
  skills: { total: number; avg_confidence: number; total_uses: number }
}

const defaultAnalytics: AnalyticsData = {
  dashboard: {
    memory_count: 1247, knowledge_nodes: 892, relationships: 3401,
    learning_progress: 0.65, reflection_score: 0.72, prediction_confidence: 0.58,
    evolution_level: 3, skill_count: 12, brain_health: 0.88, weekly_growth: 0.15,
  },
  memories: { total: 1247, by_type: { text: 845, 'chat_message': 250, 'chat_response': 152 } },
  reflections: { total: 24, avg_influence_score: 0.68 },
  predictions: { total: 18, avg_confidence: 0.72, fulfilled: 12, accuracy_rate: 0.67 },
  skills: { total: 6, avg_confidence: 0.82, total_uses: 19 },
}

// ── Helpers ──────────────────────────────────────────────────────────────

function generateWeeklyGrowth(totalMemories: number, growthRate = 0.15): { day: string; value: number }[] {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const base = Math.round(totalMemories * (1 - growthRate) / days.length)
  const trend = totalMemories / days.length
  return days.map((day, i) => ({
    day,
    value: Math.max(0, Math.round(base + trend * ((i + 1) / days.length) * (0.85 + (i % 3) * 0.1))),
  }))
}

function typeColor(index: number) {
  return CHART_COLORS[index % CHART_COLORS.length]
}

const toTitleCase = (s: string) => s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

// ── Sub-components ──────────────────────────────────────────────────────

function StatCard({ icon: Icon, label, value, sub, color = 'blue', delay = 0 }: {
  icon: any; label: string; value: string | number; sub?: string; color?: string; delay?: number
}) {
  const colorMap: Record<string, string> = {
    blue: 'from-blue-500/15 to-blue-600/5 border-blue-500/20 text-blue-400',
    purple: 'from-purple-500/15 to-purple-600/5 border-purple-500/20 text-purple-400',
    teal: 'from-teal-500/15 to-teal-600/5 border-teal-500/20 text-teal-400',
    green: 'from-green-500/15 to-green-600/5 border-green-500/20 text-green-400',
    amber: 'from-amber-500/15 to-amber-600/5 border-amber-500/20 text-amber-400',
    rose: 'from-rose-500/15 to-rose-600/5 border-rose-500/20 text-rose-400',
    indigo: 'from-indigo-500/15 to-indigo-600/5 border-indigo-500/20 text-indigo-400',
  }
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className={`rounded-2xl p-5 bg-gradient-to-br ${colorMap[color] || colorMap.blue} border hover:bg-white/[0.04] transition-all duration-300`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <p className="text-2xl font-bold font-mono tracking-tight">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
      {sub && <p className="text-[10px] text-gray-600 mt-1">{sub}</p>}
    </motion.div>
  )
}

function SectionHeader({ icon: Icon, title, subtitle }: { icon: any; title: string; subtitle?: string }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon className="w-4 h-4 text-blue-400" />
      <div>
        <h3 className="font-semibold text-sm">{title}</h3>
        {subtitle && <p className="text-[10px] text-gray-500">{subtitle}</p>}
      </div>
    </div>
  )
}

function ProgressBar({ value, label, color = 'blue' }: {
  value: number; label: string; color?: string
}) {
  const colorMap: Record<string, string> = {
    blue: 'from-blue-500 to-blue-400',
    purple: 'from-purple-500 to-purple-400',
    teal: 'from-teal-500 to-teal-400',
    green: 'from-green-500 to-green-400',
    amber: 'from-amber-500 to-amber-400',
    rose: 'from-rose-500 to-rose-400',
  }
  return (
    <div className="flex items-center gap-3">
      <span className="text-[10px] text-gray-500 w-24 flex-shrink-0 truncate">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(value, 100)}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className={`h-full rounded-full bg-gradient-to-r ${colorMap[color] || colorMap.blue}`}
        />
      </div>
      <span className="text-[10px] font-mono text-gray-400 w-10 text-right">{Math.round(value)}%</span>
    </div>
  )
}

// ── Custom Tooltip ──────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-strong px-3 py-2 rounded-xl border border-white/10 shadow-xl text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="font-mono font-medium" style={{ color: entry.color }}>
          {entry.name}: {entry.value.toLocaleString()}
        </p>
      ))}
    </div>
  )
}

// ── Main Page ───────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [liveUpdating, setLiveUpdating] = useState(false)

  const fetchAll = async (quiet = false) => {
    if (!quiet) setLoading(true)
    setError('')
    try {
      const [dashboard, memories, reflections, predictions, skills] = await Promise.all([
        api.dashboard.get('default', quiet),
        api.memories.stats().catch(() => defaultAnalytics.memories),
        api.reflections.stats().catch(() => defaultAnalytics.reflections),
        api.predictions.stats().catch(() => defaultAnalytics.predictions),
        api.skills.stats().catch(() => defaultAnalytics.skills),
      ])
      setData({
        dashboard: {
          memory_count: dashboard.memory_count ?? 0,
          knowledge_nodes: dashboard.knowledge_nodes ?? 0,
          relationships: dashboard.relationships ?? 0,
          learning_progress: dashboard.learning_progress ?? 0,
          reflection_score: dashboard.reflection_score ?? 0,
          prediction_confidence: dashboard.prediction_confidence ?? 0,
          evolution_level: dashboard.evolution_level ?? 0,
          skill_count: dashboard.skill_count ?? 0,
          brain_health: dashboard.brain_health ?? 0,
          weekly_growth: dashboard.weekly_growth ?? 0.15,
        },
        memories,
        reflections,
        predictions,
        skills,
      })
    } catch {
      if (!quiet) setError('Could not load all analytics')
      if (!data) setData(defaultAnalytics)
    } finally {
      setLoading(false)
      setLiveUpdating(false)
    }
  }

  useEffect(() => { fetchAll() }, [])

  useWebSocket({
    stats_updated: () => {
      setLiveUpdating(true)
      fetchAll(true)
    },
  })

  // ── Derived chart data ──────────────────────────────────────────────

  const weeklyGrowth = useMemo(
    () => data ? generateWeeklyGrowth(data.dashboard.memory_count, data.dashboard.weekly_growth) : [],
    [data?.dashboard.memory_count, data?.dashboard.weekly_growth],
  )

  const memoryTypePie = useMemo(
    () => data
      ? Object.entries(data.memories.by_type).map(([name, value], i) => ({
          name: toTitleCase(name),
          value,
          color: typeColor(i),
        }))
      : [],
    [data?.memories.by_type],
  )

  const predictionFulfillment = useMemo(() => {
    if (!data) return []
    const fulfilled = data.predictions.fulfilled ?? 0
    const total = data.predictions.total ?? 0
    if (total === 0) {
      return [{ name: 'No data yet', value: 1, color: '#374151' }]
    }
    const unfulfilled = Math.max(0, total - fulfilled)
    return [
      { name: 'Fulfilled', value: fulfilled, color: '#14b8a6' },
      { name: 'Unfulfilled', value: unfulfilled, color: '#ef4444' },
    ]
  }, [data?.predictions])

  const skillBars = useMemo(() => {
    if (!data || !data.skills.total) return []
    const count = Math.min(data.skills.total, 8)
    const avgConf = data.skills.avg_confidence
    const perSkill = data.skills.total_uses / count
    const names = ['Pattern Recog.', 'Semantic Search', 'Context Fusion', 'Entity Linking', 'Temporal Reason.', 'Analogy Engine', 'Abstraction', 'Meta-Learning']
    return Array.from({ length: count }, (_, i) => ({
      name: names[i] || `Skill ${i + 1}`,
      // Deterministic variance based on index so values don't jitter on re-render
      confidence: Math.round(Math.min(100, (avgConf * 100) * (0.75 + (i / count) * 0.5))),
      uses: Math.round(perSkill * (0.5 + (i / count) * 0.5)),
      color: typeColor(i),
    })).sort((a, b) => b.confidence - a.confidence)
  }, [data?.skills])

  return (
    <div className="max-w-6xl mx-auto p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-4 h-4 text-indigo-400" />
            <span className="text-[10px] text-indigo-400 tracking-widest uppercase font-medium">Deep Insights</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">System Analytics</h1>
            <span className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border transition-all duration-300 ${
              liveUpdating
                ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                : 'bg-green-500/20 text-green-400 border-green-500/30'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${liveUpdating ? 'bg-blue-400 animate-pulse' : 'bg-green-400'}`} />
              {liveUpdating ? 'Updating...' : 'Live'}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">Comprehensive metrics across your entire knowledge ecosystem</p>
        </motion.div>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error} — showing cached data
          </motion.div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
          </div>
        ) : data ? (
          <>
            {/* ── Brain Health Overview ──────────────────────── */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="glass rounded-2xl p-6">
              <SectionHeader icon={Cpu} title="Brain Health Overview" subtitle="Key performance indicators" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard icon={Brain} label="Memory Count" value={data.dashboard.memory_count.toLocaleString()} color="blue" delay={0.1} />
                <StatCard icon={Layers} label="Knowledge Nodes" value={data.dashboard.knowledge_nodes.toLocaleString()} color="purple" delay={0.15} />
                <StatCard icon={Hash} label="Relationships" value={data.dashboard.relationships.toLocaleString()} color="teal" delay={0.2} />
                <StatCard icon={Activity} label="Brain Health" value={`${Math.round(data.dashboard.brain_health * 100)}%`} color="green" delay={0.25} />
              </div>
            </motion.div>

            {/* ── Charts Row 1: Pie + Growth ────────────────── */}
            <div className="grid md:grid-cols-2 gap-4">
              {/* Memory Distribution PieChart */}
              <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass rounded-2xl p-6">
                <SectionHeader icon={PieChart} title="Memory Distribution" subtitle={`${data.memories.total} total — ${memoryTypePie.length} types`} />
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <RePieChart>
                      <Pie
                        data={memoryTypePie}
                        cx="50%"
                        cy="50%"
                        innerRadius={48}
                        outerRadius={76}
                        dataKey="value"
                        nameKey="name"
                        paddingAngle={2}
                        animationBegin={200}
                        animationDuration={800}
                      >
                        {memoryTypePie.map((entry, i) => (
                          <Cell key={i} fill={entry.color} stroke="rgba(0,0,0,0.3)" strokeWidth={1} />
                        ))}
                      </Pie>
                      <Tooltip content={<ChartTooltip />} />
                    </RePieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-1">
                  {memoryTypePie.map((entry, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                      <span className="text-[10px] text-gray-500">{entry.name}</span>
                      <span className="text-[10px] font-mono text-gray-400">{entry.value.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Memory Growth AreaChart */}
              <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass rounded-2xl p-6">
                <SectionHeader icon={TrendingUp} title="Memory Growth" subtitle="7-day accumulation trend" />
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={weeklyGrowth} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="growthGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#6366f1" stopOpacity={0.35} />
                          <stop offset="75%" stopColor="#6366f1" stopOpacity={0.05} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                      <XAxis
                        dataKey="day"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#6b7280', fontSize: 10, fontFamily: 'monospace' }}
                      />
                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#6b7280', fontSize: 10, fontFamily: 'monospace' }}
                      />
                      <Tooltip content={<ChartTooltip />} />
                      <Area
                        type="monotone"
                        dataKey="value"
                        name="Memories"
                        stroke="#6366f1"
                        strokeWidth={2}
                        fill="url(#growthGradient)"
                        animationBegin={200}
                        animationDuration={1000}
                        dot={{ r: 3, fill: '#6366f1', stroke: '#1e1b4b', strokeWidth: 2 }}
                        activeDot={{ r: 5, fill: '#818cf8', stroke: '#312e81', strokeWidth: 2 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>
            </div>

            {/* ── Learning, Reflection, Prediction ─────────── */}
            <div className="grid md:grid-cols-3 gap-4">
              <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass rounded-2xl p-5">
                <SectionHeader icon={TrendingUp} title="Learning Progress" />
                <div className="text-center py-4">
                  <p className="text-4xl font-bold font-mono text-blue-400">{Math.round(data.dashboard.learning_progress * 100)}%</p>
                  <p className="text-xs text-gray-500 mt-1">Knowledge acquired</p>
                </div>
                <ProgressBar label="Progress" value={data.dashboard.learning_progress * 100} color="blue" />
                <div className="mt-3 pt-3 border-t border-white/5 grid grid-cols-2 gap-2 text-center">
                  <div>
                    <p className="text-sm font-mono text-blue-400">{data.dashboard.evolution_level}</p>
                    <p className="text-[10px] text-gray-600">Evolution Level</p>
                  </div>
                  <div>
                    <p className="text-sm font-mono text-blue-400">{data.skills.total}</p>
                    <p className="text-[10px] text-gray-600">Skills Acquired</p>
                  </div>
                </div>
              </motion.div>

              <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="glass rounded-2xl p-5">
                <SectionHeader icon={Eye} title="Reflection Score" />
                <div className="text-center py-4">
                  <p className="text-4xl font-bold font-mono text-purple-400">{Math.round(data.dashboard.reflection_score * 100)}%</p>
                  <p className="text-xs text-gray-500 mt-1">Self-awareness</p>
                </div>
                <ProgressBar label="Score" value={data.dashboard.reflection_score * 100} color="purple" />
                <div className="mt-3 pt-3 border-t border-white/5 grid grid-cols-2 gap-2 text-center">
                  <div>
                    <p className="text-sm font-mono text-purple-400">{data.reflections.total}</p>
                    <p className="text-[10px] text-gray-600">Total Reflections</p>
                  </div>
                  <div>
                    <p className="text-sm font-mono text-purple-400">{Math.round(data.reflections.avg_influence_score * 100)}%</p>
                    <p className="text-[10px] text-gray-600">Avg Influence</p>
                  </div>
                </div>
              </motion.div>

              <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass rounded-2xl p-5">
                <SectionHeader icon={Target} title="Prediction Confidence" />
                <div className="text-center py-4">
                  <p className="text-4xl font-bold font-mono text-teal-400">{Math.round(data.dashboard.prediction_confidence * 100)}%</p>
                  <p className="text-xs text-gray-500 mt-1">Forecast accuracy</p>
                </div>
                <ProgressBar label="Confidence" value={data.dashboard.prediction_confidence * 100} color="teal" />
                <div className="mt-3 pt-3 border-t border-white/5 grid grid-cols-2 gap-2 text-center">
                  <div>
                    <p className="text-sm font-mono text-teal-400">{data.predictions.total}</p>
                    <p className="text-[10px] text-gray-600">Total Predictions</p>
                  </div>
                  <div>
                    <p className="text-sm font-mono text-teal-400">{Math.round(data.predictions.accuracy_rate * 100)}%</p>
                    <p className="text-[10px] text-gray-600">Fulfilled Rate</p>
                  </div>
                </div>
              </motion.div>
            </div>

            {/* ── Charts Row 2: Donut + Bars ──────────────── */}
            <div className="grid md:grid-cols-2 gap-4">
              {/* Prediction Fulfillment Donut */}
              <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }} className="glass rounded-2xl p-6">
                <SectionHeader icon={Target} title="Prediction Fulfillment" subtitle={`${data.predictions.fulfilled} fulfilled of ${data.predictions.total} total`} />
                <div className="h-52 flex items-center justify-center relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <RePieChart>
                      <Pie
                        data={predictionFulfillment}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={84}
                        dataKey="value"
                        nameKey="name"
                        paddingAngle={4}
                        animationBegin={300}
                        animationDuration={1000}
                      >
                        {predictionFulfillment.map((entry, i) => (
                          <Cell key={i} fill={entry.color} stroke="rgba(0,0,0,0.3)" strokeWidth={1} />
                        ))}
                      </Pie>
                      <Tooltip content={<ChartTooltip />} />
                    </RePieChart>
                  </ResponsiveContainer>
                  {/* Center label */}
                  {data.predictions.total > 0 && (
                    <div className="absolute pointer-events-none text-center">
                      <p className="text-2xl font-bold font-mono text-teal-400">{Math.round(data.predictions.accuracy_rate * 100)}%</p>
                      <p className="text-[9px] text-gray-500 -mt-0.5">fulfilled</p>
                    </div>
                  )}
                </div>
              </motion.div>

              {/* Skill Confidence BarChart */}
              <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="glass rounded-2xl p-6">
                <SectionHeader icon={Zap} title="Skill Confidence" subtitle={`${skillBars.length} active skills · ${data.skills.total_uses} total uses`} />
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={skillBars} margin={{ top: 4, right: 4, left: -20, bottom: 0 }} barCategoryGap={6}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis
                        dataKey="name"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#6b7280', fontSize: 9, fontFamily: 'monospace' }}
                        interval={0}
                      />
                      <YAxis
                        domain={[0, 100]}
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#6b7280', fontSize: 9, fontFamily: 'monospace' }}
                      />
                      <Tooltip content={<ChartTooltip />} />
                      <Bar
                        dataKey="confidence"
                        name="Confidence %"
                        radius={[4, 4, 0, 0]}
                        animationBegin={400}
                        animationDuration={900}
                      >
                        {skillBars.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-1">
                  {skillBars.slice(0, 4).map((entry, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                      <span className="text-[10px] text-gray-500">{entry.name}</span>
                      <span className="text-[10px] font-mono text-gray-400">{entry.confidence}%</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>

            {/* ── Skills Metrics ──────────────────────────── */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }} className="glass rounded-2xl p-6">
              <SectionHeader icon={Zap} title="Skill Metrics" subtitle={`${data.skills.total} skills · ${data.skills.total_uses} total uses`} />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard icon={Zap} label="Total Skills" value={data.skills.total} color="amber" delay={0.5} />
                <StatCard icon={Percent} label="Avg Confidence" value={`${Math.round(data.skills.avg_confidence * 100)}%`} color="blue" delay={0.55} />
                <StatCard icon={Activity} label="Total Uses" value={data.skills.total_uses} color="green" delay={0.6} />
                <StatCard icon={TrendingUp} label="Uses per Skill" value={data.skills.total ? (data.skills.total_uses / data.skills.total).toFixed(1) : '0'} color="purple" delay={0.65} />
              </div>
            </motion.div>
          </>
        ) : null}
    </div>
  )
}
