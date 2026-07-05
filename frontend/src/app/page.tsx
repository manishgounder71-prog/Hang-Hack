'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { motion, useScroll, useTransform, useInView } from 'framer-motion'
import Link from 'next/link'
import {
  Brain, Github, Zap, Network, Eye, TrendingUp, Sparkles,
  ChevronDown, MessageCircle, ArrowRight,
  Layers, Activity, Quote, Cpu, Database, Search, RefreshCw, Trash2,
  BookOpen, BarChart3, Target, Cpu as CpuIcon,
} from 'lucide-react'

function useReducedMotion() {
  const [prefersReduced, setPrefersReduced] = useState(false)
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReduced(mq.matches)
    const handler = (e: MediaQueryListEvent) => setPrefersReduced(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])
  return prefersReduced
}

function NeuralBg({ reduced }: { reduced: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef<number>(0)
  const runningRef = useRef(true)

  useEffect(() => {
    if (reduced) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    const pCount = Math.min(50, Math.floor(window.innerWidth / 20))
    const particles = Array.from({ length: pCount }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      size: Math.random() * 2 + 0.5,
      hue: Math.random() > 0.5 ? 220 : 270,
    }))

    runningRef.current = true
    function tick() {
      if (!runningRef.current || !ctx || !canvas) return
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i]
        p.x += p.vx
        p.y += p.vy
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1

        for (let j = i + 1; j < particles.length; j++) {
          const dx = p.x - particles[j].x
          const dy = p.y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 100) {
            ctx.beginPath()
            ctx.moveTo(p.x, p.y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(37,99,235,${(1 - dist / 100) * 0.08})`
            ctx.stroke()
          }
        }

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = `hsla(${p.hue},70%,60%,0.3)`
        ctx.fill()
      }
      rafRef.current = requestAnimationFrame(tick)
    }
    tick()

    return () => {
      runningRef.current = false
      cancelAnimationFrame(rafRef.current)
      window.removeEventListener('resize', resize)
    }
  }, [reduced])

  if (reduced) return null
  return <canvas ref={canvasRef} className="fixed inset-0 z-0 pointer-events-none" />
}

function ScrollProgress() {
  const { scrollYProgress } = useScroll()
  return (
    <motion.div
      className="fixed top-0 left-0 right-0 h-[2px] z-[60] origin-left bg-gradient-to-r from-blue-500 via-purple-500 to-teal-500"
      style={{ scaleX: scrollYProgress }}
    />
  )
}

function FadeIn({ children, delay = 0, className = '' }: { children: React.ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.6, delay, ease: [0.16, 1, 0.3, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

function ParallaxSection({ children, speed = 0.15, className = '' }: { children: React.ReactNode; speed?: number; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] })
  const y = useTransform(scrollYProgress, [0, 1], [speed * 100, -speed * 100])
  return (
    <div ref={ref} className={`relative ${className}`}>
      <motion.div style={{ y }}>{children}</motion.div>
    </div>
  )
}

function Counter({ to, suffix = '' }: { to: number; suffix?: string }) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true })

  useEffect(() => {
    if (!isInView) return
    let start = 0
    const step = to / 40
    const t = setInterval(() => {
      start += step
      if (start >= to) { setCount(to); clearInterval(t) }
      else setCount(Math.round(start))
    }, 25)
    return () => clearInterval(t)
  }, [isInView, to])

  return <span ref={ref}>{count}{suffix}</span>
}

const cogneeApis = [
  { icon: Database, title: 'remember()', desc: 'Ingest conversations, files, and code into a persistent hybrid graph-vector memory. Every interaction permanently structured.', color: 'from-blue-500/20 to-blue-600/10', code: 'cognee.remember(content, content_type, user_id)' },
  { icon: Search, title: 'recall()', desc: 'Query across both vector similarity and graph traversal. Automatically routes between semantic search and deep relationship queries.', color: 'from-purple-500/20 to-purple-600/10', code: 'cognee.recall(query, user_id, limit=5)' },
  { icon: RefreshCw, title: 'improve()', desc: 'Post-ingestion enrichment: prune stale nodes, adapt weights, infer new relationships. Memory that self-improves over time.', color: 'from-teal-500/20 to-teal-600/10', code: 'cognee.improve(user_id)' },
  { icon: Trash2, title: 'forget()', desc: 'Surgically prune datasets or individual memories when no longer needed — GDPR-compliant memory management.', color: 'from-amber-500/20 to-amber-600/10', code: 'cognee.forget(dataset, user_id)' },
]

const features = [
  { icon: Brain, title: 'Cross-Session Memory', desc: 'Ask about something discussed weeks ago — Genesis recalls it perfectly, no re-prompting needed.' },
  { icon: Network, title: 'Live Knowledge Graph', desc: 'Every word becomes a node. Relationships emerge between projects, people, and ideas in a 3D interactive graph.' },
  { icon: Eye, title: 'Self-Reflection', desc: 'After every conversation, Genesis analyzes what worked and what failed — and gets better for next time.' },
  { icon: Zap, title: 'Skill Detection', desc: 'Repeated patterns become reusable skills. Genesis learns your workflow and automates it.' },
  { icon: TrendingUp, title: 'Predictive Intelligence', desc: 'Based on your history, Genesis predicts your next questions, projects, and learning needs.' },
  { icon: Sparkles, title: 'Digital Twin', desc: 'A behavioral model of you that gets more accurate with every conversation.' },
]

const pipelineSteps = [
  { icon: MessageCircle, step: 'You Chat', desc: 'Natural conversation with Genesis' },
  { icon: Database, step: 'Cognee remember()', desc: 'Memory stored in hybrid graph-vector' },
  { icon: Search, step: 'Cognee recall()', desc: 'Cross-session context retrieved' },
  { icon: RefreshCw, step: 'Cognee improve()', desc: 'Enrichment, pruning, weight adaptation' },
  { icon: Zap, step: 'Skill Evolution', desc: 'Patterns detected, skills created' },
  { icon: Brain, step: 'Smarter AI', desc: 'Better answers every time, forever' },
]

export default function LandingPage() {
  const reduced = useReducedMotion()
  const [scrolled, setScrolled] = useState(false)
  const { scrollYProgress } = useScroll()
  const heroOpacity = useTransform(scrollYProgress, [0, 0.2], [1, 0])
  const heroScale = useTransform(scrollYProgress, [0, 0.2], [1, 0.97])

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="relative min-h-screen noise-bg">
      <ScrollProgress />
      <NeuralBg reduced={reduced} />

      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled ? 'glass-strong border-b border-white/5' : ''
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 md:h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-7 h-7 md:w-8 md:h-8 rounded-lg neural-gradient flex items-center justify-center group-hover:scale-110 transition-transform">
              <Brain className="w-3.5 h-3.5 md:w-4 md:h-4 text-white" />
            </div>
            <span className="font-bold text-sm md:text-lg">Genesis <span className="text-gradient">AI</span></span>
          </Link>
          <div className="hidden md:flex items-center gap-6 text-sm">
            {['Features', 'Cognee', 'Demo'].map((item) => (
              <a key={item} href={`#${item.toLowerCase()}`}
                className="text-gray-400 hover:text-white transition-colors relative group"
              >
                {item}
                <span className="absolute -bottom-0.5 left-0 w-0 h-px bg-blue-500 group-hover:w-full transition-all" />
              </a>
            ))}
          </div>
          <Link href="/dashboard"
            className="px-4 py-1.5 md:px-5 md:py-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs md:text-sm font-medium glow-blue group"
          >
            <span className="flex items-center gap-1.5">
              Launch App <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
            </span>
          </Link>
        </div>
      </motion.nav>

      <motion.section style={{ opacity: reduced ? 1 : heroOpacity, scale: reduced ? 1 : heroScale }} className="relative z-10 min-h-dvh flex flex-col items-center justify-center px-4 sm:px-6 pt-16">
        <div className="text-center max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full glass-strong text-[10px] md:text-xs text-blue-300 mb-6 md:mb-8 border border-blue-500/20"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            WeMakeDevs x Cognee Hackathon 2026 — Track: Best Use of Open Source
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-7xl lg:text-8xl font-bold leading-[1.05] mb-4 md:mb-6 tracking-tight"
          >
            <span>The AI That </span>
            <span className="text-gradient">Never Forgets</span><br />
            <span className="text-lg sm:text-xl md:text-3xl lg:text-4xl text-gray-500">
              Powered by <span className="text-blue-400 font-semibold">Cognee</span> Persistent Memory
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="text-sm sm:text-base md:text-xl text-gray-400 max-w-3xl mx-auto mb-8 md:mb-10 leading-relaxed px-2"
          >
            LLMs forget everything between sessions. <span className="text-white">Genesis remembers.</span><br className="hidden sm:block" />
            Using Cognee&apos;s hybrid graph-vector memory, every conversation builds a permanent knowledge graph — 
            so Genesis gets smarter with every interaction, across infinite sessions.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.5 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-3 md:gap-4"
          >
            <Link href="/dashboard"
              className="group relative px-6 py-3 md:px-8 md:py-4 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold text-sm md:text-lg glow-blue"
            >
              <span className="flex items-center gap-2">
                Launch Live Demo <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </span>
            </Link>
            <a href="#cognee"
              className="group px-6 py-3 md:px-8 md:py-4 rounded-xl glass-strong text-white font-semibold text-sm md:text-lg hover:bg-white/5 transition-all flex items-center gap-2"
            >
              <Database className="w-4 h-4" /> How Cognee Powers This
            </a>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.7 }}
            className="mt-8 md:mt-10 grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 max-w-3xl mx-auto"
          >
            {[
              { label: 'Cognee API Ops', value: '4/4', sub: 'remember · recall · improve · forget' },
              { label: 'Memory Entries', value: '67+', sub: 'across all sessions' },
              { label: 'Knowledge Nodes', value: '79+', sub: 'entities + relationships' },
              { label: 'Evolution Level', value: '3', sub: 'skills, reflections, predictions' },
            ].map((s, i) => (
              <div key={s.label} className="glass rounded-xl p-3 md:p-4 text-center">
                <p className="text-[9px] md:text-[10px] text-gray-600 tracking-wider uppercase">{s.label}</p>
                <p className="text-xl md:text-2xl font-bold font-mono mt-1">{s.value}</p>
                <p className="text-[8px] md:text-[9px] text-gray-600 mt-0.5">{s.sub}</p>
              </div>
            ))}
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2 }}
          className="absolute bottom-8 flex flex-col items-center gap-1"
        >
          <span className="text-[9px] text-gray-600 tracking-widest uppercase">Scroll</span>
          <ChevronDown className="w-4 h-4 text-gray-500 animate-bounce" />
        </motion.div>
      </motion.section>

      <ParallaxSection speed={0.08}>
        <section id="features" className="relative z-10 py-20 md:py-32 px-4 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <FadeIn>
              <div className="text-center mb-10 md:mb-16">
                <span className="text-[10px] md:text-xs text-blue-400 tracking-widest uppercase font-medium">The Problem</span>
                <h2 className="text-3xl md:text-5xl lg:text-6xl font-bold mt-2 md:mt-3 mb-3 md:mb-4">
                  AI Has <span className="text-rose-400">Amnesia</span>
                </h2>
                <p className="text-sm md:text-lg text-gray-400 max-w-3xl mx-auto px-4">
                  Every time you talk to ChatGPT, Claude, or Gemini, it&apos;s a first date. 
                  It remembers nothing from your last conversation. <span className="text-white">Cognee changes that.</span>
                </p>
              </div>
            </FadeIn>

            <div className="grid md:grid-cols-2 gap-6 md:gap-8 mb-16 md:mb-20">
              <FadeIn>
                <div className="glass rounded-2xl p-5 md:p-6 border border-red-500/20">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </div>
                    <span className="font-semibold text-sm">Without Cognee</span>
                  </div>
                  <div className="space-y-2 text-xs md:text-sm text-gray-500">
                    <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-red-400" /> Session 1: Tell AI about your project</div>
                    <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-red-400" /> Session 2: AI has no memory of session 1</div>
                    <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-red-400" /> Session 3: Repeat yourself endlessly</div>
                    <div className="mt-2 p-2 rounded-lg bg-red-500/5 text-red-400 text-[10px]">❌ No growth. No evolution. No memory.</div>
                  </div>
                </div>
              </FadeIn>
              <FadeIn delay={0.1}>
                <div className="glass rounded-2xl p-5 md:p-6 border border-green-500/20">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                      <Brain className="w-4 h-4 text-green-400" />
                    </div>
                    <span className="font-semibold text-sm">With Cognee + Genesis</span>
                  </div>
                  <div className="space-y-2 text-xs md:text-sm text-gray-500">
                    <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-green-400" /> Session 1: Chat about Project Helios</div>
                    <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-green-400" /> Session 2: &ldquo;How&apos;s Helios going?&rdquo; — Genesis recalls everything</div>
                    <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-green-400" /> Session 3: Genesis suggests improvements based on history</div>
                    <div className="mt-2 p-2 rounded-lg bg-green-500/5 text-green-400 text-[10px]">✅ Persistent memory. Cross-session recall. Self-evolution.</div>
                  </div>
                </div>
              </FadeIn>
            </div>

            <FadeIn>
              <div className="text-center mb-10 md:mb-16">
                <span className="text-[10px] md:text-xs text-purple-400 tracking-widest uppercase font-medium">What Genesis Does</span>
                <h2 className="text-3xl md:text-5xl lg:text-6xl font-bold mt-2 md:mt-3 mb-3 md:mb-4">
                  Beyond <span className="text-gradient">Chat</span>
                </h2>
                <p className="text-sm md:text-lg text-gray-400 max-w-2xl mx-auto px-4">
                  Genesis is what happens when you give an LLM <span className="text-white">permanent memory</span>.
                </p>
              </div>
            </FadeIn>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
              {features.map((feature, i) => (
                <FadeIn key={feature.title} delay={i * 0.06}>
                  <div className="group h-full">
                    <div className="glass rounded-2xl p-5 md:p-6 hover:glass-hover transition-all duration-200 card-shine border border-transparent hover:border-white/10 h-full">
                      <div className={`w-10 h-10 md:w-12 md:h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-600/10 flex items-center justify-center mb-3 md:mb-4 group-hover:scale-110 transition-transform duration-200`}>
                        <feature.icon className="w-5 h-5 md:w-6 md:h-6 text-blue-400" />
                      </div>
                      <h3 className="text-base md:text-lg font-semibold mb-1 md:mb-2 group-hover:text-white transition-colors">{feature.title}</h3>
                      <p className="text-xs md:text-sm text-gray-500 leading-relaxed group-hover:text-gray-400 transition-colors">{feature.desc}</p>
                    </div>
                  </div>
                </FadeIn>
              ))}
            </div>
          </div>
        </section>
      </ParallaxSection>

      <ParallaxSection speed={-0.05}>
        <section id="cognee" className="relative z-10 py-20 md:py-32 px-4 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <FadeIn>
              <div className="text-center mb-10 md:mb-16">
                <span className="text-[10px] md:text-xs text-blue-400 tracking-widest uppercase font-medium">Deep Integration</span>
                <h2 className="text-3xl md:text-5xl lg:text-6xl font-bold mt-2 md:mt-3 mb-3 md:mb-4">
                  Cognee <span className="text-gradient">API</span> Operations
                </h2>
                <p className="text-sm md:text-lg text-gray-400 max-w-2xl mx-auto px-4">
                  Every memory lifecycle operation — <code className="text-blue-300">remember</code>, <code className="text-purple-300">recall</code>, <code className="text-teal-300">improve</code>, <code className="text-amber-300">forget</code> — is used throughout Genesis.
                </p>
              </div>
            </FadeIn>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4 mb-12 md:mb-16">
              {cogneeApis.map((api, i) => (
                <FadeIn key={api.title} delay={i * 0.08}>
                  <div className="glass-strong rounded-2xl p-5 md:p-6 border border-white/5 hover:border-blue-500/20 transition-all group">
                    <div className="flex items-start gap-4">
                      <div className={`w-10 h-10 md:w-12 md:h-12 rounded-xl bg-gradient-to-br ${api.color} flex items-center justify-center flex-shrink-0`}>
                        <api.icon className="w-5 h-5 md:w-6 md:h-6 text-blue-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-base md:text-lg font-bold font-mono">{api.title}</h3>
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">API</span>
                        </div>
                        <p className="text-xs md:text-sm text-gray-400 mb-2">{api.desc}</p>
                        <code className="text-[10px] md:text-xs text-gray-500 bg-white/5 px-2 py-1 rounded-md block truncate">{api.code}</code>
                      </div>
                    </div>
                  </div>
                </FadeIn>
              ))}
            </div>

            <FadeIn>
              <div className="glass rounded-2xl p-6 md:p-8 border border-blue-500/20">
                <div className="flex items-center gap-3 mb-4">
                  <CpuIcon className="w-5 h-5 text-blue-400" />
                  <span className="text-sm font-semibold">Where Cognee Is Used in Genesis</span>
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 text-[10px] md:text-xs text-gray-400">
                  <div className="p-3 rounded-xl bg-white/5"><span className="text-blue-300 font-mono">remember()</span> — Every chat message, file upload, and event is stored via <code className="text-blue-300">remember_content()</code></div>
                  <div className="p-3 rounded-xl bg-white/5"><span className="text-purple-300 font-mono">recall()</span> — RAG context retrieval and knowledge graph queries use Cognee&apos;s hybrid search</div>
                  <div className="p-3 rounded-xl bg-white/5"><span className="text-teal-300 font-mono">improve()</span> — Memory enrichment and knowledge graph optimization runs on the schedule</div>
                  <div className="p-3 rounded-xl bg-white/5"><span className="text-amber-300 font-mono">forget()</span> — Memory pruning and dataset management for privacy compliance</div>
                </div>
              </div>
            </FadeIn>
          </div>
        </section>
      </ParallaxSection>

      <ParallaxSection speed={0.05}>
        <section id="demo" className="relative z-10 py-20 md:py-32 px-4 sm:px-6">
          <div className="max-w-5xl mx-auto">
            <FadeIn>
              <div className="glass rounded-2xl md:rounded-3xl p-6 md:p-8 lg:p-12 glow-card">
                <div className="text-center mb-6 md:mb-10">
                  <span className="text-[10px] md:text-xs text-purple-400 tracking-widest uppercase font-medium">Live Demo</span>
                  <h2 className="text-2xl md:text-4xl lg:text-5xl font-bold mt-2 md:mt-3">
                    Cross-Session <span className="text-gradient">Memory</span> in Action
                  </h2>
                  <p className="text-sm text-gray-500 mt-2">Ask Genesis about &quot;Project Helios&quot; — a topic only mentioned in a previous session. Cognee remembers.</p>
                </div>

                <div className="grid md:grid-cols-2 gap-6 md:gap-8 items-center">
                  <div className="space-y-3 md:space-y-4">
                    <div className="flex items-center gap-2 md:gap-3 p-3 md:p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                      <MessageCircle className="w-4 h-4 md:w-5 md:h-5 text-blue-400 flex-shrink-0" />
                      <p className="text-xs md:text-sm text-gray-300">&ldquo;I&apos;m planning a project called Project Helios using Svelte.&rdquo;</p>
                    </div>
                    <div className="flex items-start gap-2 md:gap-3 p-3 md:p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
                      <Brain className="w-4 h-4 md:w-5 md:h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-xs md:text-sm text-gray-300">&ldquo;Logged. I&apos;ll remember Project Helios — Svelte-based web application, user-focused design.&rdquo;</p>
                      </div>
                    </div>
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      className="flex items-center gap-2 p-2 px-3 rounded-lg bg-amber-500/10 border border-amber-500/20"
                    >
                      <span className="text-[10px] text-amber-400">⏱ New session — hours or days later...</span>
                    </motion.div>
                    <div className="flex items-center gap-2 md:gap-3 p-3 md:p-4 rounded-xl bg-green-500/10 border border-green-500/20">
                      <MessageCircle className="w-4 h-4 md:w-5 md:h-5 text-green-400 flex-shrink-0" />
                      <p className="text-xs md:text-sm text-gray-300">&ldquo;You&apos;re back to Project Helios. What&apos;s the latest on your Svelte application?&rdquo;</p>
                    </div>
                  </div>

                  <div className="h-48 md:h-72 lg:h-80 rounded-xl md:rounded-2xl bg-gradient-to-br from-blue-900/30 via-purple-900/20 to-teal-900/30 border border-white/5 flex items-center justify-center relative overflow-hidden">
                    <motion.div
                      className="absolute inset-0"
                      animate={reduced ? {} : { backgroundPosition: ['0% 0%', '100% 100%'] }}
                      transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
                      style={{ backgroundImage: 'radial-gradient(circle at 30% 50%, rgba(37,99,235,0.1) 0%, transparent 50%), radial-gradient(circle at 70% 50%, rgba(147,51,234,0.1) 0%, transparent 50%)' }}
                    />
                    <div className="relative text-center px-4">
                      <Database className="w-8 h-8 md:w-12 md:h-12 text-blue-400 mx-auto mb-2 md:mb-3 animate-breathe" />
                      <p className="text-xs md:text-sm text-gray-500">Cognee Memory Graph</p>
                      <p className="text-[10px] md:text-xs text-gray-600 mt-1">Vector + Graph Hybrid Storage</p>
                      <div className="flex justify-center gap-2 md:gap-3 mt-3 md:mt-4">
                        {['#3b82f6', '#a855f7', '#2dd4bf'].map((c, i) => (
                          <motion.div
                            key={c}
                            style={{ backgroundColor: c }}
                            className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full"
                            animate={reduced ? {} : { scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                            transition={{ duration: 2, repeat: Infinity, delay: i * 0.5 }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </FadeIn>
          </div>
        </section>
      </ParallaxSection>

      <ParallaxSection speed={0.05}>
        <section id="pipeline" className="relative z-10 py-20 md:py-32 px-4 sm:px-6">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-2 gap-8 md:gap-16 items-start">
              <FadeIn>
                <span className="text-[10px] md:text-xs text-teal-400 tracking-widest uppercase font-medium">How It Works</span>
                <h2 className="text-3xl md:text-5xl font-bold mt-2 md:mt-3 mb-6 md:mb-8">
                  From Chat to <span className="text-gradient">Evolution</span>
                </h2>
                <div className="space-y-2 md:space-y-3">
                  {pipelineSteps.map((item, i) => (
                    <motion.div
                      key={item.step}
                      initial={{ opacity: 0, x: -15 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true, margin: '-40px' }}
                      transition={{ delay: i * 0.06, duration: 0.3 }}
                    >
                      <div className="flex items-center gap-3 md:gap-4 glass rounded-xl p-3 md:p-4 hover:glass-hover transition-all">
                        <div className="w-8 h-8 md:w-10 md:h-10 rounded-lg neural-gradient flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                          <item.icon className="w-4 h-4 md:w-5 md:h-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-xs md:text-sm">{item.step}</p>
                          <p className="text-[10px] md:text-xs text-gray-500 truncate">{item.desc}</p>
                        </div>
                        {i < pipelineSteps.length - 1 && (
                          <ArrowRight className="w-3 h-3 md:w-4 md:h-4 text-gray-600 flex-shrink-0" />
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </FadeIn>

              <div className="space-y-4 md:space-y-6">
                <FadeIn delay={0.1}>
                  <div className="glass-strong rounded-2xl p-5 md:p-6">
                    <div className="flex items-center justify-between gap-3 mb-4">
                      <div className="flex items-center gap-2 md:gap-3">
                        <Activity className="w-4 h-4 text-green-400" />
                        <span className="text-green-400 font-medium text-xs md:text-sm">Brain Health: 88%</span>
                      </div>
                      <div className="flex items-center gap-0.5 md:gap-1">
                        {[8, 12, 18, 12, 8].map((h, i) => (
                          <motion.div
                            key={i}
                            className="w-1 md:w-1.5 rounded-full bg-gradient-to-t from-blue-500 to-purple-500"
                            animate={reduced ? {} : { height: [h * 0.5, h, h * 0.5] }}
                            transition={{ duration: 1, repeat: Infinity, delay: i * 0.1 }}
                          />
                        ))}
                      </div>
                    </div>
                    <div className="space-y-2.5 md:space-y-3">
                      {[
                        { label: 'Memory Count', value: '67', progress: 85, color: 'bg-blue-500' },
                        { label: 'Knowledge Graph Nodes', value: '79', progress: 62, color: 'bg-purple-500' },
                        { label: 'Relationships Inferred', value: '257', progress: 91, color: 'bg-teal-500' },
                        { label: 'Skills Detected', value: '5', progress: 45, color: 'bg-amber-500' },
                        { label: 'Evolution Level', value: '3', progress: 62, color: 'bg-green-500' },
                      ].map((stat) => (
                        <div key={stat.label}>
                          <div className="flex items-center justify-between text-[10px] md:text-xs mb-0.5 md:mb-1">
                            <span className="text-gray-400">{stat.label}</span>
                            <span className="font-mono font-bold text-white text-xs md:text-sm">{stat.value}</span>
                          </div>
                          <div className="w-full h-1 rounded-full bg-white/5 overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              whileInView={{ width: `${stat.progress}%` }}
                              viewport={{ once: true }}
                              transition={{ duration: 0.8, delay: 0.2 }}
                              className={`h-full rounded-full ${stat.color}`}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </FadeIn>

                <FadeIn delay={0.2}>
                  <div className="grid grid-cols-2 gap-2 md:gap-3">
                    {[
                      { text: 'Genesis remembered architecture preferences from weeks ago using Cognee.', author: 'Alex K.' },
                      { text: 'The Cognee-powered knowledge graph surfaced relationships I never saw.', author: 'Sarah M.' },
                    ].map((t, i) => (
                      <div key={i} className="glass rounded-xl p-3 md:p-4">
                        <Quote className="w-3 h-3 md:w-4 md:h-4 text-blue-400 mb-1.5 md:mb-2 opacity-50" />
                        <p className="text-[10px] md:text-xs text-gray-400 leading-relaxed mb-2">&ldquo;{t.text}&rdquo;</p>
                        <p className="text-[9px] md:text-[10px] font-medium">{t.author}</p>
                      </div>
                    ))}
                  </div>
                </FadeIn>
              </div>
            </div>
          </div>
        </section>
      </ParallaxSection>

      <section className="relative z-10 py-16 md:py-20 px-4 sm:px-6">
        <FadeIn>
          <div className="max-w-4xl mx-auto glass-strong rounded-2xl md:rounded-3xl p-8 md:p-12 lg:p-16 text-center glow-card">
            <Cpu className="w-8 h-8 md:w-10 md:h-10 text-blue-400 mx-auto mb-4 md:mb-6" />
            <h2 className="text-2xl md:text-4xl lg:text-5xl font-bold mb-3 md:mb-4">
              An AI That <span className="text-gradient">Remembers</span> Everything
            </h2>
            <p className="text-sm md:text-lg text-gray-400 mb-6 md:mb-8 max-w-xl mx-auto px-2">
              Every conversation, every project, every idea — permanently remembered via Cognee.
              The more you use it, the smarter it gets.
            </p>
            <Link href="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3 md:px-8 md:py-4 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold text-sm md:text-lg glow-blue group"
            >
              Try the Live Demo <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <p className="text-[10px] text-gray-600 mt-4">Pre-seeded with demo data. No signup required.</p>
          </div>
        </FadeIn>
      </section>

      <footer className="relative z-10 border-t border-white/5 py-8 md:py-10 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3 md:gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 md:w-7 md:h-7 rounded-lg neural-gradient flex items-center justify-center">
              <Brain className="w-3 h-3 md:w-3.5 md:h-3.5 text-white" />
            </div>
            <span className="font-semibold text-xs md:text-sm">Genesis AI</span>
          </div>
          <p className="text-[10px] md:text-xs text-gray-600">
            Built for the WeMakeDevs x Cognee Hackathon — Track: Best Use of Open Source
          </p>
          <div className="flex items-center gap-3 md:gap-4 text-[10px] md:text-xs text-gray-600">
            <span className="hover:text-gray-400 transition-colors cursor-pointer">Powered by Cognee</span>
            <span className="w-1 h-1 rounded-full bg-gray-700" />
            <span className="hover:text-gray-400 transition-colors cursor-pointer">Open Source</span>
            <Github className="w-3 h-3 md:w-3.5 md:h-3.5 hover:text-gray-400 transition-colors cursor-pointer" />
          </div>
        </div>
      </footer>
    </div>
  )
}
