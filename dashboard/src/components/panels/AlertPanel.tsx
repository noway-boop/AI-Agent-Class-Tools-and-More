import { AlertTriangle, Info, Zap, CheckCheck, ExternalLink } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { severityBadge, formatRelativeTime } from '@/lib/utils'
import type { Alert, AlertType } from '@/types'

const ALERT_TYPE_LABELS: Record<AlertType, string> = {
  sentiment_spike: 'Sentiment',
  volume_anomaly: 'Volume',
  filing_detected: 'SEC Filing',
  competitor_move: 'Competitor',
  earnings_surprise: 'Earnings',
  trend_reversal: 'Trend',
}

const SeverityIcon = ({ severity }: { severity: Alert['severity'] }) => {
  if (severity === 'critical') return <AlertTriangle size={12} className="text-red-400 flex-shrink-0" />
  if (severity === 'warning') return <Zap size={12} className="text-yellow-400 flex-shrink-0" />
  return <Info size={12} className="text-blue-400 flex-shrink-0" />
}

interface AlertPanelProps {
  alerts: Alert[]
  onMarkRead: (id: string) => void
  onMarkAllRead: () => void
  maxVisible?: number
}

export function AlertPanel({ alerts, onMarkRead, onMarkAllRead, maxVisible = 20 }: AlertPanelProps) {
  const unread = alerts.filter(a => !a.is_read)
  const sorted = [...alerts].sort((a, b) => {
    const sevOrder = { critical: 0, warning: 1, info: 2 }
    if (sevOrder[a.severity] !== sevOrder[b.severity])
      return sevOrder[a.severity] - sevOrder[b.severity]
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
  const visible = sorted.slice(0, maxVisible)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle>Active Alerts</CardTitle>
          {unread.length > 0 && (
            <span className="bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5 font-medium">
              {unread.length}
            </span>
          )}
        </div>
        {unread.length > 0 && (
          <button
            onClick={onMarkAllRead}
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            <CheckCheck size={12} />
            Mark all read
          </button>
        )}
      </CardHeader>

      <div className="space-y-2">
        {visible.length === 0 && (
          <p className="text-xs text-slate-500 text-center py-6">No active alerts</p>
        )}

        {visible.map(alert => (
          <div
            key={alert.id}
            className={`group rounded-lg p-3 border transition-all ${
              alert.is_read
                ? 'border-white/5 bg-white/2'
                : 'border-white/10 bg-white/5'
            }`}
          >
            <div className="flex items-start gap-2">
              <SeverityIcon severity={alert.severity} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <Badge className={severityBadge(alert.severity)}>
                    {alert.severity}
                  </Badge>
                  <Badge className="bg-slate-500/20 text-slate-300 border-slate-500/30">
                    {ALERT_TYPE_LABELS[alert.alert_type]}
                  </Badge>
                  <span className="text-xs text-slate-600 ml-auto">
                    {formatRelativeTime(alert.created_at)}
                  </span>
                </div>
                <p className={`text-xs font-medium leading-tight ${alert.is_read ? 'text-slate-400' : 'text-white'}`}>
                  {alert.headline}
                </p>
                {alert.summary && !alert.is_read && (
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed line-clamp-2">
                    {alert.summary}
                  </p>
                )}
              </div>
              {!alert.is_read && (
                <button
                  onClick={() => onMarkRead(alert.id)}
                  className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-slate-400 transition-all"
                >
                  <CheckCheck size={12} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
