import { ExternalLink } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { sourceIcon, formatRelativeTime, urgencyBadge } from '@/lib/utils'
import type { Signal } from '@/types'

interface SignalFeedProps {
  signals: Signal[]
  maxVisible?: number
}

const SOURCE_LABELS: Record<string, string> = {
  newsapi: 'NewsAPI',
  google_news_rss: 'Google News',
  sec_edgar: 'SEC EDGAR',
  reddit: 'Reddit',
  youtube: 'YouTube',
  twitter: 'Twitter/X',
  disney_parks_blog: 'Disney Blog',
  queue_times: 'Park API',
}

export function SignalFeed({ signals, maxVisible = 25 }: SignalFeedProps) {
  const visible = signals.slice(0, maxVisible)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Signal Feed</CardTitle>
        <span className="text-xs text-slate-500">{signals.length} signals</span>
      </CardHeader>

      <div className="space-y-2 max-h-96 overflow-y-auto pr-1 scrollbar-thin">
        {visible.length === 0 && (
          <p className="text-xs text-slate-500 text-center py-6">No signals loaded</p>
        )}

        {visible.map(signal => (
          <div key={signal.id} className="group flex gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors">
            <span className="text-base flex-shrink-0 mt-0.5">
              {sourceIcon(signal.source_type)}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-white leading-snug line-clamp-2 mb-1">
                {signal.title}
              </p>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-600">
                  {SOURCE_LABELS[signal.source_name] ?? signal.source_name}
                </span>
                <span className="text-slate-700">·</span>
                <span className="text-xs text-slate-600">
                  {formatRelativeTime(signal.published_at)}
                </span>
              </div>
            </div>
            {signal.source_url && (
              <a
                href={signal.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-disney-blue transition-all flex-shrink-0 mt-0.5"
                onClick={e => e.stopPropagation()}
              >
                <ExternalLink size={11} />
              </a>
            )}
          </div>
        ))}
      </div>
    </Card>
  )
}
