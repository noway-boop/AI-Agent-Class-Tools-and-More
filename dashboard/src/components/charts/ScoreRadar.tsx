import {
  ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Tooltip,
} from 'recharts'
import type { HealthScore } from '@/types'

interface ScoreRadarProps {
  healthScore: HealthScore
}

const COMPONENT_LABELS: Record<string, string> = {
  sentiment: 'Sentiment',
  financial: 'Financial',
  operational: 'Operations',
  volume: 'Volume',
  competitive: 'Competitive',
}

export function ScoreRadar({ healthScore }: ScoreRadarProps) {
  const data = Object.entries(healthScore.components).map(([key, comp]) => ({
    metric: COMPONENT_LABELS[key] ?? key,
    value: comp.value,
    fullMark: 100,
  }))

  return (
    <div className="w-full">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1 text-center">
        Score Breakdown
      </h4>
      <ResponsiveContainer width="100%" height={200}>
        <RadarChart data={data} margin={{ top: 8, right: 24, bottom: 8, left: 24 }}>
          <PolarGrid stroke="rgba(255,255,255,0.1)" />
          <PolarAngleAxis
            dataKey="metric"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              background: '#1E2D3D',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              fontSize: '11px',
              color: '#fff',
            }}
          />
          <Radar
            name="Score"
            dataKey="value"
            stroke="#006EBA"
            fill="#006EBA"
            fillOpacity={0.25}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
