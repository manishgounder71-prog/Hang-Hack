const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

async function fetchAPI(endpoint: string, options?: RequestInit, timeoutMs = 10000) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const res = await fetch(`${API_URL}${endpoint}`, {
      headers: { ...headers, ...options?.headers as Record<string, string> },
      ...options,
      signal: controller.signal,
    })
    if (!res.ok) {
      const errorBody = await res.text().catch(() => '')
      throw new Error(`API error: ${res.status} - ${errorBody}`)
    }
    return res.json()
  } finally {
    clearTimeout(timeout)
  }
}

// SSE streaming helper
export async function* streamChat(message: string): AsyncGenerator<string, void, unknown> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }

  const res = await fetch(`${API_URL}/chat?stream=true`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, stream: true }),
  })

  if (!res.ok || !res.body) {
    yield `[Error: ${res.status}]`
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.done) return
            if (data.token) yield data.token
          } catch {
            // skip malformed SSE
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

// WebSocket connection
export function createWebSocket(): WebSocket | null {
  const wsUrl = API_URL.replace(/^http/, 'ws')
  const ws = new WebSocket(`${wsUrl}/ws`)

  ws.onopen = () => {
    ws.send(JSON.stringify({ type: 'ping' }))
  }

  return ws
}

export const api = {
  chat: {
    send: (message: string) =>
      fetchAPI('/chat', {
        method: 'POST',
        body: JSON.stringify({ message, stream: false }),
      }, 30000),
  },
  memories: {
    list: (query = '', limit = 10, forceRefresh = false) =>
      fetchAPI(`/memories?query=${encodeURIComponent(query)}&limit=${limit}${forceRefresh ? '&force_refresh=true' : ''}`),
    get: (id: string) =>
      fetchAPI(`/memories/${id}`),
    create: (content: string, tags: string[] = []) =>
      fetchAPI('/memories', {
        method: 'POST',
        body: JSON.stringify({ content, tags }),
      }),
    improve: () =>
      fetchAPI('/memories/improve', { method: 'POST' }),
    forget: (dataset: string) =>
      fetchAPI(`/memories/forget?dataset=${encodeURIComponent(dataset)}`, { method: 'POST' }),
    stats: () =>
      fetchAPI('/memories/stats'),
  },
  reflections: {
    list: (limit = 20) =>
      fetchAPI(`/reflections?limit=${limit}`),
    get: (id: string) =>
      fetchAPI(`/reflections/${id}`),
    create: (data: { trigger_event: string; what_worked?: string; what_failed?: string }) =>
      fetchAPI('/reflections', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      fetchAPI(`/reflections/${id}`, { method: 'DELETE' }),
    stats: () =>
      fetchAPI('/reflections/stats/summary'),
  },
  predictions: {
    list: (limit = 20) =>
      fetchAPI(`/predictions?limit=${limit}`),
    get: (id: string) =>
      fetchAPI(`/predictions/${id}`),
    create: (type = 'general') =>
      fetchAPI(`/predictions?prediction_type=${type}`, { method: 'POST' }),
    fulfill: (id: string, fulfilled: boolean) =>
      fetchAPI(`/predictions/${id}/fulfill?fulfilled=${fulfilled}`, { method: 'POST' }),
    delete: (id: string) =>
      fetchAPI(`/predictions/${id}`, { method: 'DELETE' }),
    stats: () =>
      fetchAPI('/predictions/stats/summary'),
  },
  skills: {
    list: () =>
      fetchAPI('/skills'),
    get: (id: string) =>
      fetchAPI(`/skills/${id}`),
    detect: () =>
      fetchAPI('/skills/detect', { method: 'POST' }),
    delete: (id: string) =>
      fetchAPI(`/skills/${id}`, { method: 'DELETE' }),
    stats: () =>
      fetchAPI('/skills/stats/summary'),
  },
  knowledge: {
    graph: (userId = 'default') =>
      fetchAPI(`/knowledge/graph?user_id=${userId}`),
    search: (query: string) =>
      fetchAPI(`/knowledge/search?query=${encodeURIComponent(query)}`),
    status: () =>
      fetchAPI('/knowledge/status'),
  },
  dashboard: {
    get: (userId = 'default', forceRefresh = false) =>
      fetchAPI(`/dashboard?user_id=${userId}${forceRefresh ? '&force_refresh=true' : ''}`),
  },
  upload: {
    file: async (file: File, userId = 'default') => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('user_id', userId)

      const res = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
      return res.json()
    },
    supported: () =>
      fetchAPI('/upload/supported'),
  },
  settings: {
    get: (userId = 'default') =>
      fetchAPI(`/settings?user_id=${userId}`),
    update: (data: Record<string, any>, userId = 'default') =>
      fetchAPI(`/settings?user_id=${userId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    reset: (userId = 'default') =>
      fetchAPI(`/settings/reset?user_id=${userId}`, { method: 'POST' }),
  },
  ws: {
    status: () =>
      fetchAPI('/ws/status'),
  },
}
