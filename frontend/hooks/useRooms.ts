'use client'

import { useState, useEffect, useCallback } from 'react'
import { api, ApiRoom } from '@/lib/api'

export type Room = ApiRoom

export function useRooms() {
  const [rooms, setRooms] = useState<Room[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRooms = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getRooms()
      setRooms(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRooms()
  }, [fetchRooms])

  return {
    rooms,
    loading,
    error,
    refetch: fetchRooms,
  }
}

export function useRoom(id: string) {
  const [room, setRoom] = useState<Room | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRoom = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getRoom(id)
      setRoom(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchRoom()
  }, [fetchRoom])

  return {
    room,
    loading,
    error,
    refetch: fetchRoom,
  }
}
