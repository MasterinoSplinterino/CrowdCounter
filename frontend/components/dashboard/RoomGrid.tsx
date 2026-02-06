import RoomCard from './RoomCard'
import type { Room } from '@/hooks/useRooms'

interface RoomGridProps {
  rooms: Room[]
}

export default function RoomGrid({ rooms }: RoomGridProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {rooms.map(room => (
        <RoomCard key={room.id} room={room} />
      ))}
    </div>
  )
}
