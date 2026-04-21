import type {
  Alert,
  DashboardSnapshot,
  EntityAnalytics,
  MetricSnapshot,
  Signal,
  SentimentDataPoint,
  WaitTimeDataPoint,
} from '@/types'

const BASE = '/api/v1'

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(BASE + path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v))
  }
  const res = await fetch(url.toString())
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(BASE + path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}

export const api = {
  dashboard: {
    snapshot: () => get<DashboardSnapshot>('/dashboard/snapshot'),
  },

  entities: {
    analytics: (entityName: string) =>
      get<EntityAnalytics>(`/entities/${encodeURIComponent(entityName)}/analytics`),
  },

  signals: {
    list: (params?: { source_type?: string; limit?: string; entity?: string }) =>
      get<Signal[]>('/signals', params as Record<string, string>),
  },

  alerts: {
    list: (params?: { severity?: string; is_read?: string; limit?: string }) =>
      get<Alert[]>('/alerts', params as Record<string, string>),
    markRead: (alertId: string) =>
      patch<Alert>(`/alerts/${alertId}`, { is_read: true }),
    markAllRead: () =>
      patch<{ updated: number }>('/alerts/mark-all-read', {}),
  },

  metrics: {
    sentiment: (entityName: string, days?: number) =>
      get<SentimentDataPoint[]>(`/metrics/sentiment`, {
        entity: entityName,
        days: String(days ?? 7),
      }),
    waitTimes: (parkName?: string) =>
      get<WaitTimeDataPoint[]>('/metrics/wait-times', parkName ? { park: parkName } : {}),
    snapshots: (entityName: string, metricType: string) =>
      get<MetricSnapshot[]>(`/metrics/snapshots`, {
        entity: entityName,
        metric_type: metricType,
      }),
  },

  pipeline: {
    trigger: (sources?: string[]) =>
      fetch(`${BASE}/pipeline/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sources }),
      }).then(r => r.json()),
  },
}
