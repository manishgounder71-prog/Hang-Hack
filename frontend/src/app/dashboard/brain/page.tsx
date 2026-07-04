'use client'

import { motion } from 'framer-motion'
import dynamic from 'next/dynamic'
import { Cpu } from 'lucide-react'

// Dynamically import the 3D BrainGraph (Three.js ~200KB) — code-split for faster initial load
const BrainGraph = dynamic(() => import('@/components/BrainGraph'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
    </div>
  ),
})

export default function BrainPage() {
  return (
    <div className="h-[calc(100vh-56px)] relative">
        {/* The 3D graph fills the full viewport */}
        <BrainGraph />

        {/* Info overlay */}
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="absolute bottom-4 left-4 glass-strong rounded-xl p-3"
        >
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-xs font-medium">3D Knowledge Graph</span>
          </div>
          <div className="space-y-1 text-[10px] text-gray-500">
            <p>Drag to rotate · Scroll to zoom</p>
            <p className="text-blue-400">Click a node for details</p>
          </div>
        </motion.div>

        {/* Legend overlay */}
        <motion.div
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="absolute top-4 right-4 flex gap-1.5"
        >
          {['memory', 'skill', 'project', 'entity', 'concept'].map((tag) => (
            <span
              key={tag}
              className="text-[9px] px-2 py-1 rounded-full bg-white/5 border border-white/10 text-gray-400 capitalize"
            >
              {tag}
            </span>
          ))}
        </motion.div>
      </div>
  )
}
