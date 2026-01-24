import { useState, useEffect } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { LayoutDashboard, ShoppingBag, UtensilsCrossed, MessageSquare, BarChart3, Settings, LogOut, Clock } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

const navItems = [
  { to: '/restaurant/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/restaurant/orders', icon: ShoppingBag, label: 'Orders' },
  { to: '/restaurant/menu', icon: UtensilsCrossed, label: 'Menu' },
  { to: '/restaurant/transcripts', icon: MessageSquare, label: 'Transcripts' },
  { to: '/restaurant/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/restaurant/settings', icon: Settings, label: 'Settings' },
]

export default function RestaurantLayout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [currentTime, setCurrentTime] = useState(new Date())
  const timezone = user?.timezone || 'America/New_York'

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  // Format time in restaurant's timezone
  const formatTimeInTimezone = (date: Date) => {
    return date.toLocaleString('en-US', {
      timeZone: timezone,
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  // Get short timezone label (e.g., "PST", "EST")
  const getTimezoneLabel = () => {
    return new Intl.DateTimeFormat('en-US', {
      timeZone: timezone,
      timeZoneName: 'short'
    }).formatToParts(currentTime).find(p => p.type === 'timeZoneName')?.value || ''
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-56 border-r border-[--border] flex flex-col" style={{ background: 'var(--bg-card)' }}>
        <div className="p-4 border-b border-[--border]">
          <h1 className="font-semibold">RestaurantAI</h1>
          <p className="text-xs text-dim truncate">{user?.business_name}</p>
        </div>

        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={`nav-link ${location.pathname === item.to ? 'active' : ''}`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-2 border-t border-[--border]">
          <button onClick={logout} className="nav-link w-full text-left hover:text-red-400">
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-h-screen">
        <header className="px-6 py-3 border-b border-[--border] flex items-center justify-between">
          <h2 className="font-medium">
            {navItems.find(item => item.to === location.pathname)?.label || 'Dashboard'}
          </h2>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-dim">
              <Clock className="w-4 h-4" />
              <span>{formatTimeInTimezone(currentTime)}</span>
              <span className="text-xs opacity-60">{getTimezoneLabel()}</span>
            </div>
            <span className="badge badge-success text-xs">● Live</span>
          </div>
        </header>

        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
