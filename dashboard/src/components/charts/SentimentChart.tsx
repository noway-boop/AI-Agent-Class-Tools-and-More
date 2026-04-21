import {
  ResponsiveContainer, ComposedChart, Area, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Legend,
} from 'recharts'
import type { SentimentDataPoint } from '@/types'

interface SentimentChartProps {
  data: SentimentDataPoint[]
  entityName: string
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  const polarity = payload.find((p: any) => p.dataKey === 'polarity')
  const volume = payload.find((p: any) => p.dataKey === 'volume')
  return (
    <div className="bg-disney-slate border border-white/20 rounded-lg p-3 text-xs shadow-xl">
      <p className="text-slate-400 mb-1 font-medium">{label}</p>
      {polarity && (
        <p className={`font-semibold ${polarity.value >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          Sentiment: {Number(polarity.value).toFixed(3)}
        </p>
      )}
      {volume && (
        <p className="text-slate-400">Volume: {volume.value} signals</p>
      )}
    </div>
  )
}

export function SentimentChart({ data, entityName }: SentimentChartProps) {
  return (
    <div className="w-full">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">
        Sentiment & Volume — {entityName}
      </h4>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey="time"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            interval={2}
          />
          <YAxis
            yAxisId="polarity"
            domain={[-1, 1]}
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            tickCount={5}
          />
          <YAxis
            yAxisId="volume"
            orientation="right"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine yAxisId="polarity" y={0} stroke="rgba(255,255,255,0.15)" />
          <Bar
            yAxisId="volume"
            dataKey="volume"
            fill="rgba(0,110,186,0.25)"
            radius={[2, 2, 0, 0]}
            name="Volume"
          />
          <Area
            yAxisId="polarity"
            type="monotone"
            dataKey="polarity"
            stroke="#006EBA"
            strokeWidth={2}
            fill="url(#sentimentGrad)"
            name="Sentiment"
          />
          <defs>
            <linearGradient id="sentimentGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#006EBA" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#006EBA" stopOpacity={0.05} />
            </linearGradient>
          </defs>
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
