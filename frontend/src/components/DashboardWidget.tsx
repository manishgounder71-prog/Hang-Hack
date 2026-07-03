'use client'

import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'

interface DashboardWidgetProps {
  icon: LucideIcon
  title: string
  value: string | number
  subtitle?: string
  trend?: number
  color?: string
  delay?: number
}

export default function DashboardWidget({
  icon: Icon,
  title,
  value,
  subtitle,
  trend,
  color = 'blue',
  delay = 0,
}: DashboardWidgetProps) {
  const [displayValue, setDisplayValue] = useState<string | number>(
    typeof value === 'number' ? 0 : '0'
  )
  const hasAnimated = useRef(false)

  useEffect(() => {
    if (typeof value === 'number') {
      // Only animate on initial mount; for subsequent value updates (e.g. polling),
      // jump directly to the new value to avoid distracting count-up resets.
      if (hasAnimated.current) {
        setDisplayValue(value)
        return
      }
      hasAnimated.current = true

      const duration = 800
      const steps = 20
      const increment = value / steps
      let current = 0
      const timer = setInterval(() => {
        current += increment
        if (current >= value) {
          setDisplayValue(value)
          clearInterval(timer)
        } else {
          setDisplayValue(Math.round(current))
        }
      }, duration / steps)
      return () => clearInterval(timer)
    } else {
      setDisplayValue(value)
    }
  }, [value])

  const colorConfig: Record<string, { bg: string; iconCls: string; border: string }> = {
    blue: { bg: 'from-blue-500/15 via-blue-500/5 to-transparent', iconCls: 'text-blue-400', border: 'border-blue-500/20' },
    purple: { bg: 'from-purple-500/15 via-purple-500/5 to-transparent', iconCls: 'text-purple-400', border: 'border-purple-500/20' },
    teal: { bg: 'from-teal-500/15 via-teal-500/5 to-transparent', iconCls: 'text-teal-400', border: 'border-teal-500/20' },
    green: { bg: 'from-green-500/15 via-green-500/5 to-transparent', iconCls: 'text-green-400', border: 'border-green-500/20' },
    amber: { bg: 'from-amber-500/15 via-amber-500/5 to-transparent', iconCls: 'text-amber-400', border: 'border-amber-500/20' },
    rose: { bg: 'from-rose-500/15 via-rose-500/5 to-transparent', iconCls: 'text-rose-400', border: 'border-rose-500/20' },
  }

  const cc = colorConfig[color] || colorConfig.blue

  const trendClass = trend !== undefined ? (trend >= 0 ? 'bg-green-500/20 text-green-400 border border-green-500/20' : 'bg-red-500/20 text-red-400 border border-red-500/20') : ''

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -2, scale: 1.01 }}
      className={`relative overflow-hidden group rounded-2xl p-5 bg-gradient-to-br ${cc.bg} border ${cc.border} hover:bg-white/[0.04] transition-all duration-300 card-shine`}
    >
      <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-bl from-white/[0.03] to-transparent rounded-bl-full" />

      <div className="flex items-start justify-between mb-3 relative">
        <div className={`w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:scale-110 group-hover:border-white/20 transition-all duration-300`}>
          <Icon className={`w-5 h-5 ${cc.iconCls}`} />
        </div>
        {trend !== undefined && (
          <motion.span
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: delay + 0.3 }}
            className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${trendClass}`}
          >
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </motion.span>
        )}
      </div>

      <p className="text-2xl font-bold font-mono tracking-tight mb-0.5">{displayValue}</p>
      <p className="text-xs text-gray-500">{title}</p>
      {subtitle && <p className="text-[10px] text-gray-600 mt-1.5">{subtitle}</p>}

      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
    </motion.div>
  )
}
