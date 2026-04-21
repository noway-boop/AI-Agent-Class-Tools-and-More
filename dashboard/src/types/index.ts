export type SourceType =
  | 'news' | 'sec_filing' | 'reddit' | 'youtube'
  | 'twitter' | 'tiktok' | 'disney_blog' | 'park_api'
  | 'earnings' | 'competitor'

export type Urgency = 'low' | 'medium' | 'high' | 'critical'
export type Severity = 'info' | 'warning' | 'critical'
export type AlertType =
  | 'sentiment_spike' | 'volume_anomaly' | 'filing_detected'
  | 'competitor_move' | 'earnings_surprise' | 'trend_reversal'
export type TrendDirection =
  | 'accelerating' | 'stable' | 'decelerating' | 'reversing' | 'insufficient_data'
export type Period = 'daily' | 'weekly' | 'monthly' | 'quarterly'

export interface Signal {
  id: string
  source_type: SourceType
  source_name: string
  source_url: string
  title: string
  body: string
  published_at: string
  ingested_at: string
  language: string
  dedup_hash: string
  status: string
}

export interface SentimentScore {
  id: string
  signal_id: string
  model_used: string
  polarity: number      // -1.0 to 1.0
  magnitude: number     // 0.0 to 1.0
  urgency: Urgency
  confidence: number
  scored_at: string
}

export interface ComponentScore {
  name: string
  value: number         // 0-100
  weight: number
  contributing_factors: string[]
}

export interface HealthScore {
  entity_name: string
  overall_score: number
  components: Record<string, ComponentScore>
  risk_flags: string[]
  opportunities: string[]
  computed_at: string
}

export interface TrendResult {
  metric_name: string
  direction: TrendDirection
  short_term_avg: number
  long_term_avg: number
  delta_pct: number
  momentum: number
  data_points: number
  period_start: string
  period_end: string
  description: string
}

export interface Alert {
  id: string
  signal_id?: string
  entity_id: string
  alert_type: AlertType
  severity: Severity
  headline: string
  summary: string
  is_read: boolean
  created_at: string
  expires_at?: string
}

export interface Scorecard {
  id: string
  entity_id: string
  period: Period
  period_date: string
  overall_score: number
  sentiment_avg: number
  signal_volume: number
  risk_flags: string[]
  opportunities: string[]
  generated_at: string
}

export interface EntityAnalytics {
  entity_id: string
  entity_name: string
  health_score: HealthScore | null
  scorecard: Scorecard | null
  sentiment_trend: TrendResult | null
  metric_trends: Record<string, TrendResult>
  alerts: Alert[]
  signal_count: number
  computed_at: string
}

export interface DashboardSnapshot {
  entities: Record<string, EntityAnalytics>
  total_signals: number
  total_alerts: number
  critical_alerts: number
  top_risks: string[]
  top_opportunities: string[]
  generated_at: string
}

export interface SentimentDataPoint {
  time: string
  polarity: number
  volume: number
  entity: string
}

export interface WaitTimeDataPoint {
  time: string
  park: string
  avg_wait: number
  max_wait: number
  crowd_level: number
}

export interface MetricSnapshot {
  id: string
  entity_id: string
  metric_type: string
  value: number
  previous_value?: number
  delta_pct?: number
  period_start: string
  period_end: string
  source: string
  recorded_at: string
}
