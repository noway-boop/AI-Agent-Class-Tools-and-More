import { X, TrendingUp, TrendingDown, Minus, AlertTriangle, Star } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { ScoreBar } from '@/components/ui/ScoreBar'
import { SentimentChart } from '@/components/charts/SentimentChart'
import { ScoreRadar } from '@/components/charts/ScoreRadar'
import { Badge } from '@/components/ui/Badge'
import {
  scoreColor, formatScore, trendIcon, trendColor,
  severityBadge, formatRelativeTime, polarityColor,
} from '@/lib/utils'
import type { EntityAnalytics, SentimentDataPoint } from '@/types'

interface EntityDetailProps {
  analytics: EntityAnalytics
  sentimentSeries: SentimentDataPoint[]
  onClose: () => void
}

const COMPONENT_LABELS: Record<string, string> = {
  sentiment: 'Sentiment',
  financial: 'Financial',
  operational: 'Operations',
  volume: 'Signal Volume',
  competitive: 'Competitive',
}

const COMPONENT_WEIGHTS: Record<string, string> = {
  sentiment: '30%',
  financial: '25%',
  operational: '20%',
  volume: '15%',
  competitive: '10%',
}

export function EntityDetail({ analytics, sentimentSeries, onClose }: EntityDetailProps) {
  const { health_score, sentiment_trend, alerts, scorecard } = analytics
  if (!health_score) return null

  const unreadAlerts = alerts.filter(a => !a.is_read)

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">{analytics.entity_name}</h2>
          <div className="flex items-center gap-3 mt-1">
            <span className={`text-3xl font-bold ${scoreColor(health_score.overall_score)}`}>
              {formatScore(health_score.overall_score)}
            </span>
            <span className="text-slate-500 text-sm">/100</span>
            {sentiment_trend && (
              <span className={`text-sm font-medium ${trendColor(sentiment_trend.direction)}`}>
                {trendIcon(sentiment_trend.direction)} {sentiment_trend.direction}
              </span>
            )}
          </div>
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors p-1">
          <X size={18} />
        </button>
      </div>

      {/* Key metrics row */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="text-center py-3">
          <p className="text-xs text-slate-500 mb-1">Sentiment</p>
          <p className={`text-lg font-bold ${polarityColor(scorecard?.sentiment_avg ?? 0)}`}>
            {((scorecard?.sentiment_avg ?? 0) >= 0 ? '+' : '')}{(scorecard?.sentiment_avg ?? 0).toFixed(3)}
          </p>
        </Card>
        <Card className="text-center py-3">
          <p className="text-xs text-slate-500 mb-1">Signals</p>
          <p className="text-lg font-bold text-white">{analytics.signal_count.toLocaleString()}</p>
        </Card>
        <Card className="text-center py-3">
          <p className="text-xs text-slate-500 mb-1">Alerts</p>
          <p className={`text-lg font-bold ${unreadAlerts.length > 0 ? 'text-yellow-400' : 'text-slate-400'}`}>
            {unreadAlerts.length}
          </p>
        </Card>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <SentimentChart data={sentimentSeries} entityName={analytics.entity_name} />
        </Card>
        <Card>
          <ScoreRadar healthScore={health_score} />
        </Card>
      </div>

      {/* Component breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Score Components</CardTitle>
        </CardHeader>
        <div className="space-y-3">
          {Object.entries(health_score.components).map(([key, comp]) => (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-300 font-medium">
                  {COMPONENT_LABELS[key] ?? key}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-600">{COMPONENT_WEIGHTS[key]}</span>
                  <span className={`text-xs font-bold ${scoreColor(comp.value)}`}>
                    {comp.value.toFixed(0)}
                  </span>
                </div>
              </div>
              <ScoreBar value={comp.value} size="sm" />
              <div className="flex flex-wrap gap-1 mt-1">
                {comp.contributing_factors.slice(0, 2).map((f, i) => (
                  <span key={i} className="text-xs text-slate-600">{f}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Risks & Opportunities */}
      {(health_score.risk_flags.length > 0 || health_score.opportunities.length > 0) && (
        <div className="grid grid-cols-2 gap-4">
          {health_score.risk_flags.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-red-400">Risk Flags</CardTitle>
              </CardHeader>
              <ul className="space-y-1.5">
                {health_score.risk_flags.map((flag, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-slate-300">
                    <AlertTriangle size={10} className="text-red-400 flex-shrink-0 mt-0.5" />
                    {flag}
                  </li>
                ))}
              </ul>
            </Card>
          )}
          {health_score.opportunities.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-emerald-400">Opportunities</CardTitle>
              </CardHeader>
              <ul className="space-y-1.5">
                {health_score.opportunities.map((opp, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-slate-300">
                    <Star size={10} className="text-emerald-400 flex-shrink-0 mt-0.5" />
                    {opp}
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}

      {/* Recent alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
          </CardHeader>
          <div className="space-y-2">
            {alerts.slice(0, 5).map(alert => (
              <div key={alert.id} className={`flex items-start gap-2 text-xs p-2 rounded-lg border ${severityBadge(alert.severity)}`}>
                <AlertTriangle size={10} className="flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium">{alert.headline}</p>
                  <p className="opacity-70 mt-0.5">{formatRelativeTime(alert.created_at)}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
