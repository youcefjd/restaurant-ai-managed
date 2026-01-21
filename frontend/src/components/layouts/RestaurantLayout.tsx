import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  ShoppingBag,
  UtensilsCrossed,
  MessageSquare,
  BarChart3,
  Settings,
  LogOut,
  Phone
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
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col">
        {/* Brand header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center">
              <Phone className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-gray-900">RestaurantAI</h1>
              <p className="text-xs text-gray-500 truncate max-w-[140px]">
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
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <item.icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : ''}`} />
                <span className="flex-1">{item.label}</span>
              </NavLink>
            )
          })}
        </nav>

        {/* Footer section */}
        <div className="p-3 space-y-2 border-t border-gray-200">
          {/* Trial status */}
          {daysLeft !== null && (
            <div className="p-4 rounded-lg bg-blue-50 border border-blue-100">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-blue-700">Free Trial</span>
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                  {daysLeft} days left
                </span>
              </div>
              <div className="h-1.5 bg-blue-100 rounded-full overflow-hidden">
                <div
                  style={{ width: `${Math.max(10, (daysLeft / 14) * 100)}%` }}
                  className="h-full bg-blue-600 rounded-full transition-all"
                />
              </div>
            </div>
          )}

          {/* Voice status indicator */}
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Phone className="w-5 h-5 text-gray-600" />
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-gray-700">Voice AI Active</p>
                <p className="text-xs text-gray-500 truncate">Ready to take calls</p>
              </div>
            </div>
          </div>

          {/* Logout button */}
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium text-sm">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-white border-b border-gray-200">
          <div className="px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  {navItems.find(item => item.to === location.pathname)?.label || 'Dashboard'}
                </h2>
                <div className="flex items-center gap-1 text-gray-500 text-sm">
                  <span className="text-gray-400">/</span>
                  <span>{user?.business_name}</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {/* Live indicator */}
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 border border-green-200">
                  <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-xs font-medium text-green-700">Live</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
