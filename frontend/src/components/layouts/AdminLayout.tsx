import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Store, DollarSign, TrendingUp, LogOut, Settings } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function AdminLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const navItems = [
    { to: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/admin/restaurants', icon: Store, label: 'Restaurants' },
    { to: '/admin/revenue', icon: DollarSign, label: 'Revenue' },
    { to: '/admin/analytics', icon: TrendingUp, label: 'Analytics' },
  ]

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg)' }}>
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 flex flex-col border-r border-[--border]" style={{ background: 'var(--bg-card)' }}>
        <div className="p-6 border-b border-[--border]">
          <h1 className="text-xl font-bold text-accent">Platform Admin</h1>
          <p className="text-xs text-dim mt-1">Multi-Restaurant SaaS</p>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-[--border]">
          <button
            onClick={logout}
            className="nav-link w-full text-left"
          >
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
          </button>
          <div className="mt-3 p-3 rounded-lg bg-success/10 border border-success/20">
            <p className="text-xs text-success font-medium">Platform Status</p>
            <p className="text-xs text-dim mt-1">All Systems Operational</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <header className="border-b border-[--border] px-6 py-4" style={{ background: 'var(--bg-card)' }}>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Platform Overview</h2>
            <div className="flex items-center gap-3">
              <button onClick={() => navigate('/admin/restaurants')} className="btn btn-primary btn-sm">
                Add Restaurant
              </button>
              <button
                onClick={() => alert('Settings coming soon!')}
                className="p-2 rounded-lg hover:bg-white/5 text-dim hover:text-white transition-colors"
                title="Settings"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </header>

        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
