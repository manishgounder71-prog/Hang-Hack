'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  Brain, Network, Eye, Zap, TrendingUp,
  BarChart3, BookOpen, Settings,
  Menu, X, Activity, Cpu
} from 'lucide-react'

const navItems = [
  { icon: Brain, label: 'Dashboard', href: '/dashboard' },
  { icon: Network, label: 'Brain', href: '/dashboard/brain' },
  { icon: BookOpen, label: 'Timeline', href: '/dashboard/timeline' },
  { icon: Zap, label: 'Skills', href: '/dashboard/skills' },
  { icon: TrendingUp, label: 'Predictions', href: '/dashboard/predictions' },
  { icon: Eye, label: 'Reflections', href: '/dashboard/reflections' },
  { icon: BarChart3, label: 'Analytics', href: '/dashboard/analytics' },
  { icon: Settings, label: 'Settings', href: '/dashboard/settings' },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-[rgb(5,5,25)] noise-bg text-white">
      {/* Navbar */}
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="fixed top-0 left-0 right-0 z-50 glass-strong border-b border-white/5 h-14"
      >
        <div className="flex items-center justify-between h-full px-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden w-8 h-8 rounded-lg flex items-center justify-center hover:bg-white/5 transition-colors"
            >
              {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg neural-gradient flex items-center justify-center">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-sm">Genesis <span className="text-gradient">AI</span></span>
            </div>
            <span className="hidden sm:inline-flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/20">
              <Cpu className="w-3 h-3" />
              Lvl 3
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs">
              <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              <span className="text-gray-500 hidden sm:inline">Brain Active</span>
            </div>
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-[10px] font-bold">
              G
            </div>
          </div>
        </div>
      </motion.nav>

      {/* Sidebar */}
      <motion.aside
        initial={{ x: -200 }}
        animate={{ x: 0 }}
        className={`fixed top-14 left-0 bottom-0 w-56 glass-strong border-r border-white/5 z-40 transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        <div className="p-3 space-y-0.5 pb-24">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))
            return (
              <Link
                key={item.label}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 sm:py-2 rounded-lg text-sm transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/10 text-blue-400 border-l-2 border-blue-500'
                    : 'text-gray-500 hover:text-white hover:bg-white/5 border-l-2 border-transparent'
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            )
          })}
        </div>
        <div className="absolute bottom-4 left-3 right-3 p-3 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-500/5 border border-white/5">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-3 h-3 text-green-400" />
            <span className="text-[10px] text-green-400 font-medium">System Status</span>
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[10px]">
              <span className="text-gray-600">Memory</span>
              <span className="text-green-400">98%</span>
            </div>
            <div className="w-full h-1 rounded-full bg-white/5 overflow-hidden">
              <div className="h-full rounded-full bg-green-500" style={{ width: '98%' }} />
            </div>
          </div>
        </div>
      </motion.aside>

      {/* Main content viewport */}
      <main className="lg:ml-56 pt-14 min-h-dvh">
        {children}
      </main>
    </div>
  )
}
