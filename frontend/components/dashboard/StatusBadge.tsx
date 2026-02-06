type Status = 'empty' | 'low' | 'medium' | 'high' | 'full'

interface StatusBadgeProps {
  status: Status
}

const statusConfig: Record<Status, { color: string; label: string }> = {
  empty: { color: 'bg-gray-400', label: 'Пусто' },
  low: { color: 'bg-green-500', label: 'Свободно' },
  medium: { color: 'bg-yellow-500', label: 'Умеренно' },
  high: { color: 'bg-orange-500', label: 'Заполняется' },
  full: { color: 'bg-red-500', label: 'Почти полный' },
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.empty

  return (
    <div className="flex items-center space-x-1.5">
      <span className={`inline-block w-2.5 h-2.5 rounded-full ${config.color}`} />
      <span className="text-sm text-gray-600 dark:text-gray-300">
        {config.label}
      </span>
    </div>
  )
}
