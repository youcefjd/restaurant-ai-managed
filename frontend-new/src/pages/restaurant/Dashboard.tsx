import { useQuery } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { ShoppingBag, DollarSign, Clock, TrendingUp, CheckCircle, Package, Activity, ArrowUpRight } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { AreaChart, Area, BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts'

export default function RestaurantDashboard() {
  const { user } = useAuth()
  const restaurantId = user?.id

  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['orders', restaurantId],
    queryFn: () => restaurantAPI.getOrders(restaurantId!),
    enabled: !!restaurantId,
  })

  const orderData = orders?.data || []

  // Calculate stats
  const todayOrders = orderData.filter((o: any) => {
    const orderDate = new Date(o.created_at).toDateString()
    const today = new Date().toDateString()
    return orderDate === today
  })

  const pendingOrders = orderData.filter((o: any) => o.status === 'pending').length
  const completedToday = todayOrders.filter((o: any) => o.status === 'completed').length
  const todayRevenue = todayOrders.reduce((sum: number, o: any) => sum + o.total, 0) / 100
  const totalRevenue = orderData.reduce((sum: number, o: any) => sum + o.total, 0) / 100

  // Chart data - last 7 days
  const getLast7Days = () => {
    const days = []
    for (let i = 6; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      const dayOrders = orderData.filter((o: any) => {
        const orderDate = new Date(o.created_at).toDateString()
        return orderDate === date.toDateString()
      })
      days.push({
        day: date.toLocaleDateString('en-US', { weekday: 'short' }),
        orders: dayOrders.length,
        revenue: dayOrders.reduce((sum: number, o: any) => sum + o.total, 0) / 100
      })
    }
    return days
  }

  const weekData = getLast7Days()

  const stats = [
    {
      label: 'Today\'s Revenue',
      value: `$${todayRevenue.toFixed(2)}`,
      icon: DollarSign,
      gradient: 'from-green-500 to-emerald-600',
      iconBg: 'bg-green-500',
      bgGradient: 'bg-gradient-to-br from-green-50 to-emerald-100',
      change: '+12%',
      trend: 'up',
    },
    {
      label: 'Pending Orders',
      value: pendingOrders,
      icon: Clock,
      gradient: 'from-orange-500 to-amber-600',
      iconBg: 'bg-orange-500',
      bgGradient: 'bg-gradient-to-br from-orange-50 to-amber-100',
      change: pendingOrders > 0 ? 'Needs attention' : 'All clear',
      trend: pendingOrders > 0 ? 'alert' : 'normal',
    },
    {
      label: 'Completed Today',
      value: completedToday,
      icon: CheckCircle,
      gradient: 'from-blue-500 to-blue-600',
      iconBg: 'bg-blue-500',
      bgGradient: 'bg-gradient-to-br from-blue-50 to-blue-100',
      change: `${todayOrders.length} total`,
      trend: 'normal',
    },
    {
      label: 'Total Revenue',
      value: `$${totalRevenue.toFixed(2)}`,
      icon: TrendingUp,
      gradient: 'from-purple-500 to-purple-600',
      iconBg: 'bg-purple-500',
      bgGradient: 'bg-gradient-to-br from-purple-50 to-purple-100',
      change: 'All time',
      trend: 'up',
    },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary-200 border-t-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 max-w-md mx-auto">
          <p className="text-red-600 font-semibold">Error loading dashboard</p>
          <p className="text-sm text-red-500 mt-2">Please refresh the page</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl p-8 text-white shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Welcome back!</h1>
            <p className="text-blue-100">Here's what's happening with your restaurant today</p>
          </div>
          <div className="hidden md:flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
            <Activity className="w-5 h-5" />
            <span className="font-semibold">Live Dashboard</span>
          </div>
        </div>
      </div>

      {/* Stats Grid - Optimized for Tablets */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="relative group bg-white rounded-2xl p-6 shadow-card hover:shadow-card-hover transition-all duration-300 border border-gray-100 overflow-hidden min-h-[180px]"
          >
            {/* Background decoration */}
            <div className={`absolute top-0 right-0 w-32 h-32 ${stat.bgGradient} rounded-full blur-3xl opacity-30 group-hover:opacity-50 transition-opacity`}></div>

            <div className="relative">
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-xl ${stat.iconBg} shadow-lg`}>
                  <stat.icon className="w-7 h-7 text-white" />
                </div>
                {stat.trend === 'alert' && (
                  <div className="flex items-center gap-1 px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-semibold">
                    <Activity className="w-3 h-3" />
                    {stat.change}
                  </div>
                )}
              </div>

              <div>
                <p className="text-gray-600 text-sm font-medium mb-2">{stat.label}</p>
                <p className="text-4xl font-bold text-gray-900 mb-2">{stat.value}</p>
                {stat.trend !== 'alert' && (
                  <p className="text-xs text-gray-500">{stat.change}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <div className="bg-white rounded-2xl p-6 shadow-card border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-gray-900">Revenue (Last 7 Days)</h2>
            <div className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-semibold">
              ${weekData.reduce((sum, d) => sum + d.revenue, 0).toFixed(0)}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={weekData}>
              <defs>
                <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="day" stroke="#9ca3af" fontSize={12} />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Revenue']}
              />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#22c55e"
                strokeWidth={3}
                fill="url(#revenueGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Orders Chart */}
        <div className="bg-white rounded-2xl p-6 shadow-card border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-gray-900">Orders (Last 7 Days)</h2>
            <div className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
              {weekData.reduce((sum, d) => sum + d.orders, 0)} orders
            </div>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={weekData}>
              <XAxis dataKey="day" stroke="#9ca3af" fontSize={12} />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              />
              <Bar dataKey="orders" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Orders - Tablet Optimized */}
      <div className="bg-white rounded-2xl p-6 shadow-card border border-gray-100">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-gray-900">Recent Orders</h2>
          <button className="text-sm text-primary-600 hover:text-primary-700 font-semibold flex items-center gap-1">
            View All <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>

        {todayOrders.length === 0 ? (
          <div className="text-center py-16 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl">
            <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 font-medium">No orders yet today</p>
            <p className="text-sm text-gray-500 mt-1">Orders will appear here as they come in</p>
          </div>
        ) : (
          <div className="space-y-3">
            {todayOrders.slice(0, 5).map((order: any) => (
              <div
                key={order.id}
                className="flex items-center justify-between p-5 bg-gradient-to-r from-gray-50 to-white rounded-xl border border-gray-100 hover:border-primary-200 hover:shadow-md transition-all duration-200 cursor-pointer group"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    order.status === 'completed' ? 'bg-green-100' :
                    order.status === 'pending' ? 'bg-orange-100' : 'bg-blue-100'
                  }`}>
                    {order.status === 'completed' ? (
                      <CheckCircle className="w-6 h-6 text-green-600" />
                    ) : order.status === 'pending' ? (
                      <Clock className="w-6 h-6 text-orange-600" />
                    ) : (
                      <ShoppingBag className="w-6 h-6 text-blue-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 text-lg">Order #{order.id}</p>
                    <p className="text-sm text-gray-600">{order.customer_name || 'Anonymous'}</p>
                    <p className="text-xs text-gray-500">{new Date(order.created_at).toLocaleTimeString()}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900 mb-1">${(order.total / 100).toFixed(2)}</p>
                  <span
                    className={`inline-flex items-center text-xs px-3 py-1.5 rounded-full font-semibold ${
                      order.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : order.status === 'pending'
                        ? 'bg-orange-100 text-orange-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {order.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
