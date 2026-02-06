'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '@/lib/api'

export interface WebSocketMessage {
  type: string
  room_id?: string
  count?: number
  raw_count?: number
  occupancy_percent?: number
  status?: string
  timestamp?: string
  frame?: string
}

// Using polling instead of WebSocket for internal network architecture
// WebSocket would require exposing backend externally or complex proxy setup
// Polling every 5 seconds is sufficient for dashboard updates

export function useWebSocket(path: string) {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const fetchUpdates = useCallback(async () => {
    try {
      // Dashboard - fetch all rooms
      if (path === '/ws/dashboard') {
        const rooms = await api.getRooms()
        if (rooms.length > 0) {
          // Emit update for each room
          rooms.forEach(room => {
            setLastMessage({
              type: 'count_update',
              room_id: room.id,
              count: room.count,
              raw_count: room.raw_count,
              occupancy_percent: room.occupancy_percent,
              status: room.status,
              timestamp: room.last_updated || new Date().toISOString(),
            })
          })
        }
        setIsConnected(true)
      }
      // Room specific - fetch room data + preview
      else if (path.startsWith('/ws/room/')) {
        const roomId = path.replace('/ws/room/', '')
        const room = await api.getRoom(roomId)

        let frame: string | undefined
        try {
          const preview = await api.getPreview(roomId)
          frame = preview.frame
        } catch {
          // Preview may not be available
        }

        setLastMessage({
          type: 'count_update',
          room_id: room.id,
          count: room.count,
          raw_count: room.raw_count,
          occupancy_percent: room.occupancy_percent,
          status: room.status,
          timestamp: room.last_updated || new Date().toISOString(),
          frame,
        })
        setIsConnected(true)
      }
    } catch (error) {
      console.error('Polling error:', error)
      setIsConnected(false)
    }
  }, [path])

  useEffect(() => {
    // Initial fetch
    fetchUpdates()

    // Poll every 5 seconds
    intervalRef.current = setInterval(fetchUpdates, 5000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [fetchUpdates])

  return {
    lastMessage,
    isConnected,
  }
}
