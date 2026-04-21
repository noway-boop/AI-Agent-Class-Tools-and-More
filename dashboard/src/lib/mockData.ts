import type { DashboardSnapshot, SentimentDataPoint, WaitTimeDataPoint } from '@/types'

export const MOCK_SNAPSHOT: DashboardSnapshot = {
  generated_at: new Date().toISOString(),
  total_signals: 1842,
  total_alerts: 7,
  critical_alerts: 2,
  top_risks: [
    '[Walt Disney World] Sentiment below critical threshold',
    '[Walt Disney World] Volume spike combined with negative sentiment',
    '[Disney Cruise Line] Financial metrics trending below expectations',
  ],
  top_opportunities: [
    '[Disneyland Resort] Strong positive sentiment — capitalize on brand momentum',
    '[Walt Disney World] High engagement — amplify key messages',
    '[Shanghai Disney Resort] Competitive advantage — widen the gap',
  ],
  entities: {
    'Walt Disney World': {
      entity_id: 'e1',
      entity_name: 'Walt Disney World',
      signal_count: 721,
      computed_at: new Date().toISOString(),
      health_score: {
        entity_name: 'Walt Disney World',
        overall_score: 62.4,
        computed_at: new Date().toISOString(),
        risk_flags: ['Sentiment below critical threshold', 'Volume spike with negative signals'],
        opportunities: ['High engagement — amplify key messages'],
        components: {
          sentiment: { name: 'sentiment', value: 54.2, weight: 0.30, contributing_factors: ['Avg polarity: -0.08', 'Sharp negative swing: -0.18 in 24h', 'Sample size: 248'] },
          financial: { name: 'financial', value: 71.0, weight: 0.25, contributing_factors: ['Revenue delta: +4.2%', 'Analyst rating: 4.1/5.0'] },
          operational: { name: 'operational', value: 58.5, weight: 0.20, contributing_factors: ['Avg wait: 52 min', 'Crowd level: 7/10', 'Park hours: 14h'] },
          volume: { name: 'volume', value: 85.0, weight: 0.15, contributing_factors: ['Volume spike: 2.4x average', '24h signals: 189'] },
          competitive: { name: 'competitive', value: 52.0, weight: 0.10, contributing_factors: ['Share of voice: 38%', 'Sentiment gap vs competitors: +0.04'] },
        },
      },
      scorecard: {
        id: 's1', entity_id: 'e1', period: 'daily',
        period_date: new Date().toISOString(), overall_score: 62.4,
        sentiment_avg: -0.08, signal_volume: 721,
        risk_flags: ['Sentiment below critical threshold'],
        opportunities: ['High engagement'],
        generated_at: new Date().toISOString(),
      },
      sentiment_trend: {
        metric_name: 'sentiment', direction: 'decelerating',
        short_term_avg: -0.08, long_term_avg: 0.10,
        delta_pct: -18.0, momentum: -0.03, data_points: 248,
        period_start: new Date(Date.now() - 30 * 86400000).toISOString(),
        period_end: new Date().toISOString(),
        description: 'Sentiment is declining (-18.0% vs baseline, momentum -0.030)',
      },
      metric_trends: {},
      alerts: [
        {
          id: 'a1', entity_id: 'e1', alert_type: 'sentiment_spike',
          severity: 'critical', is_read: false,
          headline: 'Critical sentiment drop: -0.32 in 24h',
          summary: 'Lightning Lane pricing backlash driving negative social volume.',
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: 'a2', entity_id: 'e1', alert_type: 'volume_anomaly',
          severity: 'warning', is_read: false,
          headline: 'Signal volume spike: +140% above average',
          summary: '189 signals in 24h vs 79 daily average.',
          created_at: new Date(Date.now() - 7200000).toISOString(),
        },
      ],
    },
    'Disneyland Resort': {
      entity_id: 'e2',
      entity_name: 'Disneyland Resort',
      signal_count: 412,
      computed_at: new Date().toISOString(),
      health_score: {
        entity_name: 'Disneyland Resort',
        overall_score: 78.1,
        computed_at: new Date().toISOString(),
        risk_flags: [],
        opportunities: ['Strong positive sentiment — capitalize on brand momentum', 'Operational excellence — guest experience is strong'],
        components: {
          sentiment: { name: 'sentiment', value: 82.0, weight: 0.30, contributing_factors: ['Avg polarity: +0.31', 'Sample size: 143'] },
          financial: { name: 'financial', value: 74.0, weight: 0.25, contributing_factors: ['Revenue delta: +6.1%', 'Analyst rating: 4.2/5.0'] },
          operational: { name: 'operational', value: 76.5, weight: 0.20, contributing_factors: ['Avg wait: 34 min', 'Crowd level: 5/10', 'Park hours: 13h'] },
          volume: { name: 'volume', value: 68.0, weight: 0.15, contributing_factors: ['Above-average buzz: 1.6x', '24h signals: 89'] },
          competitive: { name: 'competitive', value: 71.0, weight: 0.10, contributing_factors: ['Share of voice: 28%', 'Sentiment gap: +0.18'] },
        },
      },
      scorecard: {
        id: 's2', entity_id: 'e2', period: 'daily',
        period_date: new Date().toISOString(), overall_score: 78.1,
        sentiment_avg: 0.31, signal_volume: 412,
        risk_flags: [],
        opportunities: ['Strong positive sentiment'],
        generated_at: new Date().toISOString(),
      },
      sentiment_trend: {
        metric_name: 'sentiment', direction: 'accelerating',
        short_term_avg: 0.31, long_term_avg: 0.18,
        delta_pct: 12.3, momentum: 0.02, data_points: 143,
        period_start: new Date(Date.now() - 30 * 86400000).toISOString(),
        period_end: new Date().toISOString(),
        description: 'Sentiment is accelerating (+12.3% vs baseline)',
      },
      metric_trends: {},
      alerts: [
        {
          id: 'a3', entity_id: 'e2', alert_type: 'sentiment_spike',
          severity: 'info', is_read: true,
          headline: 'Positive sentiment surge: +0.28 in 24h',
          summary: 'Rise of the Resistance and new seasonal food event driving positive coverage.',
          created_at: new Date(Date.now() - 14400000).toISOString(),
        },
      ],
    },
    'Disney Cruise Line': {
      entity_id: 'e3',
      entity_name: 'Disney Cruise Line',
      signal_count: 298,
      computed_at: new Date().toISOString(),
      health_score: {
        entity_name: 'Disney Cruise Line',
        overall_score: 55.8,
        computed_at: new Date().toISOString(),
        risk_flags: ['Financial metrics trending below expectations'],
        opportunities: [],
        components: {
          sentiment: { name: 'sentiment', value: 60.0, weight: 0.30, contributing_factors: ['Avg polarity: +0.12', 'Sample size: 87'] },
          financial: { name: 'financial', value: 42.0, weight: 0.25, contributing_factors: ['Revenue delta: -2.1%', 'Analyst rating: 3.8/5.0'] },
          operational: { name: 'operational', value: 64.0, weight: 0.20, contributing_factors: ['Itinerary availability', 'Ship capacity: 91%'] },
          volume: { name: 'volume', value: 52.0, weight: 0.15, contributing_factors: ['Normal volume', '24h signals: 48'] },
          competitive: { name: 'competitive', value: 58.0, weight: 0.10, contributing_factors: ['Share of voice: 22%'] },
        },
      },
      scorecard: {
        id: 's3', entity_id: 'e3', period: 'daily',
        period_date: new Date().toISOString(), overall_score: 55.8,
        sentiment_avg: 0.12, signal_volume: 298,
        risk_flags: ['Financial metrics trending below expectations'],
        opportunities: [],
        generated_at: new Date().toISOString(),
      },
      sentiment_trend: {
        metric_name: 'sentiment', direction: 'stable',
        short_term_avg: 0.12, long_term_avg: 0.11,
        delta_pct: 1.2, momentum: 0.001, data_points: 87,
        period_start: new Date(Date.now() - 30 * 86400000).toISOString(),
        period_end: new Date().toISOString(),
        description: 'Sentiment is stable (within normal range)',
      },
      metric_trends: {},
      alerts: [
        {
          id: 'a4', entity_id: 'e3', alert_type: 'filing_detected',
          severity: 'warning', is_read: false,
          headline: 'SEC 10-Q filing detected',
          summary: 'Quarterly filing shows Cruise segment revenue -2.1% YoY.',
          created_at: new Date(Date.now() - 21600000).toISOString(),
        },
      ],
    },
    'Shanghai Disney Resort': {
      entity_id: 'e4',
      entity_name: 'Shanghai Disney Resort',
      signal_count: 187,
      computed_at: new Date().toISOString(),
      health_score: {
        entity_name: 'Shanghai Disney Resort',
        overall_score: 71.3,
        computed_at: new Date().toISOString(),
        risk_flags: [],
        opportunities: ['Competitive advantage — widen the gap'],
        components: {
          sentiment: { name: 'sentiment', value: 74.0, weight: 0.30, contributing_factors: ['Avg polarity: +0.24', 'Sample size: 62'] },
          financial: { name: 'financial', value: 68.0, weight: 0.25, contributing_factors: ['Revenue delta: +8.3%'] },
          operational: { name: 'operational', value: 72.0, weight: 0.20, contributing_factors: ['Avg wait: 41 min', 'Crowd level: 6/10'] },
          volume: { name: 'volume', value: 60.0, weight: 0.15, contributing_factors: ['Normal volume'] },
          competitive: { name: 'competitive', value: 80.0, weight: 0.10, contributing_factors: ['Strong market position'] },
        },
      },
      scorecard: {
        id: 's4', entity_id: 'e4', period: 'daily',
        period_date: new Date().toISOString(), overall_score: 71.3,
        sentiment_avg: 0.24, signal_volume: 187,
        risk_flags: [], opportunities: ['Competitive advantage'],
        generated_at: new Date().toISOString(),
      },
      sentiment_trend: {
        metric_name: 'sentiment', direction: 'accelerating',
        short_term_avg: 0.24, long_term_avg: 0.14,
        delta_pct: 10.5, momentum: 0.015, data_points: 62,
        period_start: new Date(Date.now() - 30 * 86400000).toISOString(),
        period_end: new Date().toISOString(),
        description: 'Sentiment is accelerating (+10.5% vs baseline)',
      },
      metric_trends: {},
      alerts: [],
    },
  },
}

export function generateSentimentSeries(entityName: string, days = 14): SentimentDataPoint[] {
  const points: SentimentDataPoint[] = []
  const bases: Record<string, number> = {
    'Walt Disney World': -0.05,
    'Disneyland Resort': 0.28,
    'Disney Cruise Line': 0.14,
    'Shanghai Disney Resort': 0.22,
  }
  const base = bases[entityName] ?? 0.1

  for (let i = days; i >= 0; i--) {
    const date = new Date(Date.now() - i * 86400000)
    const noise = (Math.random() - 0.5) * 0.2
    points.push({
      time: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      polarity: Math.max(-1, Math.min(1, base + noise)),
      volume: Math.floor(30 + Math.random() * 80),
      entity: entityName,
    })
  }
  return points
}

export function generateWaitTimeSeries(): WaitTimeDataPoint[] {
  const parks = ['Magic Kingdom', 'EPCOT', 'Hollywood Studios', 'Animal Kingdom']
  const points: WaitTimeDataPoint[] = []
  const now = new Date()

  for (let h = 9; h <= 21; h++) {
    const time = `${h}:00`
    const peakFactor = h >= 11 && h <= 14 ? 1.4 : h >= 18 && h <= 20 ? 1.2 : 1.0
    parks.forEach(park => {
      const base = park === 'Magic Kingdom' ? 55 : park === 'EPCOT' ? 42 : 38
      const avg = Math.floor(base * peakFactor * (0.85 + Math.random() * 0.3))
      points.push({
        time,
        park,
        avg_wait: avg,
        max_wait: Math.floor(avg * 1.8),
        crowd_level: Math.min(10, Math.floor(avg / 10)),
      })
    })
  }
  return points
}
