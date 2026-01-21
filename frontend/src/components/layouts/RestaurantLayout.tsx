import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  ShoppingBag,
  UtensilsCrossed,
  MessageSquare,
  BarChart3,
  Settings,
  LogOut,
  Phone,
  Search,
  Bell
} from 'lucide-react'
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

  const daysLeft = user?.trial_ends_at
    ? Math.max(0, Math.ceil((new Date(user.trial_ends_at).getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
    : null

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg-primary)' }}>
      {/* Ambient background */}
      <div className="bg-ambient">
        <div className="ambient-blob ambient-blob-cyan w-96 h-96 -top-48 -left-48 opacity-20" />
        <div className="ambient-blob ambient-blob-pink w-96 h-96 top-1/2 -right-48 opacity-15" />
        <div className="ambient-blob ambient-blob-purple w-64 h-64 bottom-0 left-1/3 opacity-10" />
      </div>

      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 glass-sidebar relative z-10">
        {/* Brand header */}
        <div className="p-5" style={{ borderBottom: '1px solid var(--border-glass)' }}>
          <div className="flex items-center gap-3">
            <div className="icon-box icon-box-md icon-box-cyan rounded-xl">
              <Phone className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-semibold text-white">RestaurantAI</h1>
              <p className="text-xs truncate max-w-[140px]" style={{ color: 'var(--text-muted)' }}>
                {user?.business_name || 'Restaurant Portal'}
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location.pathname === item.to
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={isActive ? 'nav-item-active' : 'nav-item'}
              >
                <item.icon className="w-5 h-5" />
                <span className="flex-1">{item.label}</span>
                {isActive && (
                  <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--accent-cyan)' }} />
                )}
              </NavLink>
            )
          })}
        </nav>

        {/* Footer section */}
        <div className="p-3 space-y-3" style={{ borderTop: '1px solid var(--border-glass)' }}>
          {/* Trial status */}
          {daysLeft !== null && (
            <div className="glass-card p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Free Trial</span>
                <span className="badge badge-cyan text-xs">
                  {daysLeft} days left
                </span>
              </div>
              <div className="progress-bar">
                <div
                  style={{ width: `${Math.max(10, (daysLeft / 14) * 100)}%` }}
                  className="progress-bar-fill progress-bar-cyan"
                />
              </div>
            </div>
          )}

          {/* Voice status indicator */}
          <div className="glass-card p-4">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Phone className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
                <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full animate-pulse-glow" style={{ background: 'var(--accent-mint)' }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-white">Voice AI Active</p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Ready to take calls</p>
              </div>
            </div>
          </div>

          {/* Logout button */}
          <button
            onClick={logout}
            className="w-full nav-item hover:text-red-400 group"
          >
            <LogOut className="w-5 h-5 group-hover:text-red-400" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen overflow-hidden relative z-10">
        {/* Header */}
        <header className="sticky top-0 z-10 px-6 py-4" style={{ background: 'rgba(15, 15, 20, 0.8)', backdropFilter: 'blur(20px)', borderBottom: '1px solid var(--border-glass)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Search bar */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Search something here..."
                  className="input-glass pl-10 pr-4 py-2 w-80 text-sm"
                />
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Page title */}
              <div className="text-right mr-4">
                <h2 className="text-lg font-semibold text-white">
                  {navItems.find(item => item.to === location.pathname)?.label || 'Dashboard'}
                </h2>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{user?.business_name}</p>
              </div>

              {/* Live indicator */}
              <div className="flex items-center gap-2 badge badge-mint">
                <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--accent-mint)' }} />
                <span>Live</span>
              </div>

              {/* Notifications */}
              <button className="btn-glass p-2 rounded-xl relative">
                <Bell className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
                <span className="absolute top-1 right-1 w-2 h-2 rounded-full" style={{ background: 'var(--accent-pink)' }} />
              </button>

              {/* User avatar */}
              <div className="w-10 h-10 rounded-xl overflow-hidden" style={{ background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))' }}>
                <div className="w-full h-full flex items-center justify-center text-sm font-bold text-white">
                  {user?.business_name?.charAt(0) || 'R'}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
