import { useState, useEffect } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { LayoutDashboard, Store, DollarSign, TrendingUp, LogOut, Settings, Menu, X } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function AdminLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const navItems = [
    { to: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/admin/restaurants', icon: Store, label: 'Restaurants' },
    { to: '/admin/revenue', icon: DollarSign, label: 'Revenue' },
    { to: '/admin/analytics', icon: TrendingUp, label: 'Analytics' },
  ]

  // Close sidebar on route change
  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname])

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg)' }}>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="sidebar-overlay md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-64 flex-shrink-0 flex flex-col border-r border-[--border] transform transition-transform duration-200 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0`}
        style={{ background: 'var(--bg-card)' }}
      >
        <div className="p-6 border-b border-[--border] flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-accent">Platform Admin</h1>
            <p className="text-xs text-dim mt-1">Multi-Restaurant SaaS</p>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden text-dim hover:text-white">
            <X className="w-5 h-5" />
          </button>
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
      <main className="flex-1 overflow-auto w-full">
        <header className="border-b border-[--border] px-4 md:px-6 py-4" style={{ background: 'var(--bg-card)' }}>
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-3">
              <button onClick={() => setSidebarOpen(true)} className="md:hidden text-dim hover:text-white">
                <Menu className="w-5 h-5" />
              </button>
              <h2 className="text-base md:text-lg font-semibold">Platform Overview</h2>
            </div>
            <div className="flex items-center gap-2 md:gap-3">
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

        <div className="p-4 md:p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
