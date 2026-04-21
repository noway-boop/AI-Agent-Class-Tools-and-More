import { clsx, type ClassValue } from 'clsx'
import type { Severity, TrendDirection, Urgency } from '@/types'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatScore(score: number): string {
  return score.toFixed(1)
}

export function scoreColor(score: number): string {
  if (score >= 75) return 'text-emerald-400'
  if (score >= 55) return 'text-yellow-400'
  if (score >= 35) return 'text-orange-400'
  return 'text-red-400'
}

export function scoreBg(score: number): string {
  if (score >= 75) return 'bg-emerald-500'
  if (score >= 55) return 'bg-yellow-500'
  if (score >= 35) return 'bg-orange-500'
  return 'bg-red-500'
}

export function severityColor(severity: Severity): string {
  const map: Record<Severity, string> = {
    info: 'text-blue-400',
    warning: 'text-yellow-400',
    critical: 'text-red-400',
  }
  return map[severity]
}

export function severityBadge(severity: Severity): string {
  const map: Record<Severity, string> = {
    info: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    warning: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    critical: 'bg-red-500/20 text-red-300 border-red-500/30',
  }
  return map[severity]
}

export function urgencyBadge(urgency: Urgency): string {
  const map: Record<Urgency, string> = {
    low: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
    medium: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    high: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    critical: 'bg-red-500/20 text-red-300 border-red-500/30',
  }
  return map[urgency]
}

export function trendIcon(direction: TrendDirection): string {
  const map: Record<TrendDirection, string> = {
    accelerating: '↑',
    stable: '→',
    decelerating: '↓',
    reversing: '⇅',
    insufficient_data: '–',
  }
  return map[direction]
}

export function trendColor(direction: TrendDirection): string {
  const map: Record<TrendDirection, string> = {
    accelerating: 'text-emerald-400',
    stable: 'text-slate-400',
    decelerating: 'text-red-400',
    reversing: 'text-yellow-400',
    insufficient_data: 'text-slate-500',
  }
  return map[direction]
}

export function polarityColor(polarity: number): string {
  if (polarity > 0.2) return 'text-emerald-400'
  if (polarity > 0) return 'text-emerald-300'
  if (polarity > -0.2) return 'text-yellow-400'
  return 'text-red-400'
}

export function sourceIcon(sourceType: string): string {
  const map: Record<string, string> = {
    news: '📰',
    sec_filing: '📋',
    reddit: '🔶',
    youtube: '▶️',
    twitter: '🐦',
    tiktok: '🎵',
    disney_blog: '🏰',
    park_api: '🎢',
    earnings: '💰',
    competitor: '⚔️',
  }
  return map[sourceType] ?? '📄'
}

export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

export function formatDateShort(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
