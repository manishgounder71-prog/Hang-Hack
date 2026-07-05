'use client'

import { useEffect, useRef, useCallback, useState } from 'react'

type MessageHandler = (data: any) => void

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

/**
 * Hook that connects to the Genesis AI WebSocket, auto-reconnects on disconnect,
 * and invokes handlers for specific message types.
 */
export function useWebSocket(handlers?: Record<string, MessageHandler>) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const handlersRef = useRef(handlers)
  const [connected, setConnected] = useState(false)
  const [reconnecting, setReconnecting] = useState(false)
  const attemptRef = useRef(0)

  // Keep handlers ref current without re-triggering effect
  handlersRef.current = handlers

  const connect = useCallback(() => {
    // Clean up any existing connection
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    const wsUrl = API_URL.replace(/^http/, 'ws')
    const ws = new WebSocket(`${wsUrl}/ws`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      setReconnecting(false)
      attemptRef.current = 0
      ws.send(JSON.stringify({ type: 'ping' }))
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const type = data.type
        if (type && handlersRef.current?.[type]) {
          handlersRef.current[type](data)
        }
      } catch {
        // Ignore malformed messages
      }
    }

    ws.onclose = () => {
      setConnected(false)
      // Auto-reconnect with exponential backoff
      attemptRef.current += 1
      const delay = Math.min(1000 * Math.pow(2, attemptRef.current), 30000)
      setReconnecting(true)
      reconnectTimer.current = setTimeout(() => {
        connect()
      }, delay)
    }

    ws.onerror = () => {
      // onclose will fire after onerror, triggering reconnect
      ws.close()
    }
  }, [])

  const send = useCallback((data: Record<string, any>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  const subscribe = useCallback((topic: string) => {
    send({ type: 'subscribe', topic })
  }, [send])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      if (wsRef.current) {
        wsRef.current.onclose = null // prevent reconnect on cleanup
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])

  return { connected, reconnecting, send, subscribe }
}
