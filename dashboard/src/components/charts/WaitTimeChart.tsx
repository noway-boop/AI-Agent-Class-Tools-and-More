import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
} from 'recharts'
import type { WaitTimeDataPoint } from '@/types'

interface WaitTimeChartProps {
  data: WaitTimeDataPoint[]
}

const PARK_COLORS: Record<string, string> = {
  'Magic Kingdom': '#006EBA',
  'EPCOT': '#C8A951',
  'Hollywood Studios': '#E84545',
  'Animal Kingdom': '#4CAF76',
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-disney-slate border border-white/20 rounded-lg p-3 text-xs shadow-xl">
      <p className="text-slate-400 mb-2 font-medium">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.stroke }} className="font-medium">
          {p.name}: {p.value} min
        </p>
      ))}
    </div>
  )
}

export function WaitTimeChart({ data }: WaitTimeChartProps) {
  const parks = [...new Set(data.map(d => d.park))]

  const byTime: Record<string, Record<string, number>> = {}
  data.forEach(d => {
    if (!byTime[d.time]) byTime[d.time] = {}
    byTime[d.time][d.park] = d.avg_wait
  })

  const chartData = Object.entries(byTime).map(([time, parks]) => ({ time, ...parks }))

  return (
    <div className="w-full">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">
        Park Wait Times (avg minutes)
      </h4>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey="time"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            interval={2}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            unit=" min"
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconSize={8}
            wrapperStyle={{ fontSize: '10px', color: '#94a3b8' }}
          />
          {parks.map(park => (
            <Line
              key={park}
              type="monotone"
              dataKey={park}
              stroke={PARK_COLORS[park] ?? '#888'}
              strokeWidth={2}
              dot={false}
              name={park}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
