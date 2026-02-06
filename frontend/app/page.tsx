'use client'

import { useEffect, useState } from 'react'
import RoomGrid from '@/components/dashboard/RoomGrid'
import LiveIndicator from '@/components/shared/LiveIndicator'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useRooms, Room } from '@/hooks/useRooms'

export default function Dashboard() {
  const { rooms, loading, error, refetch } = useRooms()
  const [liveRooms, setLiveRooms] = useState<Room[]>([])

  // WebSocket for real-time updates
  const { lastMessage, isConnected } = useWebSocket('/ws/dashboard')

  useEffect(() => {
    if (rooms) {
      setLiveRooms(rooms)
    }
  }, [rooms])

  useEffect(() => {
    if (lastMessage?.type === 'count_update' && lastMessage.room_id) {
      setLiveRooms(prev => prev.map(room =>
        room.id === lastMessage.room_id
          ? {
              ...room,
              count: lastMessage.count ?? room.count,
              raw_count: lastMessage.raw_count ?? room.raw_count,
              occupancy_percent: lastMessage.occupancy_percent ?? room.occupancy_percent,
              status: (lastMessage.status as Room['status']) ?? room.status,
              last_updated: lastMessage.timestamp ?? room.last_updated,
            }
          : room
      ))
    }
  }, [lastMessage])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-600 dark:text-red-400">Ошибка загрузки: {error}</p>
        <button
          onClick={refetch}
          className="mt-2 text-sm text-red-600 dark:text-red-400 underline"
        >
          Попробовать снова
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Обзор залов
        </h1>
        <LiveIndicator isConnected={isConnected} />
      </div>

      {liveRooms.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            Нет настроенных залов
          </p>
          <a
            href="/settings/rooms"
            className="mt-2 inline-block text-blue-500 hover:text-blue-600"
          >
            Добавить зал
          </a>
        </div>
      ) : (
        <RoomGrid rooms={liveRooms} />
      )}

      {liveRooms.length > 0 && liveRooms[0].last_updated && (
        <p className="text-sm text-gray-400 mt-4 text-center">
          Обновлено: {new Date(liveRooms[0].last_updated).toLocaleTimeString('ru-RU')}
        </p>
      )}
    </div>
  )
}
