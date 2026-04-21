import { useState } from 'react'
import {
  LayoutDashboard, Bell, Radio, ChevronRight,
  RefreshCw, Activity, TrendingUp, Newspaper,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface LayoutProps {
  children: React.ReactNode
  activeTab: string
  onTabChange: (tab: string) => void
  criticalAlerts: number
  onRefresh: () => void
  lastUpdated: string
  isRefreshing: boolean
}

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'entities', label: 'Entities', icon: Activity },
  { id: 'trends', label: 'Trends', icon: TrendingUp },
  { id: 'signals', label: 'Signal Feed', icon: Newspaper },
  { id: 'alerts', label: 'Alerts', icon: Bell },
]

export function Layout({
  children, activeTab, onTabChange, criticalAlerts,
  onRefresh, lastUpdated, isRefreshing,
}: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen bg-disney-navy text-white overflow-hidden font-sans">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col bg-disney-navy-light border-r border-white/10 transition-all duration-200',
          sidebarOpen ? 'w-56' : 'w-14',
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-white/10 h-16">
          <div className="flex-shrink-0 w-6 h-6 rounded bg-disney-blue flex items-center justify-center">
            <span className="text-xs font-bold">D</span>
          </div>
          {sidebarOpen && (
            <div className="overflow-hidden">
              <p className="text-xs font-bold text-white leading-tight">Disney</p>
              <p className="text-xs text-disney-gold leading-tight">Experiences Intel</p>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 space-y-0.5 px-2">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => onTabChange(id)}
              className={cn(
                'w-full flex items-center gap-3 px-2 py-2 rounded-lg text-sm transition-all',
                activeTab === id
                  ? 'bg-disney-blue text-white font-medium'
                  : 'text-slate-400 hover:text-white hover:bg-white/5',
              )}
            >
              <Icon size={16} className="flex-shrink-0" />
              {sidebarOpen && (
                <span className="truncate">{label}</span>
              )}
              {sidebarOpen && id === 'alerts' && criticalAlerts > 0 && (
                <span className="ml-auto bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                  {criticalAlerts}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* Collapse toggle */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-3 text-slate-500 hover:text-white border-t border-white/10 flex justify-center"
        >
          <ChevronRight size={14} className={cn('transition-transform', sidebarOpen && 'rotate-180')} />
        </button>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-white/10 bg-disney-navy-light flex-shrink-0">
          <div>
            <h1 className="text-base font-semibold text-white">
              {NAV_ITEMS.find(n => n.id === activeTab)?.label}
            </h1>
            <p className="text-xs text-slate-500">
              Last updated: {lastUpdated}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {criticalAlerts > 0 && (
              <div className="flex items-center gap-1.5 bg-red-500/20 border border-red-500/30 text-red-300 text-xs px-3 py-1.5 rounded-full">
                <Radio size={10} className="animate-pulse" />
                {criticalAlerts} critical
              </div>
            )}
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 text-xs text-slate-400 hover:text-white border border-white/10 hover:border-disney-blue/50 px-3 py-1.5 rounded-lg transition-all"
            >
              <RefreshCw size={12} className={cn(isRefreshing && 'animate-spin')} />
              Refresh
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
