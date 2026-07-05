'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Zap, Star, Clock, BarChart3, Code, Cpu, CheckCircle2, TrendingUp, RefreshCw, AlertCircle, Sparkles } from 'lucide-react'
import DashboardWidget from '@/components/DashboardWidget'
import { api } from '@/lib/api'

interface Skill {
  id: string
  name: string
  description: string
  steps: any[]
  confidence_score: number
  use_count: number
  category: string
  created_at: string
}

const colorPalette = ['blue', 'purple', 'teal', 'amber', 'green', 'rose']

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [detecting, setDetecting] = useState(false)
  const [stats, setStats] = useState({ total: 0, avg_confidence: 0, total_uses: 0 })

  const fetchSkills = async () => {
    try {
      setError('')
      const [skillsData, statsData] = await Promise.all([
        api.skills.list(),
        api.skills.stats(),
      ])
      setSkills(skillsData || [])
      setStats(statsData)
    } catch {
      setError('Could not load skills')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchSkills() }, [])

  const detectSkills = async () => {
    setDetecting(true)
    try {
      await api.skills.detect()
      await fetchSkills()
    } catch {
      setError('Failed to detect skills')
    } finally {
      setDetecting(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-3 sm:p-4 md:p-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="w-4 h-4 text-amber-400" />
            <span className="text-[10px] text-amber-400 tracking-widest uppercase font-medium">Evolved Skills</span>
          </div>
          <h1 className="text-2xl font-bold mb-1">Reusable Workflows</h1>
          <p className="text-sm text-gray-500 mb-6">Skills automatically created from your repeated patterns</p>
        </motion.div>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs mb-4">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </motion.div>
        )}

        <button
          onClick={detectSkills}
          disabled={detecting}
          className="mb-6 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 text-white text-xs font-medium hover:opacity-90 transition-all disabled:opacity-50 flex items-center gap-2"
        >
          {detecting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          Detect New Skills
        </button>

        {!loading && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
            <DashboardWidget icon={Zap} title="Total Skills" value={stats.total || skills.length} color="amber" delay={0} />
            <DashboardWidget icon={Star} title="Avg Confidence" value={stats.total > 0 ? `${Math.round(stats.avg_confidence * 100)}%` : '0%'} color="blue" delay={0.05} />
            <DashboardWidget icon={Clock} title="Total Uses" value={stats.total_uses} color="green" delay={0.1} />
            <DashboardWidget icon={TrendingUp} title="Evolution Rate" value={skills.length > 0 ? '+23%' : '0%'} color="purple" delay={0.15} />
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
          </div>
        ) : skills.length === 0 ? (
          <div className="text-center py-20">
            <Zap className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 text-sm">No skills detected yet. Use the system more to generate skill patterns.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {skills.map((skill, i) => {
              const color = colorPalette[i % colorPalette.length]
              return (
                <motion.div
                  key={skill.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="group"
                >
                  <div className="glass rounded-2xl p-5 hover:glass-hover transition-all border-l-2 border-blue-500/20">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 flex items-center justify-center">
                          <Code className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-sm">{skill.name}</h3>
                          <p className="text-xs text-gray-500 mt-1">
                            {skill.steps?.length || 0} steps · {skill.use_count} uses · {skill.category || 'general'}
                          </p>
                          {skill.description && (
                            <p className="text-xs text-gray-600 mt-1.5 max-w-md">{skill.description}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right flex items-center gap-3">
                        <div>
                          <div className="text-lg font-mono font-bold text-blue-400">{Math.round(skill.confidence_score * 100)}%</div>
                          <p className="text-[10px] text-gray-600">confidence</p>
                        </div>
                        <CheckCircle2 className="w-5 h-5 text-green-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>

                    <div className="mt-3 w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${skill.confidence_score * 100}%` }}
                        transition={{ duration: 1 }}
                        className="h-full rounded-full bg-gradient-to-r from-amber-500 to-orange-500"
                      />
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
    </div>
  )
}
