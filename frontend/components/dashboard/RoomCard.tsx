import Link from 'next/link'
import StatusBadge from './StatusBadge'
import type { Room } from '@/hooks/useRooms'

interface RoomCardProps {
  room: Room
}

export default function RoomCard({ room }: RoomCardProps) {
  const percentage = room.occupancy_percent

  return (
    <Link href={`/rooms/${room.id}`}>
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900 dark:text-white truncate">
            {room.name}
          </h3>
          {!room.is_active && (
            <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 px-2 py-0.5 rounded">
              Неактивен
            </span>
          )}
        </div>

        <div className="text-center mb-4">
          <span className="text-4xl font-bold text-gray-900 dark:text-white">
            {room.count}
          </span>
          <span className="text-lg text-gray-400 dark:text-gray-500">
            {' / '}{room.capacity}
          </span>
        </div>

        {/* Progress bar */}
        <div className="mb-3">
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${getProgressColor(room.status)}`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-lg font-medium text-gray-700 dark:text-gray-300">
            {percentage.toFixed(0)}%
          </span>
          <StatusBadge status={room.status} />
        </div>
      </div>
    </Link>
  )
}

function getProgressColor(status: string): string {
  switch (status) {
    case 'empty': return 'bg-gray-400'
    case 'low': return 'bg-green-500'
    case 'medium': return 'bg-yellow-500'
    case 'high': return 'bg-orange-500'
    case 'full': return 'bg-red-500'
    default: return 'bg-gray-400'
  }
}
