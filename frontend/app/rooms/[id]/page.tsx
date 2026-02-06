'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { useRoom } from '@/hooks/useRooms'
import { useWebSocket } from '@/hooks/useWebSocket'
import LiveIndicator from '@/components/shared/LiveIndicator'
import StatusBadge from '@/components/dashboard/StatusBadge'
import LivePreview from '@/components/room/LivePreview'
import HistoryChart from '@/components/room/HistoryChart'
import OccupancyGauge from '@/components/room/OccupancyGauge'
import { api, ApiCount } from '@/lib/api'

export default function RoomPage() {
  const params = useParams()
  const roomId = params.id as string
  const { room, loading, error } = useRoom(roomId)
  const { lastMessage, isConnected } = useWebSocket(`/ws/room/${roomId}`)

  const [liveData, setLiveData] = useState<{
    count: number
    raw_count: number
    occupancy_percent: number
    status: string
    frame?: string
  } | null>(null)

  const [history, setHistory] = useState<ApiCount[]>([])

  useEffect(() => {
    if (room) {
      setLiveData({
        count: room.count,
        raw_count: room.raw_count,
        occupancy_percent: room.occupancy_percent,
        status: room.status,
      })
    }
  }, [room])

  useEffect(() => {
    if (lastMessage?.room_id === roomId) {
      setLiveData({
        count: lastMessage.count!,
        raw_count: lastMessage.raw_count!,
        occupancy_percent: lastMessage.occupancy_percent!,
        status: lastMessage.status!,
        frame: lastMessage.frame,
      })
    }
  }, [lastMessage, roomId])

  useEffect(() => {
    api.getHistory(roomId, 10).then(setHistory).catch(console.error)
  }, [roomId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    )
  }

  if (error || !room) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-600 dark:text-red-400">
          {error || 'Зал не найден'}
        </p>
        <Link href="/" className="mt-2 text-sm text-red-600 dark:text-red-400 underline">
          Вернуться на главную
        </Link>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Link
            href="/"
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {room.name}
          </h1>
        </div>
        <LiveIndicator isConnected={isConnected} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Live Preview */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Live Preview
          </h2>
          <LivePreview frame={liveData?.frame} roomId={roomId} />
        </div>

        {/* Current Stats */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Сейчас
          </h2>
          <div className="flex flex-col items-center">
            <OccupancyGauge
              percent={liveData?.occupancy_percent || 0}
              count={liveData?.count || 0}
              capacity={room.capacity}
            />
            <div className="mt-4">
              <StatusBadge status={(liveData?.status || 'empty') as any} />
            </div>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              Камера: {room.camera_url.split('@')[1]?.split(':')[0] || room.camera_url}
            </p>
          </div>
        </div>
      </div>

      {/* History Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Загруженность за сегодня
        </h2>
        <HistoryChart data={history} capacity={room.capacity} />
      </div>
    </div>
  )
}
