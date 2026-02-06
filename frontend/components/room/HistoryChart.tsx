'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { ApiCount } from '@/lib/api'

interface HistoryChartProps {
  data: ApiCount[]
  capacity: number
}

export default function HistoryChart({ data, capacity }: HistoryChartProps) {
  if (data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-400">
        Нет данных за сегодня
      </div>
    )
  }

  const chartData = data.map(item => ({
    time: new Date(item.timestamp).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
    }),
    count: item.count,
    raw: item.raw_count,
  }))

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12 }}
            className="fill-gray-500"
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[0, Math.max(capacity, Math.max(...chartData.map(d => d.count)) + 10)]}
            tick={{ fontSize: 12 }}
            className="fill-gray-500"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            labelStyle={{ fontWeight: 'bold' }}
          />
          <ReferenceLine
            y={capacity}
            label={{ value: 'Вместимость', position: 'right', fontSize: 10 }}
            stroke="#EF4444"
            strokeDasharray="5 5"
          />
          <Line
            type="monotone"
            dataKey="count"
            name="Людей"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
