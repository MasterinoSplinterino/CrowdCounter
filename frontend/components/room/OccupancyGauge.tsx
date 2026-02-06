interface OccupancyGaugeProps {
  percent: number
  count: number
  capacity: number
}

export default function OccupancyGauge({ percent, count, capacity }: OccupancyGaugeProps) {
  const radius = 80
  const strokeWidth = 12
  const normalizedRadius = radius - strokeWidth / 2
  const circumference = normalizedRadius * 2 * Math.PI
  const strokeDashoffset = circumference - (percent / 100) * circumference

  const getColor = (p: number) => {
    if (p === 0) return '#9CA3AF'
    if (p < 40) return '#22C55E'
    if (p < 70) return '#EAB308'
    if (p < 90) return '#F97316'
    return '#EF4444'
  }

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg height={radius * 2} width={radius * 2}>
        {/* Background circle */}
        <circle
          stroke="#E5E7EB"
          fill="transparent"
          strokeWidth={strokeWidth}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          className="dark:stroke-gray-700"
        />
        {/* Progress circle */}
        <circle
          stroke={getColor(percent)}
          fill="transparent"
          strokeWidth={strokeWidth}
          strokeDasharray={`${circumference} ${circumference}`}
          style={{
            strokeDashoffset,
            transform: 'rotate(-90deg)',
            transformOrigin: '50% 50%',
            transition: 'stroke-dashoffset 0.5s ease-in-out',
          }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-bold text-gray-900 dark:text-white">
          {count}
        </span>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          / {capacity}
        </span>
        <span className="text-lg font-semibold" style={{ color: getColor(percent) }}>
          {percent.toFixed(1)}%
        </span>
      </div>
    </div>
  )
}
