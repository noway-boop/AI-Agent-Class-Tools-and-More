import { cn } from '@/lib/utils'

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-white/20 border-t-disney-blue',
        'h-5 w-5',
        className,
      )}
    />
  )
}
