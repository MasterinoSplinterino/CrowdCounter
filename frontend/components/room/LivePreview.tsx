'use client'

import { useEffect, useState } from 'react'
import { Camera, CameraOff } from 'lucide-react'
import { api } from '@/lib/api'

interface LivePreviewProps {
  frame?: string
  roomId: string
}

export default function LivePreview({ frame, roomId }: LivePreviewProps) {
  const [staticFrame, setStaticFrame] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!frame && !staticFrame) {
      setLoading(true)
      api.getPreview(roomId)
        .then(data => setStaticFrame(data.frame))
        .catch(() => {})
        .finally(() => setLoading(false))
    }
  }, [frame, roomId, staticFrame])

  const displayFrame = frame || staticFrame

  if (loading) {
    return (
      <div className="aspect-video bg-gray-100 dark:bg-gray-900 rounded-lg flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    )
  }

  if (!displayFrame) {
    return (
      <div className="aspect-video bg-gray-100 dark:bg-gray-900 rounded-lg flex flex-col items-center justify-center text-gray-400">
        <CameraOff className="w-12 h-12 mb-2" />
        <p className="text-sm">Нет изображения</p>
      </div>
    )
  }

  return (
    <div className="relative aspect-video bg-gray-100 dark:bg-gray-900 rounded-lg overflow-hidden">
      <img
        src={displayFrame}
        alt="Live camera feed"
        className="w-full h-full object-contain"
      />
      <div className="absolute top-2 right-2 flex items-center space-x-1 bg-black/50 text-white text-xs px-2 py-1 rounded">
        <Camera className="w-3 h-3" />
        <span>LIVE</span>
      </div>
    </div>
  )
}
