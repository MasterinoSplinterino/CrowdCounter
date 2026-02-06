'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, Plus, Pencil, Trash2 } from 'lucide-react'
import { useRooms } from '@/hooks/useRooms'
import RoomForm from '@/components/settings/RoomForm'
import { api, CreateRoomData, UpdateRoomData } from '@/lib/api'

export default function RoomsSettingsPage() {
  const { rooms, loading, refetch } = useRooms()
  const [showForm, setShowForm] = useState(false)
  const [editingRoom, setEditingRoom] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)

  const handleCreate = async (data: CreateRoomData) => {
    await api.createRoom(data)
    setShowForm(false)
    refetch()
  }

  const handleUpdate = async (id: string, data: UpdateRoomData) => {
    await api.updateRoom(id, data)
    setEditingRoom(null)
    refetch()
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить зал и всю его историю?')) return
    setDeleting(id)
    try {
      await api.deleteRoom(id)
      refetch()
    } finally {
      setDeleting(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Link
            href="/settings"
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Управление залами
          </h1>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Добавить зал</span>
        </button>
      </div>

      {showForm && (
        <div className="mb-6">
          <RoomForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      <div className="space-y-4">
        {rooms.map(room => (
          <div
            key={room.id}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4"
          >
            {editingRoom === room.id ? (
              <RoomForm
                room={room}
                onSubmit={(data) => handleUpdate(room.id, data)}
                onCancel={() => setEditingRoom(null)}
              />
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {room.name}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    ID: {room.id} | Вместимость: {room.capacity} | Камера: {room.camera_url.split('@')[1]?.split(':')[0] || 'webcam'}
                  </p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span
                      className={`inline-block w-2 h-2 rounded-full ${
                        room.is_active ? 'bg-green-500' : 'bg-gray-400'
                      }`}
                    />
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {room.is_active ? 'Активен' : 'Неактивен'}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setEditingRoom(room.id)}
                    className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(room.id)}
                    disabled={deleting === room.id}
                    className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {rooms.length === 0 && !showForm && (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            Нет настроенных залов
          </div>
        )}
      </div>
    </div>
  )
}
