'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Save } from 'lucide-react'
import { api, ApiSettings, ApiStatus } from '@/lib/api'

export default function DetectionSettingsPage() {
  const [settings, setSettings] = useState<ApiSettings | null>(null)
  const [status, setStatus] = useState<ApiStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([api.getSettings(), api.getStatus()])
      .then(([settingsData, statusData]) => {
        setSettings(settingsData)
        setStatus(statusData)
      })
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    if (!settings) return
    setSaving(true)
    try {
      await api.updateSettings(settings)
      const newStatus = await api.getStatus()
      setStatus(newStatus)
    } finally {
      setSaving(false)
    }
  }

  if (loading || !settings) {
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
            Параметры детекции
          </h1>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Сохранение...' : 'Применить изменения'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Модель YOLO
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Модель
              </label>
              <select
                value={settings.model}
                onChange={(e) => setSettings({ ...settings, model: e.target.value })}
                className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="yolo11n.pt">yolo11n.pt (nano, быстрая)</option>
                <option value="yolo11s.pt">yolo11s.pt (small, точнее)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Detection Parameters */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Параметры детекции
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Уверенность (confidence): {settings.confidence_threshold}
              </label>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={settings.confidence_threshold}
                onChange={(e) => setSettings({ ...settings, confidence_threshold: parseFloat(e.target.value) })}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Интервал (сек): {settings.detection_interval}
              </label>
              <input
                type="range"
                min="1"
                max="60"
                step="1"
                value={settings.detection_interval}
                onChange={(e) => setSettings({ ...settings, detection_interval: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Сглаживание (alpha): {settings.smoothing_alpha}
              </label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={settings.smoothing_alpha}
                onChange={(e) => setSettings({ ...settings, smoothing_alpha: parseFloat(e.target.value) })}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Размер кадра (imgsz)
              </label>
              <select
                value={settings.imgsz}
                onChange={(e) => setSettings({ ...settings, imgsz: parseInt(e.target.value) })}
                className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="480">480</option>
                <option value="640">640</option>
                <option value="1280">1280</option>
              </select>
            </div>
          </div>
        </div>

        {/* System Status */}
        {status && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 lg:col-span-2">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Статус системы
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Device</p>
                <p className="font-medium text-gray-900 dark:text-white">{status.device}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Модель</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {status.model} {status.model_loaded ? '✓' : '✗'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Камеры</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {status.cameras_connected} / {status.cameras_total}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Uptime</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {formatUptime(status.uptime_seconds)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Avg Inference</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {status.avg_inference_ms.toFixed(1)} ms
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function formatUptime(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}ч ${minutes}мин`
  }
  return `${minutes}мин`
}
