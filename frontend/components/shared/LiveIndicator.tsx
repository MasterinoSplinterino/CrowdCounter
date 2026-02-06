interface LiveIndicatorProps {
  isConnected: boolean
}

export default function LiveIndicator({ isConnected }: LiveIndicatorProps) {
  return (
    <div className="flex items-center space-x-2">
      <span
        className={`inline-block w-2.5 h-2.5 rounded-full ${
          isConnected
            ? 'bg-green-500 animate-pulse'
            : 'bg-gray-400'
        }`}
      />
      <span
        className={`text-sm font-medium ${
          isConnected
            ? 'text-green-600 dark:text-green-400'
            : 'text-gray-500 dark:text-gray-400'
        }`}
      >
        {isConnected ? 'LIVE' : 'OFFLINE'}
      </span>
    </div>
  )
}
