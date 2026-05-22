'use client'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export type MetricSeries = {
  name: string
  booked?: number
  upcoming?: number
  completed?: number
  missed?: number
  value?: number
  leads?: number
  tasks?: number
  revenue?: number
  reviews?: number
}

const COLORS = {
  booked: '#20ccce',
  upcoming: '#3b82f6',
  completed: '#10b981',
  missed: '#f59e0b',
  value: '#8b5cf6',
  leads: '#20ccce',
  tasks: '#6366f1',
  revenue: '#10b981',
  reviews: '#fbbf24',
}

export function ModuleMetricCharts({
  title,
  subtitle,
  data,
  seriesKeys,
}: {
  title: string
  subtitle?: string
  data: MetricSeries[]
  seriesKeys: Array<keyof MetricSeries>
}) {
  const keys = seriesKeys.filter((k) => k !== 'name')

  return (
    <section className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-5 shadow-sm">
      <div className="mb-4">
        <h2 className="text-sm font-bold text-white">{title}</h2>
        {subtitle ? <p className="text-xs text-brand-teal-100/65 mt-0.5">{subtitle}</p> : null}
      </div>
      <div className="h-56 sm:h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#025422" opacity={0.35} />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#a7f3d0' }} />
            <YAxis tick={{ fontSize: 11, fill: '#a7f3d0' }} allowDecimals={false} />
            <Tooltip
              contentStyle={{
                background: '#025422',
                border: '1px solid #20ccce33',
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {keys.map((key) => (
              <Bar
                key={String(key)}
                dataKey={String(key)}
                fill={COLORS[key as keyof typeof COLORS] ?? '#20ccce'}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
