import { useState, useCallback } from 'react'
import { Layout } from '@/components/Layout'
import { Overview } from '@/pages/Overview'
import { AlertPanel } from '@/components/panels/AlertPanel'
import { SignalFeed } from '@/components/panels/SignalFeed'
import { Card } from '@/components/ui/Card'
import { MOCK_SNAPSHOT } from '@/lib/mockData'
import type { DashboardSnapshot, Alert, Signal } from '@/types'
import { formatDateShort } from '@/lib/utils'

function generateMockSignals(): Signal[] {
  const sources = [
    { type: 'news' as const, name: 'newsapi', titles: [
      'Disney World ticket prices reach record high amid mixed visitor reviews',
      'Lightning Lane Multi Pass sees surge in negative social media response',
      'Disney Parks announce new Tiana\'s Bayou Adventure opening date',
      'Walt Disney World reports strong Q2 attendance despite pricing concerns',
    ]},
    { type: 'reddit' as const, name: 'r/WaltDisneyWorld', titles: [
      'Lightning Lane prices are getting out of hand — $35 for one ride?',
      'Just got back from a magical week at WDW — worth every penny!',
      'Tips for rope dropping Magic Kingdom in peak season',
      'Is the Dining Plan worth it in 2026?',
    ]},
    { type: 'disney_blog' as const, name: 'disney_parks_blog', titles: [
      'Celebrate the Magic: New Nighttime Spectacular Coming to EPCOT',
      'Disney Cruise Line Announces New Mediterranean Itineraries for 2027',
    ]},
    { type: 'sec_filing' as const, name: 'sec_edgar', titles: [
      'Disney SEC 10-Q Filing: Q2 FY2026 — Disney Experiences Segment',
    ]},
    { type: 'youtube' as const, name: 'youtube:DFBGuide', titles: [
      'NEW Disney World Food Rankings 2026 — Every Park Reviewed!',
      'Is Disney Genie+ Worth It in 2026? Honest Review',
    ]},
  ]

  const signals: Signal[] = []
  let idx = 0

  sources.forEach(src => {
    src.titles.forEach((title, i) => {
      signals.push({
        id: `sig-${idx++}`,
        source_type: src.type,
        source_name: src.name,
        source_url: 'https://example.com',
        title,
        body: '',
        published_at: new Date(Date.now() - i * 3600000 * 2).toISOString(),
        ingested_at: new Date(Date.now() - i * 3600000).toISOString(),
        language: 'en',
        dedup_hash: `hash-${idx}`,
        status: 'scored',
      })
    })
  })

  return signals
}

const MOCK_SIGNALS = generateMockSignals()

export default function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const [snapshot, setSnapshot] = useState<DashboardSnapshot>(MOCK_SNAPSHOT)
  const [signals] = useState<Signal[]>(MOCK_SIGNALS)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(
    formatDateShort(new Date().toISOString()),
  )

  const allAlerts: Alert[] = Object.values(snapshot.entities).flatMap(e => e.alerts)
  const criticalAlerts = allAlerts.filter(a => !a.is_read && a.severity === 'critical').length

  const handleMarkAlertRead = useCallback((alertId: string) => {
    setSnapshot(prev => ({
      ...prev,
      entities: Object.fromEntries(
        Object.entries(prev.entities).map(([name, entity]) => [
          name,
          {
            ...entity,
            alerts: entity.alerts.map(a =>
              a.id === alertId ? { ...a, is_read: true } : a,
            ),
          },
        ]),
      ),
    }))
  }, [])

  const handleMarkAllAlertsRead = useCallback(() => {
    setSnapshot(prev => ({
      ...prev,
      entities: Object.fromEntries(
        Object.entries(prev.entities).map(([name, entity]) => [
          name,
          { ...entity, alerts: entity.alerts.map(a => ({ ...a, is_read: true })) },
        ]),
      ),
    }))
  }, [])

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true)
    await new Promise(r => setTimeout(r, 1200))
    setLastUpdated(formatDateShort(new Date().toISOString()))
    setIsRefreshing(false)
  }, [])

  function renderContent() {
    switch (activeTab) {
      case 'overview':
        return (
          <Overview
            snapshot={snapshot}
            signals={signals}
            onMarkAlertRead={handleMarkAlertRead}
            onMarkAllAlertsRead={handleMarkAllAlertsRead}
          />
        )
      case 'alerts':
        return (
          <div className="max-w-2xl">
            <AlertPanel
              alerts={allAlerts}
              onMarkRead={handleMarkAlertRead}
              onMarkAllRead={handleMarkAllAlertsRead}
              maxVisible={50}
            />
          </div>
        )
      case 'signals':
        return (
          <div className="max-w-2xl">
            <SignalFeed signals={signals} maxVisible={100} />
          </div>
        )
      case 'entities':
      case 'trends':
        return (
          <Overview
            snapshot={snapshot}
            signals={signals}
            onMarkAlertRead={handleMarkAlertRead}
            onMarkAllAlertsRead={handleMarkAllAlertsRead}
          />
        )
      default:
        return null
    }
  }

  return (
    <Layout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      criticalAlerts={criticalAlerts}
      onRefresh={handleRefresh}
      lastUpdated={lastUpdated}
      isRefreshing={isRefreshing}
    >
      {renderContent()}
    </Layout>
  )
}
