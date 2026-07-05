'use client'

import { useEffect, useState, useCallback, useId } from 'react'
import { motion } from 'framer-motion'
import {
  Settings, User, Shield, Bell, Database,
  Cpu, Globe, Key, Trash2, RefreshCw,
  AlertCircle, CheckCircle2, ExternalLink,
  Activity, Cog, Wifi, HardDrive,
} from 'lucide-react'
import { api } from '@/lib/api'

interface SettingsData {
  memory_aware_responses: boolean
  auto_reflect_after_chat: boolean
  predict_next_topics: boolean
  skill_auto_detection: boolean
  response_style: string
  memory_recall_count: number
  anonymous_usage_data: boolean
  encrypt_memories: boolean
  session_timeout: string
  weekly_summary: boolean
  skill_detected_notify: boolean
  prediction_alerts: boolean
  system_updates: boolean
  llm_provider: string
  llm_model: string
  llm_api_key: string
  cognee_api_key: string
  enable_websocket: boolean
  streaming_responses: boolean
  connection_mode: string
  username: string
  email: string
  storage_capacity_pct: number
}

const defaultSettings: SettingsData = {
  memory_aware_responses: true, auto_reflect_after_chat: true, predict_next_topics: true,
  skill_auto_detection: false, response_style: 'balanced', memory_recall_count: 10,
  anonymous_usage_data: false, encrypt_memories: true, session_timeout: '24 hours',
  weekly_summary: true, skill_detected_notify: true, prediction_alerts: false, system_updates: true,
  llm_provider: 'openai', llm_model: 'gpt-4o-mini', llm_api_key: '', cognee_api_key: '',
  enable_websocket: true, streaming_responses: true, connection_mode: 'auto',
  username: '', email: '', storage_capacity_pct: 34,
}

function Toggle({ label, desc, enabled, onChange }: {
  label: string; desc?: string; enabled: boolean; onChange: (v: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <p className="text-xs text-gray-300">{label}</p>
        {desc && <p className="text-[10px] text-gray-600">{desc}</p>}
      </div>
      <button
        onClick={() => onChange(!enabled)}
        className={`relative w-9 h-5 rounded-full transition-colors duration-300 ${
          enabled ? 'bg-blue-500' : 'bg-white/10'
        }`}
      >
        <motion.div
          animate={{ x: enabled ? 16 : 2 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          className="absolute top-1 left-0.5 w-3.5 h-3.5 rounded-full bg-white shadow"
        />
      </button>
    </div>
  )
}

function SelectInput({ label, options, value, onChange }: {
  label: string; options: string[]; value: string; onChange: (v: string) => void
}) {
  const id = useId()
  return (
    <div className="py-2">
      <label htmlFor={id} className="text-xs text-gray-400 mb-1.5 block">{label}</label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500/40 focus:bg-white/[0.06] transition-all text-gray-300"
      >
        {options.map((opt) => (
          <option key={opt} value={opt.toLowerCase()} className="bg-[rgb(5,5,25)]">{opt}</option>
        ))}
      </select>
    </div>
  )
}

function TextInput({ label, icon: Icon, value, onChange, isPassword = false, placeholder = '' }: {
  label: string; icon: any; value: string; onChange: (v: string) => void; isPassword?: boolean; placeholder?: string
}) {
  const id = useId()
  return (
    <div className="py-2">
      <label htmlFor={id} className="text-xs text-gray-400 mb-1 flex items-center gap-1">
        {Icon && <Icon className="w-3 h-3" />}
        {label}
      </label>
      <input
        id={id}
        type={isPassword ? 'password' : 'text'}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500/40 transition-all text-gray-300 font-mono placeholder:text-gray-700"
      />
    </div>
  )
}

function SettingSection({ icon: Icon, title, desc, children }: {
  icon: any; title: string; desc?: string; children: React.ReactNode
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-2xl p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/10 flex items-center justify-center">
          <Icon className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">{title}</h3>
          {desc && <p className="text-[10px] text-gray-500">{desc}</p>}
        </div>
      </div>
      {children}
    </motion.div>
  )
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsData>(defaultSettings)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'general' | 'data' | 'api'>('general')

  const fetchSettings = useCallback(async () => {
    try {
      setError('')
      const data = await api.settings.get()
      setSettings({ ...defaultSettings, ...data })
    } catch {
      setError('Could not load settings')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchSettings() }, [fetchSettings])

  const handleSave = async () => {
    setSaving(true)
    setError('')
    try {
      await api.settings.update(settings)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      setError('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const update = <K extends keyof SettingsData>(key: K, value: SettingsData[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const tabs = [
    { id: 'general' as const, label: 'General', icon: Cog },
    { id: 'data' as const, label: 'Data', icon: Database },
    { id: 'api' as const, label: 'API', icon: Key },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-2 mb-1">
          <Settings className="w-4 h-4 text-gray-400" />
          <span className="text-[10px] text-gray-400 tracking-widest uppercase font-medium">Configuration</span>
        </div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold mb-1">Settings</h1>
            <p className="text-sm text-gray-500">Configure your Genesis AI system preferences</p>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="text-[10px] px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:opacity-90 transition-all disabled:opacity-50 flex items-center gap-1.5"
          >
            {saving ? (
              <><RefreshCw className="w-3 h-3 animate-spin" /> Saving</>
            ) : saved ? (
              <><CheckCircle2 className="w-3 h-3" /> Saved</>
            ) : (
              <><RefreshCw className="w-3 h-3" /> Save Changes</>
            )}
          </button>
        </div>
        <div className="flex gap-2">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-medium transition-all ${
                tab === t.id
                  ? 'bg-gradient-to-r from-blue-600/30 to-purple-600/20 text-blue-400 border border-blue-500/20'
                  : 'text-gray-500 hover:text-white hover:bg-white/5 border border-transparent'
              }`}
            >
              <t.icon className="w-3 h-3" />
              {t.label}
            </button>
          ))}
        </div>
      </motion.div>

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        {saved && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 p-3 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 text-xs">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            Settings saved successfully
          </motion.div>
        )}

        {tab === 'general' && (
          <div className="space-y-4">
            <SettingSection icon={User} title="Profile">
              <TextInput label="Username" icon={User} value={settings.username} onChange={(v) => update('username', v)} />
              <TextInput label="Email" icon={Globe} value={settings.email} onChange={(v) => update('email', v)} />
            </SettingSection>
            <SettingSection icon={Cpu} title="AI Behavior">
              <Toggle label="Memory-aware responses" desc="Reference past conversations in replies" enabled={settings.memory_aware_responses} onChange={(v) => update('memory_aware_responses', v)} />
              <Toggle label="Auto-reflect after chat" desc="Generate reflections after conversations" enabled={settings.auto_reflect_after_chat} onChange={(v) => update('auto_reflect_after_chat', v)} />
              <Toggle label="Predict next topics" desc="Proactively predict what you'll ask next" enabled={settings.predict_next_topics} onChange={(v) => update('predict_next_topics', v)} />
              <Toggle label="Skill auto-detection" desc="Detect reusable patterns automatically" enabled={settings.skill_auto_detection} onChange={(v) => update('skill_auto_detection', v)} />
              <SelectInput label="Response style" options={['Concise', 'Detailed', 'Balanced']} value={settings.response_style} onChange={(v) => update('response_style', v)} />
              <SelectInput label="Memory recall count" options={['5', '10', '20', '50']} value={String(settings.memory_recall_count)} onChange={(v) => update('memory_recall_count', parseInt(v))} />
            </SettingSection>
            <SettingSection icon={Shield} title="Privacy & Security">
              <Toggle label="Anonymous usage data" enabled={settings.anonymous_usage_data} onChange={(v) => update('anonymous_usage_data', v)} />
              <Toggle label="Encrypt memories at rest" enabled={settings.encrypt_memories} onChange={(v) => update('encrypt_memories', v)} />
              <SelectInput label="Session timeout" options={['30 minutes', '1 hour', '4 hours', '24 hours', 'Never']} value={settings.session_timeout} onChange={(v) => update('session_timeout', v)} />
            </SettingSection>
            <SettingSection icon={Bell} title="Notifications">
              <Toggle label="Weekly summary" enabled={settings.weekly_summary} onChange={(v) => update('weekly_summary', v)} />
              <Toggle label="Skill detected" enabled={settings.skill_detected_notify} onChange={(v) => update('skill_detected_notify', v)} />
              <Toggle label="Prediction alerts" enabled={settings.prediction_alerts} onChange={(v) => update('prediction_alerts', v)} />
              <Toggle label="System updates" enabled={settings.system_updates} onChange={(v) => update('system_updates', v)} />
            </SettingSection>
          </div>
        )}

        {tab === 'data' && (
          <div className="space-y-4">
            <SettingSection icon={HardDrive} title="Storage & Memory">
              <div className="grid grid-cols-3 gap-3 mb-4">
                {[
                  { label: 'Total Memories', value: '1,247', color: 'text-blue-400' },
                  { label: 'Skills', value: '6', color: 'text-amber-400' },
                  { label: 'Reflections', value: '24', color: 'text-purple-400' },
                ].map((s) => (
                  <div key={s.label} className="text-center p-3 rounded-xl bg-white/5">
                    <p className={`text-lg font-bold font-mono ${s.color}`}>{s.value}</p>
                    <p className="text-[9px] text-gray-600">{s.label}</p>
                  </div>
                ))}
              </div>
              <div className="w-full h-2 rounded-full bg-white/5 overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500" style={{ width: `${settings.storage_capacity_pct}%` }} />
              </div>
              <p className="text-[10px] text-gray-600 mt-1">{settings.storage_capacity_pct}% of storage capacity used</p>
              <div className="mt-3">
                <label className="text-xs text-gray-400 mb-1 block">Storage threshold</label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={settings.storage_capacity_pct}
                  onChange={(e) => update('storage_capacity_pct', parseInt(e.target.value))}
                  className="w-full accent-blue-500"
                />
              </div>
            </SettingSection>
            <SettingSection icon={Database} title="Data Management">
              <div className="flex items-center justify-between py-2">
                <div className="flex items-start gap-2">
                  <Trash2 className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-xs text-gray-300">Clear Chat History</p>
                    <p className="text-[10px] text-gray-600">Remove all chat messages but keep memories</p>
                  </div>
                </div>
                <button className="text-[10px] px-3 py-1.5 rounded-lg bg-red-500/20 text-red-400 border border-red-500/20 hover:bg-red-500/30 transition-all whitespace-nowrap">Execute</button>
              </div>
              <div className="border-t border-white/5 pt-3 mt-2">
                <button className="flex items-center gap-2 text-[10px] text-gray-500 hover:text-blue-400 transition-colors">
                  <ExternalLink className="w-3 h-3" />
                  Export all data as JSON
                </button>
              </div>
            </SettingSection>
            <SettingSection icon={Activity} title="System Health">
              <div className="space-y-2">
                {[
                  { label: 'Database', status: 'Connected', ok: true },
                  { label: 'Cognee Memory', status: 'Available', ok: true },
                  { label: 'LLM Provider', status: settings.llm_api_key ? 'Online' : 'Not configured', ok: !!settings.llm_api_key },
                  { label: 'Redis Cache', status: 'Connected', ok: true },
                  { label: 'WebSocket', status: settings.enable_websocket ? 'Active' : 'Disabled', ok: settings.enable_websocket },
                ].map((sys) => (
                  <div key={sys.label} className="flex items-center justify-between py-1.5">
                    <span className="text-xs text-gray-400">{sys.label}</span>
                    <span className={`flex items-center gap-1 text-[10px] ${sys.ok ? 'text-green-400' : 'text-amber-400'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${sys.ok ? 'bg-green-400' : 'bg-amber-400'}`} />
                      {sys.status}
                    </span>
                  </div>
                ))}
              </div>
            </SettingSection>
          </div>
        )}

        {tab === 'api' && (
          <div className="space-y-4">
            <SettingSection icon={Key} title="API Keys">
              <TextInput label="LLM API Key" icon={Globe} value={settings.llm_api_key} onChange={(v) => update('llm_api_key', v)} isPassword placeholder="sk-..." />
              <SelectInput label="LLM Provider" options={['OpenAI', 'Anthropic', 'Groq', 'Google Gemini', 'Ollama (Local)']} value={settings.llm_provider} onChange={(v) => update('llm_provider', v)} />
              <SelectInput label="LLM Model" options={['gpt-4o', 'gpt-4o-mini', 'claude-3-5-sonnet', 'gemini-2.0-flash', 'llama-3.3-70b-versatile']} value={settings.llm_model} onChange={(v) => update('llm_model', v)} />
              <TextInput label="Cognee API Key (optional)" icon={Database} value={settings.cognee_api_key} onChange={(v) => update('cognee_api_key', v)} isPassword placeholder="Enter Cognee API key" />
            </SettingSection>
            <SettingSection icon={Wifi} title="WebSocket & Streaming">
              <Toggle label="Enable WebSocket" desc="Real-time dashboard updates" enabled={settings.enable_websocket} onChange={(v) => update('enable_websocket', v)} />
              <Toggle label="Streaming responses" desc="Token-by-token AI responses" enabled={settings.streaming_responses} onChange={(v) => update('streaming_responses', v)} />
              <SelectInput label="Connection mode" options={['Auto', 'WebSocket Only', 'Polling Only']} value={settings.connection_mode} onChange={(v) => update('connection_mode', v)} />
            </SettingSection>
            <SettingSection icon={Globe} title="API Endpoints">
              <div className="space-y-2">
                {[
                  { label: 'Backend API', url: 'http://localhost:8000', status: 'running' },
                  { label: 'Frontend', url: 'http://localhost:3000', status: 'running' },
                  { label: 'Documentation', url: 'http://localhost:8000/docs', status: 'available' },
                ].map((svc) => (
                  <div key={svc.label} className="flex items-center justify-between py-2 px-3 rounded-lg bg-white/5">
                    <div>
                      <p className="text-xs text-gray-300">{svc.label}</p>
                      <p className="text-[10px] text-gray-600 font-mono">{svc.url}</p>
                    </div>
                    <span className="text-[9px] px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 border border-green-500/20 capitalize">{svc.status}</span>
                  </div>
                ))}
              </div>
            </SettingSection>
          </div>
        )}

        <div className="text-center py-6">
          <p className="text-[10px] text-gray-700">Genesis AI v1.0.0 · Built for WeMakeDevs x Cognee Hackathon</p>
        </div>
    </div>
  )
}
