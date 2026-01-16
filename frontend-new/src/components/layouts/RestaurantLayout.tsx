import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Home, ShoppingBag, BarChart3, Settings, LogOut, MessageSquare, UtensilsCrossed } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function RestaurantLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const navItems = [
    { to: '/restaurant/dashboard', icon: Home, label: 'Dashboard' },
    { to: '/restaurant/orders', icon: ShoppingBag, label: 'Orders' },
    { to: '/restaurant/menu', icon: UtensilsCrossed, label: 'Menu' },
    { to: '/restaurant/transcripts', icon: MessageSquare, label: 'Transcripts' },
    { to: '/restaurant/analytics', icon: BarChart3, label: 'Analytics' },
    { to: '/restaurant/settings', icon: Settings, label: 'Settings' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-primary-600">Restaurant Portal</h1>
          <p className="text-sm text-gray-500 mt-1">{user?.business_name || 'Restaurant'}</p>
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
          {user?.trial_ends_at && (
            <div className="mt-2 px-3 py-2 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-800">Free Trial</p>
              <p className="text-xs text-blue-600 mt-1">
                {Math.ceil((new Date(user.trial_ends_at).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))} days left
              </p>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <header className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Welcome back!</h2>
            <div className="flex items-center gap-4">
              <button onClick={() => navigate('/restaurant/orders')} className="btn btn-primary">New Order</button>
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
