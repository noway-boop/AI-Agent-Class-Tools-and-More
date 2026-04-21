import { Activity, Bell, TrendingUp, Zap } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import type { DashboardSnapshot } from '@/types'

interface OverviewStatsProps {
  snapshot: DashboardSnapshot
}

export function OverviewStats({ snapshot }: OverviewStatsProps) {
  const avgScore = Object.values(snapshot.entities).reduce(
    (sum, e) => sum + (e.health_score?.overall_score ?? 0), 0,
  ) / Math.max(Object.keys(snapshot.entities).length, 1)

  const stats = [
    {
      label: 'Avg Health Score',
      value: avgScore.toFixed(1),
      sub: `across ${Object.keys(snapshot.entities).length} entities`,
      icon: Activity,
      color: avgScore >= 70 ? 'text-emerald-400' : avgScore >= 50 ? 'text-yellow-400' : 'text-red-400',
    },
    {
      label: 'Signals Analyzed',
      value: snapshot.total_signals.toLocaleString(),
      sub: 'last 24 hours',
      icon: TrendingUp,
      color: 'text-disney-blue',
    },
    {
      label: 'Active Alerts',
      value: String(snapshot.total_alerts),
      sub: `${snapshot.critical_alerts} critical`,
      icon: Bell,
      color: snapshot.critical_alerts > 0 ? 'text-red-400' : 'text-slate-400',
    },
    {
      label: 'Critical Issues',
      value: String(snapshot.critical_alerts),
      sub: 'require attention',
      icon: Zap,
      color: snapshot.critical_alerts > 0 ? 'text-red-400' : 'text-emerald-400',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map(({ label, value, sub, icon: Icon, color }) => (
        <Card key={label}>
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-slate-500 mb-1">{label}</p>
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-slate-600 mt-0.5">{sub}</p>
            </div>
            <Icon size={16} className={`${color} opacity-60`} />
          </div>
        </Card>
      ))}
    </div>
  )
}
