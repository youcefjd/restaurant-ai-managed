import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  label: string
  value: string | number
  icon?: LucideIcon
  trend?: {
    value: string
    direction: 'up' | 'down'
  }
  subtitle?: string
}

export default function StatCard({ label, value, icon: Icon, trend, subtitle }: StatCardProps) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-dim">{label}</p>
          <p className="text-2xl font-semibold mt-1">{value}</p>
          {trend && (
            <p className={`text-xs mt-1 ${trend.direction === 'up' ? 'text-success' : 'text-danger'}`}>
              {trend.direction === 'up' ? '+' : ''}{trend.value}
            </p>
          )}
          {subtitle && <p className="text-xs text-dim mt-1">{subtitle}</p>}
        </div>
        {Icon && (
          <div className="p-2 rounded-lg bg-white/5">
            <Icon className="w-5 h-5 text-accent" />
          </div>
        )}
      </div>
    </div>
  )
}
