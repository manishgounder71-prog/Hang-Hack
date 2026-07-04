'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Brain, TrendingUp, Lightbulb, AlertTriangle, Target, CheckCircle2, Sparkles, RefreshCw, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'

interface Prediction {
  id: string
  prediction_type: string
  content: string
  confidence: number
  reasoning: string
  influencing_memories: string[]
  is_fulfilled: number
  created_at: string
}

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [generating, setGenerating] = useState(false)

  const fetchPredictions = async () => {
    try {
      setError('')
      const data = await api.predictions.list()
      setPredictions(data.predictions || [])
    } catch {
      setError('Could not load predictions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPredictions() }, [])

  const generatePrediction = async () => {
    setGenerating(true)
    try {
      await api.predictions.create()
      await fetchPredictions()
    } catch {
      setError('Failed to generate prediction')
    } finally {
      setGenerating(false)
    }
  }

  const typeIcons: Record<string, typeof Brain> = {
    project: Target, learning: Lightbulb, skill: TrendingUp,
    risk: AlertTriangle, interest: Brain, goal: CheckCircle2,
    general: Brain,
  }

  const colorConfig: Record<string, string> = {
    project: 'from-blue-500/20 to-blue-600/10 border-blue-500/20 text-blue-400',
    learning: 'from-purple-500/20 to-purple-600/10 border-purple-500/20 text-purple-400',
    skill: 'from-teal-500/20 to-teal-600/10 border-teal-500/20 text-teal-400',
    risk: 'from-rose-500/20 to-rose-600/10 border-rose-500/20 text-rose-400',
    interest: 'from-amber-500/20 to-amber-600/10 border-amber-500/20 text-amber-400',
    goal: 'from-green-500/20 to-green-600/10 border-green-500/20 text-green-400',
    general: 'from-blue-500/20 to-blue-600/10 border-blue-500/20 text-blue-400',
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-teal-400" />
            <span className="text-[10px] text-teal-400 tracking-widest uppercase font-medium">Forecasting</span>
          </div>
          <h1 className="text-2xl font-bold mb-1">AI Predictions</h1>
          <p className="text-sm text-gray-500 mb-6">What Genesis predicts based on your memory patterns</p>
        </motion.div>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs mb-4">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </motion.div>
        )}

        <button
          onClick={generatePrediction}
          disabled={generating}
          className="mb-6 px-4 py-2 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 text-white text-xs font-medium hover:opacity-90 transition-all disabled:opacity-50 flex items-center gap-2"
        >
          {generating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          Generate New Prediction
        </button>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-teal-500/30 border-t-teal-500 rounded-full animate-spin" />
          </div>
        ) : predictions.length === 0 ? (
          <div className="text-center py-20">
            <Brain className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 text-sm">No predictions yet. Generate one to see what Genesis forecasts.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {predictions.map((pred, i) => {
              const Icon = typeIcons[pred.prediction_type] || Brain
              const colors = colorConfig[pred.prediction_type] || colorConfig.general
              return (
                <motion.div
                  key={pred.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="group"
                >
                  <div className={`glass rounded-2xl p-5 hover:glass-hover transition-all border-l-2 ${colors.split(' ')[2]}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4 flex-1 min-w-0">
                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colors.split(' ')[0]} ${colors.split(' ')[1]} flex items-center justify-center flex-shrink-0`}>
                          <Icon className={`w-5 h-5 ${colors.split(' ')[4]}`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-semibold text-sm">{pred.content}</h3>
                            <span className={`text-[9px] px-2 py-0.5 rounded-full border text-gray-400 border-white/10 bg-white/5`}>
                              {pred.prediction_type}
                            </span>
                            {pred.is_fulfilled ? (
                              <span className="text-[9px] px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 border border-green-500/20">
                                ✓ Fulfilled
                              </span>
                            ) : null}
                          </div>
                          {pred.reasoning && (
                            <p className="text-xs text-gray-500 mt-2 flex items-start gap-1">
                              <span className="text-blue-400 font-medium flex-shrink-0">Why?</span>
                              {pred.reasoning}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="text-right flex flex-col items-center flex-shrink-0 ml-4">
                        <div className="text-lg font-mono font-bold" style={{ color: `var(--genesis-teal)` }}>{Math.round(pred.confidence * 100)}%</div>
                        <p className="text-[10px] text-gray-600">confidence</p>
                        <p className="text-[9px] text-gray-600 mt-1">{new Date(pred.created_at).toLocaleDateString()}</p>
                      </div>
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
