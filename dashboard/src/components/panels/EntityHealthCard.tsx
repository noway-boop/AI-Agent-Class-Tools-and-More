import { Card } from '@/components/ui/Card'
import { ScoreBar } from '@/components/ui/ScoreBar'
import { Badge } from '@/components/ui/Badge'
import { trendIcon, trendColor, scoreColor, formatScore, severityBadge } from '@/lib/utils'
import type { EntityAnalytics } from '@/types'
import { AlertTriangle, Zap } from 'lucide-react'

interface EntityHealthCardProps {
  analytics: EntityAnalytics
  selected: boolean
  onClick: () => void
}

const COMPONENT_ORDER = ['sentiment', 'financial', 'operational', 'volume', 'competitive']

export function EntityHealthCard({ analytics, selected, onClick }: EntityHealthCardProps) {
  const { health_score, sentiment_trend, alerts } = analytics
  if (!health_score) return null

  const unreadCritical = alerts.filter(a => !a.is_read && a.severity === 'critical').length
  const unreadWarning = alerts.filter(a => !a.is_read && a.severity === 'warning').length

  return (
    <Card
      onClick={onClick}
      className={selected ? 'border-disney-blue ring-1 ring-disney-blue/30' : ''}
    >
      {/* Entity name + overall score */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white truncate pr-2">
            {analytics.entity_name}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {analytics.signal_count.toLocaleString()} signals
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <span className={`text-2xl font-bold ${scoreColor(health_score.overall_score)}`}>
            {formatScore(health_score.overall_score)}
          </span>
          {sentiment_trend && (
            <p className={`text-xs font-medium ${trendColor(sentiment_trend.direction)}`}>
              {trendIcon(sentiment_trend.direction)} {sentiment_trend.direction}
            </p>
          )}
        </div>
      </div>

      {/* Overall score bar */}
      <ScoreBar value={health_score.overall_score} size="md" className="mb-4" />

      {/* Component breakdown */}
      <div className="space-y-2 mb-3">
        {COMPONENT_ORDER.map(key => {
          const comp = health_score.components[key]
          if (!comp) return null
          return (
            <div key={key} className="flex items-center gap-2">
              <span className="text-xs text-slate-500 w-20 capitalize flex-shrink-0">{key}</span>
              <ScoreBar value={comp.value} size="sm" className="flex-1" />
              <span className="text-xs text-slate-400 w-7 text-right flex-shrink-0">
                {comp.value.toFixed(0)}
              </span>
            </div>
          )
        })}
      </div>

      {/* Alert badges */}
      {(unreadCritical > 0 || unreadWarning > 0) && (
        <div className="flex gap-2 pt-2 border-t border-white/10">
          {unreadCritical > 0 && (
            <div className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded border ${severityBadge('critical')}`}>
              <AlertTriangle size={10} />
              {unreadCritical} critical
            </div>
          )}
          {unreadWarning > 0 && (
            <div className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded border ${severityBadge('warning')}`}>
              <Zap size={10} />
              {unreadWarning} warning
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
