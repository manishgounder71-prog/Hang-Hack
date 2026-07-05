'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import {
  Brain, Github, Zap, Network, Eye, TrendingUp, Sparkles,
  ChevronDown, MessageCircle, BookOpen, ArrowRight, Shield,
  Layers, Timer, BarChart3, Star, Target, Activity,
  Globe, Cpu, Quote, ChevronRight, Dot,
} from 'lucide-react'

function NeuralBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mouseRef = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    const particles: {
      x: number; y: number; vx: number; vy: number; size: number;
      baseX: number; baseY: number; alpha: number; hue: number;
    }[] = []
    const pCount = 100

    for (let i = 0; i < pCount; i++) {
      const hue = Math.random() > 0.5 ? 220 : 270
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        size: Math.random() * 2.5 + 0.5,
        baseX: 0, baseY: 0,
        alpha: Math.random() * 0.5 + 0.2,
        hue,
      })
    }

    const handleMouse = (e: MouseEvent) => {
      mouseRef.current.x = e.clientX
      mouseRef.current.y = e.clientY
    }
    window.addEventListener('mousemove', handleMouse)

    let animId: number
    function animate() {
      if (!ctx || !canvas) return
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const mx = mouseRef.current.x / canvas.width
      const my = mouseRef.current.y / canvas.height

      particles.forEach((p, i) => {
        p.vx += (Math.random() - 0.5) * 0.01
        p.vy += (Math.random() - 0.5) * 0.01
        p.vx *= 0.99
        p.vy *= 0.99

        const dx = mx * canvas.width - p.x
        const dy = my * canvas.height - p.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 200) {
          p.vx -= dx * 0.00005
          p.vy -= dy * 0.00005
        }

        p.x += p.vx
        p.y += p.vy

        if (p.x < 0 || p.x > canvas.width) p.vx *= -1
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1

        for (let j = i + 1; j < particles.length; j++) {
          const pdx = p.x - particles[j].x
          const pdy = p.y - particles[j].y
          const pdist = Math.sqrt(pdx * pdx + pdy * pdy)
          if (pdist < 120) {
            ctx.beginPath()
            ctx.moveTo(p.x, p.y)
            ctx.lineTo(particles[j].x, particles[j].y)
            const alpha = (1 - pdist / 120) * 0.12
            ctx.strokeStyle = `rgba(37, 99, 235, ${alpha})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = `hsla(${p.hue}, 70%, 60%, ${p.alpha * 0.6})`
        ctx.fill()

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size * 2.5, 0, Math.PI * 2)
        ctx.fillStyle = `hsla(${p.hue}, 70%, 60%, ${p.alpha * 0.05})`
        ctx.fill()
      })

      animId = requestAnimationFrame(animate)
    }
    animate()

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('mousemove', handleMouse)
    }
  }, [])

  return <canvas ref={canvasRef} className="fixed inset-0 z-0 pointer-events-none" />
}

function GradientOrb() {
  return (
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
      <div className="relative w-[600px] h-[600px] md:w-[800px] md:h-[800px]">
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500/15 via-purple-500/10 to-teal-500/15 blur-3xl animate-breathe" />
        <div className="absolute inset-[15%] rounded-full bg-gradient-to-r from-purple-500/10 via-blue-500/10 to-cyan-500/10 blur-2xl animate-spin-slow" />
        <div className="absolute inset-[30%] rounded-full bg-gradient-to-r from-blue-500/15 to-purple-500/15 blur-xl animate-pulse-glow" />
      </div>
    </div>
  )
}

function FloatingNodes() {
  const nodes = [
    { size: 80, x: 15, y: 20, duration: 7, delay: 0 },
    { size: 50, x: 75, y: 15, duration: 9, delay: 1 },
    { size: 100, x: 85, y: 70, duration: 8, delay: 2 },
    { size: 60, x: 10, y: 75, duration: 6, delay: 0.5 },
    { size: 40, x: 45, y: 10, duration: 10, delay: 1.5 },
    { size: 70, x: 20, y: 60, duration: 7.5, delay: 3 },
    { size: 45, x: 65, y: 80, duration: 8.5, delay: 1 },
  ]

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {nodes.map((nd, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full neural-gradient-soft"
          style={{
            width: nd.size, height: nd.size,
            left: `${nd.x}%`, top: `${nd.y}%`,
          }}
          animate={{
            y: [0, -nd.size * 0.4, 0],
            x: [0, nd.size * 0.2, 0],
            scale: [1, 1.08, 1],
            opacity: [0.08, 0.18, 0.08],
          }}
          transition={{
            duration: nd.duration, repeat: Infinity, delay: nd.delay,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  )
}

const codeLines = [
  'import cognee',
  '',
  '# Every interaction is remembered',
  'await cognee.remember("User started a new AI project")',
  '',
  '# Past knowledge influences every response',
  'memories = await cognee.recall("previous architecture patterns")',
  '',
  '# The system improves itself over time',
  'await cognee.improve()',
]

function CodeWindow() {
  const [visible, setVisible] = useState(false)

  return (
    <div
      className="glass-strong rounded-2xl overflow-hidden font-mono text-sm w-full max-w-2xl mx-auto"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
        <div className="w-3 h-3 rounded-full bg-red-500/50" />
        <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
        <div className="w-3 h-3 rounded-full bg-green-500/50" />
        <span className="text-xs text-gray-600 ml-2">genesis_core.py</span>
      </div>
      <div className="p-4 space-y-1.5">
        {codeLines.map((line, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.15, duration: 0.3 }}
            className="flex"
          >
            <span className="text-gray-600 w-6 text-right mr-3 select-none text-xs">{i + 1}</span>
            {line.startsWith('import') && <span><span className="text-purple-400">import </span><span className="text-teal-400">cognee</span></span>}
            {line.startsWith('#') && !line.startsWith('# E') && !line.startsWith('# P') && !line.startsWith('# T') && <span className="text-gray-600">{line}</span>}
            {line.startsWith('# Every') && <span className="text-gray-500 italic">{line}</span>}
            {line.startsWith('memories') && <span><span className="text-blue-400">memories</span><span className="text-gray-400"> = </span><span className="text-purple-400">await </span><span className="text-teal-400">cognee</span><span className="text-gray-400">.</span><span className="text-yellow-400">recall</span><span className="text-gray-400">(</span><span className="text-green-400">&quot;previous architecture patterns&quot;</span><span className="text-gray-400">)</span></span>}
            {line.startsWith('await cognee.remember') && <span><span className="text-purple-400">await </span><span className="text-teal-400">cognee</span><span className="text-gray-400">.</span><span className="text-yellow-400">remember</span><span className="text-gray-400">(</span><span className="text-green-400">&quot;User started a new AI project&quot;</span><span className="text-gray-400">)</span></span>}
            {line.startsWith('await cognee.improve') && <span><span className="text-purple-400">await </span><span className="text-teal-400">cognee</span><span className="text-gray-400">.</span><span className="text-yellow-400">improve</span><span className="text-gray-400">()</span></span>}
            {line === '' && <span>&nbsp;</span>}
          </motion.div>
        ))}
      </div>
      {visible && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="border-t border-white/5 px-4 py-2 bg-blue-500/5"
        >
          <span className="text-green-400">✓</span>
          <span className="text-gray-400 text-xs ml-2">Memory stored. 3 similar patterns found. Confidence: 92%</span>
        </motion.div>
      )}
    </div>
  )
}

const iconColorMap: Record<string, string> = {
  blue: '#60a5fa',
  purple: '#a78bfa',
  teal: '#2dd4bf',
  amber: '#fbbf24',
  rose: '#fb7185',
  green: '#34d399',
  default: '#60a5fa',
}

const features = [
  { icon: Brain, title: 'Persistent Memory', desc: 'Every interaction becomes structured memory via Cognee', gradient: 'from-blue-500/20 to-blue-600/10', color: 'blue' },
  { icon: Network, title: 'Knowledge Graph', desc: 'Dynamic 3D graph showing relationships between everything', gradient: 'from-purple-500/20 to-purple-600/10', color: 'purple' },
  { icon: Eye, title: 'Reflection Engine', desc: 'Self-analysis after every task to improve future behavior', gradient: 'from-teal-500/20 to-teal-600/10', color: 'teal' },
  { icon: Zap, title: 'Skill Evolution', desc: 'Automatically creates reusable skills from repeated workflows', gradient: 'from-amber-500/20 to-amber-600/10', color: 'amber' },
  { icon: TrendingUp, title: 'Prediction Engine', desc: 'Predicts next projects, questions, and learning paths', gradient: 'from-rose-500/20 to-rose-600/10', color: 'rose' },
  { icon: Sparkles, title: 'Digital Twin', desc: 'Behavioral model that adapts to your style over time', gradient: 'from-green-500/20 to-green-600/10', color: 'green' },
]

const pipelineSteps = [
  { icon: MessageCircle, step: 'Experience', desc: 'User interacts with Genesis', color: 'border-blue-500/30' },
  { icon: Layers, step: 'Cognee Memory', desc: 'Structured into persistent knowledge graph', color: 'border-purple-500/30' },
  { icon: Eye, step: 'Reflection', desc: 'AI analyzes what worked and what failed', color: 'border-teal-500/30' },
  { icon: Zap, step: 'Learning', desc: 'Patterns detected, skills created', color: 'border-amber-500/30' },
  { icon: TrendingUp, step: 'Prediction', desc: 'Future needs anticipated', color: 'border-rose-500/30' },
  { icon: Brain, step: 'Evolution', desc: 'Better decisions every time', color: 'border-green-500/30' },
]

const testimonials = [
  { text: 'Genesis remembered my architecture preferences from weeks ago and applied them automatically. It felt like it knew me.', author: 'Alex K.', role: 'Full-Stack Developer' },
  { text: 'The reflection engine caught a pattern I was doing wrong for months. It created a skill to fix it permanently.', author: 'Sarah M.', role: 'AI Engineer' },
]

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false)
  const { scrollYProgress } = useScroll()
  const heroOpacity = useTransform(scrollYProgress, [0, 0.3], [1, 0])
  const heroScale = useTransform(scrollYProgress, [0, 0.3], [1, 0.95])

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 80)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="relative min-h-screen noise-bg">
      <NeuralBackground />
      <GradientOrb />
      <FloatingNodes />

      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrolled ? 'glass-strong border-b border-white/5' : ''
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg neural-gradient flex items-center justify-center group-hover:scale-110 transition-transform">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg">Genesis <span className="text-gradient">AI</span></span>
          </Link>
          <div className="hidden md:flex items-center gap-8 text-sm">
            {['Features', 'Demo', 'Pipeline'].map((item) => (
              <a key={item} href={`#${item.toLowerCase()}`}
                className="text-gray-400 hover:text-white transition-colors relative group">
                {item}
                <span className="absolute -bottom-1 left-0 w-0 h-px bg-blue-500 group-hover:w-full transition-all" />
              </a>
            ))}
          </div>
          <Link href="/dashboard"
            className="group relative px-5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium overflow-hidden glow-blue"
          >
            <span className="relative z-10 flex items-center gap-2">
              Launch App <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity" />
          </Link>
        </div>
      </motion.nav>

      <motion.section style={{ opacity: heroOpacity, scale: heroScale }} className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6 pt-20">
        <div className="text-center max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-strong text-xs text-blue-300 mb-8 border border-blue-500/20"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            Powered by Cognee Persistent Memory
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-5xl md:text-7xl lg:text-8xl font-bold leading-[1.05] mb-6 tracking-tight"
          >
            <span className="inline-block">The AI That</span>{' '}
            <span className="inline-block text-gradient">Evolves</span>
            <br />
            <span className="inline-block">Because It</span>{' '}
            <span className="inline-block relative">
              <span className="text-gradient">Remembers</span>
              <motion.span
                className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-teal-500 rounded-full"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: 1.5, duration: 0.8 }}
              />
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="text-base md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Not a chatbot. The world&apos;s first self-evolving AI operating system.
            Every conversation permanently improves the system.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link href="/dashboard"
              className="group relative px-8 py-4 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold text-lg overflow-hidden glow-blue"
            >
              <span className="relative z-10 flex items-center gap-2">
                Enter Genesis <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-400 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            </Link>
            <a href="#demo"
              className="group px-8 py-4 rounded-xl glass-strong text-white font-semibold text-lg hover:bg-white/5 transition-all flex items-center gap-2"
            >
              <MessageCircle className="w-5 h-5 group-hover:rotate-12 transition-transform" /> See How It Works
            </a>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2 }}
          className="absolute bottom-10 flex flex-col items-center gap-2"
        >
          <span className="text-[10px] text-gray-600 tracking-widest uppercase">Scroll to explore</span>
          <ChevronDown className="w-4 h-4 text-gray-500 animate-bounce" />
        </motion.div>
      </motion.section>

      <section id="features" className="relative z-10 py-32 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="text-xs text-blue-400 tracking-widest uppercase font-medium">Core Capabilities</span>
            <h2 className="text-4xl md:text-6xl font-bold mt-3 mb-4">
              The <span className="text-gradient">Genesis</span> Difference
            </h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Traditional AI forgets. Genesis learns, reflects, and evolves with every interaction.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="group relative"
              >
                <div className="glass rounded-2xl p-6 hover:glass-hover transition-all duration-300 card-shine border border-transparent hover:border-white/10">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                    <feature.icon style={{ color: iconColorMap[feature.color] || iconColorMap.default }} className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 group-hover:text-white transition-colors">{feature.title}</h3>
                  <p className="text-gray-500 text-sm leading-relaxed group-hover:text-gray-400 transition-colors">{feature.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section id="demo" className="relative z-10 py-32 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="glass rounded-3xl p-8 md:p-12 glow-card"
          >
            <div className="text-center mb-10">
              <span className="text-xs text-purple-400 tracking-widest uppercase font-medium">Live Demo</span>
              <h2 className="text-3xl md:text-5xl font-bold mt-3">
                See It In <span className="text-gradient">Action</span>
              </h2>
            </div>

            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                  <MessageCircle className="w-5 h-5 text-blue-400 flex-shrink-0" />
                  <p className="text-sm text-gray-300">&ldquo;Help me build another AI project&rdquo;</p>
                </div>
                <div className="flex items-start gap-3 p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
                  <Brain className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-300">&ldquo;I remember you built an internship management system and explored AI productivity tools. Based on what worked, I recommend this architecture.&rdquo;</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {['Auth Module', 'Dashboard', 'API Scaffold'].map((s) => (
                        <span key={s} className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/20 text-green-400">{s} ✓</span>
                      ))}
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-500 italic">It visually highlights the memories and reasoning path on the graph.</p>
              </div>

              <div className="h-64 md:h-80 rounded-2xl bg-gradient-to-br from-blue-900/30 via-purple-900/20 to-teal-900/30 border border-white/5 flex items-center justify-center relative overflow-hidden">
                <motion.div
                  className="absolute inset-0"
                  animate={{ backgroundPosition: ['0% 0%', '100% 100%'] }}
                  transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
                  style={{ backgroundImage: 'radial-gradient(circle at 30% 50%, rgba(37,99,235,0.1) 0%, transparent 50%), radial-gradient(circle at 70% 50%, rgba(147,51,234,0.1) 0%, transparent 50%)' }}
                />
                <div className="relative text-center">
                  <Brain className="w-12 h-12 text-blue-400 mx-auto mb-3 animate-breathe" />
                  <p className="text-gray-500 text-sm">Memory Graph Visualization</p>
                  <div className="flex justify-center gap-3 mt-4">
                    {[{label: 'blue', color: '#3b82f6'}, {label: 'purple', color: '#a855f7'}, {label: 'teal', color: '#2dd4bf'}].map((c) => (
                      <motion.div
                        key={c.label}
                        style={{ backgroundColor: c.color }}
                        className="w-3 h-3 rounded-full"
                        animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity, delay: ['blue', 'purple', 'teal'].indexOf(c.label) * 0.5 }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section id="pipeline" className="relative z-10 py-32 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <span className="text-xs text-teal-400 tracking-widest uppercase font-medium">How It Works</span>
              <h2 className="text-3xl md:text-5xl font-bold mt-3 mb-8">
                The Evolution <span className="text-gradient">Pipeline</span>
              </h2>

              <div className="space-y-3">
                {pipelineSteps.map((item, i) => (
                  <motion.div
                    key={item.step}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.08 }}
                    className="group"
                  >
                    <div className={`flex items-center gap-4 glass rounded-xl p-4 border-l-2 ${item.color} hover:glass-hover transition-all`}>
                      <div className="w-10 h-10 rounded-lg neural-gradient flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                        <item.icon className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-sm">{item.step}</p>
                        <p className="text-xs text-gray-500">{item.desc}</p>
                      </div>
                      {i < pipelineSteps.length - 1 && (
                        <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-gray-400 transition-colors" />
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="space-y-6"
            >
              <CodeWindow />

              <div className="glass-strong rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Activity className="w-4 h-4 text-green-400" />
                  <span className="text-green-400 font-medium text-sm">Brain Health: 88%</span>
                  <div className="ml-auto flex items-center gap-1">
                    {[1,2,3,4,5].map((i) => (
                      <motion.div
                        key={i}
                        className="w-1.5 h-4 rounded-full bg-gradient-to-t from-blue-500 to-purple-500"
                        animate={{ height: [4, 8, 14, 8, 4][i-1] * 2 }}
                        transition={{ duration: 1, repeat: Infinity, delay: i * 0.1 }}
                      />
                    ))}
                  </div>
                </div>
                <div className="space-y-3">
                  {[
                    { label: 'Memory Count', value: '1,247', progress: 85, color: 'bg-blue-500' },
                    { label: 'Knowledge Nodes', value: '892', progress: 62, color: 'bg-purple-500' },
                    { label: 'Relationships', value: '3,401', progress: 91, color: 'bg-teal-500' },
                    { label: 'Skills', value: '12', progress: 45, color: 'bg-amber-500' },
                    { label: 'Evolution Level', value: '3', progress: 38, color: 'bg-green-500' },
                  ].map((stat) => (
                    <div key={stat.label}>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-gray-400">{stat.label}</span>
                        <span className="font-mono font-bold text-white">{stat.value}</span>
                      </div>
                      <div className="w-full h-1 rounded-full bg-white/5 overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: `${stat.progress}%` }}
                          viewport={{ once: true }}
                          transition={{ duration: 1, delay: 0.3 }}
                          className={`h-full rounded-full ${stat.color}`}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {testimonials.map((t, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1 }}
                    className="glass rounded-xl p-4"
                  >
                    <Quote className="w-4 h-4 text-blue-400 mb-2 opacity-50" />
                    <p className="text-xs text-gray-400 leading-relaxed mb-3">&ldquo;{t.text}&rdquo;</p>
                    <div>
                      <p className="text-xs font-medium">{t.author}</p>
                      <p className="text-[10px] text-gray-600">{t.role}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      <section className="relative z-10 py-20 px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto glass-strong rounded-3xl p-12 md:p-16 text-center glow-card"
        >
          <Cpu className="w-10 h-10 text-blue-400 mx-auto mb-6" />
          <h2 className="text-3xl md:text-5xl font-bold mb-4">
            Ready to Build an{' '}
            <span className="text-gradient">Evolving</span> AI?
          </h2>
          <p className="text-gray-400 text-lg mb-8 max-w-xl mx-auto">
            Every conversation, every project, every mistake makes Genesis smarter.
            Start your evolution today.
          </p>
          <Link href="/dashboard"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold text-lg glow-blue group"
          >
            Enter Genesis <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </motion.div>
      </section>

      <footer className="relative z-10 border-t border-white/5 py-10 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg neural-gradient flex items-center justify-center">
              <Brain className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-semibold text-sm">Genesis AI</span>
          </div>
          <p className="text-gray-600 text-xs">
            Built for the WeMakeDevs x Cognee Hackathon
          </p>
          <div className="flex items-center gap-4 text-gray-600 text-xs">
            <span className="hover:text-gray-400 transition-colors cursor-pointer">Powered by Cognee</span>
            <span className="w-1 h-1 rounded-full bg-gray-700" />
            <span className="hover:text-gray-400 transition-colors cursor-pointer">Open Source</span>
            <span className="w-1 h-1 rounded-full bg-gray-700" />
            <Github className="w-3.5 h-3.5 hover:text-gray-400 transition-colors cursor-pointer" />
          </div>
        </div>
      </footer>
    </div>
  )
}
