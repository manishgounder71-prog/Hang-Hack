'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Eye, ThumbsUp, ThumbsDown, Lightbulb, GitBranch, AlertCircle, RefreshCw, Sparkles } from 'lucide-react'
import { api } from '@/lib/api'

interface Reflection {
  id: string
  trigger_event: string
  what_worked: string
  what_failed: string
  improvements: string
  patterns: string
  influence_score: number
  created_at: string
}

export default function ReflectionsPage() {
  const [reflections, setReflections] = useState<Reflection[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  const fetchReflections = useCallback(async () => {
    try {
      setError('')
      const data = await api.reflections.list()
      setReflections(data || [])
    } catch {
      setError('Could not load reflections')
    } finally {
      setLoading(false)
    }
  }, [])

  const generateReflection = useCallback(async () => {
    setGenerating(true)
    setError('')
    try {
      await api.reflections.create({
        trigger_event: 'chat_session_review',
        what_worked: 'Reviewed recent project discussions and technical decisions',
        what_failed: '',
      })
      await fetchReflections()
    } catch {
      setError('Failed to generate reflection')
    } finally {
      setGenerating(false)
    }
  }, [fetchReflections])

  useEffect(() => { fetchReflections() }, [fetchReflections])

  return (
    <div className="max-w-5xl mx-auto p-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 mb-1">
            <Eye className="w-4 h-4 text-purple-400" />
            <span className="text-[10px] text-purple-400 tracking-widest uppercase font-medium">Self-Analysis</span>
          </div>
          <h1 className="text-2xl font-bold mb-1">How Genesis Learns</h1>
          <p className="text-sm text-gray-500 mb-6">Every completed task generates a reflection that improves future behavior</p>
        </motion.div>

        <div className="flex items-center justify-between mb-6">
          <div />
          <button
            onClick={generateReflection}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {generating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            {generating ? 'Generating...' : 'Generate Reflection'}
          </button>
        </div>

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
        ) : reflections.length === 0 ? (
          <div className="text-center py-20">
            <Eye className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 text-sm">No reflections yet. Click "Generate Reflection" to analyze recent conversations.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {reflections.map((ref, i) => (
              <motion.div
                key={ref.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <div className="glass rounded-2xl p-5 hover:glass-hover transition-all">
                  <div className="flex items-start gap-4 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/10 flex items-center justify-center">
                      <Eye className="w-5 h-5 text-purple-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-sm">{ref.trigger_event}</h3>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-[10px] text-gray-600">Influence score</span>
                        <div className="w-24 h-1.5 rounded-full bg-white/5 overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${ref.influence_score * 100}%` }}
                            transition={{ duration: 1 }}
                            className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500"
                          />
                        </div>
                        <span className="text-[10px] font-mono text-purple-400">{Math.round(ref.influence_score * 100)}%</span>
                        <span className="text-[9px] text-gray-600 ml-auto">{new Date(ref.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-3">
                    <div className="flex items-start gap-3 p-3 rounded-xl bg-green-500/5 border border-green-500/10">
                      <ThumbsUp className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-[10px] text-green-400 uppercase font-medium mb-1">What Worked</p>
                        <p className="text-xs text-gray-300">{ref.what_worked}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 rounded-xl bg-red-500/5 border border-red-500/10">
                      <ThumbsDown className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-[10px] text-red-400 uppercase font-medium mb-1">What Failed</p>
                        <p className="text-xs text-gray-300">{ref.what_failed}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 rounded-xl bg-amber-500/5 border border-amber-500/10">
                      <Lightbulb className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-[10px] text-amber-400 uppercase font-medium mb-1">Improvements</p>
                        <p className="text-xs text-gray-300">{ref.improvements}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 rounded-xl bg-blue-500/5 border border-blue-500/10">
                      <GitBranch className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-[10px] text-blue-400 uppercase font-medium mb-1">Patterns Detected</p>
                        <p className="text-xs text-gray-300">{ref.patterns}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
    </div>
  )
}
