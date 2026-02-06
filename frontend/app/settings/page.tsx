'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Building, Cog } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Настройки
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link href="/settings/rooms">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Building className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Залы
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Управление залами и камерами
                </p>
              </div>
            </div>
          </div>
        </Link>

        <Link href="/settings/detection">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Cog className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Детекция
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Параметры обработки видео
                </p>
              </div>
            </div>
          </div>
        </Link>
      </div>
    </div>
  )
}
