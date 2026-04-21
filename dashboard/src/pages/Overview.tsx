import { useState } from 'react'
import { EntityHealthCard } from '@/components/panels/EntityHealthCard'
import { AlertPanel } from '@/components/panels/AlertPanel'
import { SignalFeed } from '@/components/panels/SignalFeed'
import { EntityDetail } from '@/components/panels/EntityDetail'
import { OverviewStats } from '@/components/panels/OverviewStats'
import { WaitTimeChart } from '@/components/charts/WaitTimeChart'
import { Card } from '@/components/ui/Card'
import type { DashboardSnapshot, Signal, Alert, SentimentDataPoint } from '@/types'
import { generateSentimentSeries, generateWaitTimeSeries } from '@/lib/mockData'

interface OverviewProps {
  snapshot: DashboardSnapshot
  signals: Signal[]
  onMarkAlertRead: (id: string) => void
  onMarkAllAlertsRead: () => void
}

export function Overview({ snapshot, signals, onMarkAlertRead, onMarkAllAlertsRead }: OverviewProps) {
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null)

  const allAlerts: Alert[] = Object.values(snapshot.entities).flatMap(e => e.alerts)
  const waitTimeData = generateWaitTimeSeries()

  const selectedAnalytics = selectedEntity ? snapshot.entities[selectedEntity] : null
  const sentimentSeries: SentimentDataPoint[] = selectedEntity
    ? generateSentimentSeries(selectedEntity, 14)
    : []

  const sortedEntities = Object.values(snapshot.entities).sort(
    (a, b) => (b.health_score?.overall_score ?? 0) - (a.health_score?.overall_score ?? 0),
  )

  return (
    <div className="space-y-6">
      {/* Stats row */}
      <OverviewStats snapshot={snapshot} />

      {/* Main content grid */}
      <div className="grid grid-cols-12 gap-4">
        {/* Left: Entity cards */}
        <div className="col-span-12 lg:col-span-3 space-y-3">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide px-1">
            Entity Health
          </h3>
          {sortedEntities.map(entity => (
            <EntityHealthCard
              key={entity.entity_name}
              analytics={entity}
              selected={selectedEntity === entity.entity_name}
              onClick={() =>
                setSelectedEntity(
                  selectedEntity === entity.entity_name ? null : entity.entity_name,
                )
              }
            />
          ))}
        </div>

        {/* Center: Detail or wait times */}
        <div className="col-span-12 lg:col-span-6 space-y-4">
          {selectedAnalytics ? (
            <EntityDetail
              analytics={selectedAnalytics}
              sentimentSeries={sentimentSeries}
              onClose={() => setSelectedEntity(null)}
            />
          ) : (
            <>
              <Card>
                <WaitTimeChart data={waitTimeData} />
              </Card>

              {/* Risk/Opportunity summary */}
              <div className="grid grid-cols-2 gap-4">
                {snapshot.top_risks.length > 0 && (
                  <Card>
                    <h4 className="text-xs font-semibold text-red-400 uppercase tracking-wide mb-3">
                      Top Risks
                    </h4>
                    <ul className="space-y-1.5">
                      {snapshot.top_risks.slice(0, 4).map((risk, i) => (
                        <li key={i} className="text-xs text-slate-400 leading-tight flex items-start gap-1.5">
                          <span className="text-red-500 flex-shrink-0">⚠</span>
                          {risk}
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}
                {snapshot.top_opportunities.length > 0 && (
                  <Card>
                    <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wide mb-3">
                      Opportunities
                    </h4>
                    <ul className="space-y-1.5">
                      {snapshot.top_opportunities.slice(0, 4).map((opp, i) => (
                        <li key={i} className="text-xs text-slate-400 leading-tight flex items-start gap-1.5">
                          <span className="text-emerald-500 flex-shrink-0">★</span>
                          {opp}
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}
              </div>
            </>
          )}
        </div>

        {/* Right: Alerts + signals */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          <AlertPanel
            alerts={allAlerts}
            onMarkRead={onMarkAlertRead}
            onMarkAllRead={onMarkAllAlertsRead}
            maxVisible={8}
          />
          <SignalFeed signals={signals} maxVisible={15} />
        </div>
      </div>
    </div>
  )
}
