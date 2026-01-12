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
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-primary-600">Platform Admin</h1>
          <p className="text-sm text-gray-500 mt-1">Multi-Restaurant SaaS</p>
        </div>

        <nav className="px-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto p-3">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
          </button>
          <div className="mt-2 px-3 py-2 bg-green-50 rounded-lg">
            <p className="text-xs text-green-800">Platform Status</p>
            <p className="text-xs text-green-600 mt-1">All Systems Operational</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <header className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Platform Overview</h2>
            <div className="flex items-center gap-4">
              <button onClick={() => navigate('/admin/restaurants')} className="btn btn-primary">Add Restaurant</button>
              <button onClick={() => alert('Settings coming soon!')} className="p-2 hover:bg-gray-100 rounded-lg" title="Settings">
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </header>

        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
